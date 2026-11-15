import functools
import os

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from gigbid_core.db import Audit, db, init_db
from gigbid_core.security import MCPAuth, redact, tenant, trace_context

READ = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=True)


def create_server(name, port):
    server = FastMCP(
        name, host="0.0.0.0", port=int(os.getenv("MCP_PORT", port)), stateless_http=True, json_response=True
    )
    server._gigbid_server_id = {8101: "portfolio", 8102: "marketplace", 8103: "workspace"}[port]
    return server


def audit_tool(fn):
    @functools.wraps(fn)
    async def wrapped(*args, **kwargs):
        clean = {
            k: v.model_dump(exclude={"approval_token"}) if hasattr(v, "model_dump") else v
            for k, v in kwargs.items()
            if k != "approval_token"
        }
        try:
            from gigbid_core.tracing import span

            with span("mcp.server." + fn.__name__, run_id=trace_context.get(), tenant_id=tenant()):
                result = await fn(*args, **kwargs)
        except Exception as exc:
            with db() as session:
                session.add(
                    Audit(
                        tenant=tenant(),
                        trace_id=trace_context.get(),
                        tool=fn.__name__,
                        payload=redact({"arguments": clean, "error": type(exc).__name__}),
                    )
                )
            raise
        with db() as session:
            session.add(
                Audit(
                    tenant=tenant(),
                    trace_id=trace_context.get(),
                    tool=fn.__name__,
                    payload=redact({"arguments": clean, "result": result}),
                )
            )
        return result

    return wrapped


def serve(mcp):
    init_db()
    if os.getenv("MCP_SERVE_TRANSPORT", "stdio") == "stdio":
        mcp.run(transport="stdio")
    else:
        import uvicorn

        app = mcp.streamable_http_app()
        uvicorn.run(
            MCPAuth(app, server_id=mcp._gigbid_server_id),
            host="0.0.0.0",
            port=mcp.settings.port,
            log_level="warning",
        )
