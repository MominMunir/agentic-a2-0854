import asyncio
import json
import os
import sys

from langchain_mcp_adapters.client import MultiServerMCPClient

from gigbid_core.config import ROOT, settings
from gigbid_core.security import tenant_context, token, trace_context

ALLOWLISTS = {
    "scout": {"search_jobs", "get_job"},
    "analyst": set(),
    "risk_assessor": {"get_client_history"},
    "fit_matcher": {"search_evidence", "list_skills"},
    "pricing": {"get_connects_balance", "search_jobs"},
    "writer": {"search_evidence", "get_case_study"},
    "critic": {"get_case_study"},
    "client_liaison": {"list_messages", "free_calendar_slots"},
    "approval": {"submit_proposal", "send_message", "create_proposal_draft"},
    "workspace_approval": {"create_interview_hold", "create_email_draft"},
    "ui": {
        "search_jobs",
        "get_job",
        "list_messages",
        "get_connects_balance",
        "free_calendar_slots",
        "list_skills",
    },
}
SERVER_TOOLS = {
    "portfolio": {"search_evidence", "get_case_study", "list_skills"},
    "marketplace": {
        "search_jobs",
        "get_job",
        "get_client_history",
        "get_connects_balance",
        "list_messages",
        "submit_proposal",
        "send_message",
        "create_proposal_draft",
    },
    "workspace": {"free_calendar_slots", "create_interview_hold", "create_email_draft"},
}


def parse_result(result):
    if hasattr(result, "content"):
        if result.isError:
            raise RuntimeError(
                "MCP tool failed: " + " ".join(c.text for c in result.content if hasattr(c, "text"))
            )
        result = [c.model_dump() for c in result.content]
    if isinstance(result, list):
        text = "\n".join(x.get("text", "") for x in result if isinstance(x, dict))
        return json.loads(text)
    return json.loads(result) if isinstance(result, str) else result


class Tools:
    def __init__(self, user, role, trace=""):
        self.user, self.role, self.trace = user, role, trace

    async def call(self, name, **arguments):
        if name not in ALLOWLISTS.get(self.role, set()):
            raise PermissionError(f"{self.role} has no access to {name}")
        server = next(s for s, names in SERVER_TOOLS.items() if name in names)
        for attempt in range(3):
            try:
                from gigbid_core.tracing import span

                with span("mcp." + name, run_id=self.trace, role=self.role, server=server):
                    return await asyncio.wait_for(self._invoke(server, name, arguments), timeout=45)
            except (OSError, ConnectionError, TimeoutError):
                if attempt == 2:
                    raise ConnectionError("Marketplace/MCP unavailable. Work is queued for retry.") from None
                await asyncio.sleep(2**attempt)

    async def _invoke(self, server, name, arguments):
        cfg = settings()
        if cfg.mcp_transport == "memory":
            # Real SDK transport, useful for single-process development and unit tests.
            from importlib import import_module
            from mcp.shared.memory import create_connected_server_and_client_session

            module = import_module(f"mcp_servers.{server}.server")
            t, tr = tenant_context.set(self.user), trace_context.set(self.trace)
            try:
                async with create_connected_server_and_client_session(module.mcp._mcp_server) as session:
                    return parse_result(await session.call_tool(name, arguments))
            finally:
                tenant_context.reset(t)
                trace_context.reset(tr)
        if cfg.mcp_transport == "stdio":
            connection = {
                "transport": "stdio",
                "command": sys.executable,
                "args": ["-m", f"mcp_servers.{server}.server"],
                "cwd": str(ROOT),
                "env": {**os.environ, "MCP_STDIO_TENANT": self.user},
            }
        else:
            from opentelemetry.propagate import inject

            headers = {
                "Authorization": "Bearer " + token(self.user, "mcp", ttl=300, server=server),
                "X-Trace-ID": self.trace,
            }
            inject(headers)
            connection = {
                "transport": "streamable_http",
                "url": getattr(cfg, f"{server}_mcp_url"),
                "headers": headers,
                "timeout": 45,
            }
        client = MultiServerMCPClient({server: connection})
        tools = await client.get_tools()
        target = next(tool for tool in tools if tool.name == name)
        return parse_result(await target.ainvoke(arguments))
