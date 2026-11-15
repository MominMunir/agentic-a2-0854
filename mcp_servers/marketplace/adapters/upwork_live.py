import json
import time
from urllib.parse import urlparse

import httpx

from langchain_mcp_adapters.client import MultiServerMCPClient

from gigbid_core.config import settings
from gigbid_core.db import db, get, put
from gigbid_core.security import decrypt, encrypt, tenant
from mcp_servers.marketplace.adapters.local import validate_approval


class UpworkAdapter:
    """Official MCP only. Live effects are drafts, never automatic platform confirmations."""

    async def call(self, logical_name, args):
        with db() as session:
            stored = get(session, tenant(), "oauth", "upwork")
            mapping = get(session, tenant(), "tool_map", "upwork") or {}
        if not stored:
            raise PermissionError("Connect your Upwork account in Settings first")
        credentials = decrypt(stored["encrypted"])
        if credentials.get("expires_at", time.time() + 1) <= time.time():
            endpoint = credentials.get("token_endpoint", "")
            host = urlparse(endpoint).hostname or ""
            if not endpoint.startswith("https://") or not (
                host == "upwork.com" or host.endswith(".upwork.com")
            ):
                raise PermissionError("Reconnect Upwork: trusted token endpoint missing")
            async with httpx.AsyncClient(timeout=20) as http:
                response = await http.post(
                    endpoint,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": credentials.get("refresh_token", ""),
                        "client_id": credentials["client_id"],
                    },
                )
                response.raise_for_status()
                values = response.json()
            credentials = {
                **credentials,
                **values,
                "expires_at": time.time() + values.get("expires_in", 3600),
            }
            with db() as session:
                put(session, tenant(), "oauth", "upwork", {"encrypted": encrypt(credentials)})
        client = MultiServerMCPClient(
            {
                "upwork": {
                    "transport": "streamable_http",
                    "url": settings().upwork_mcp_url,
                    "headers": {"Authorization": "Bearer " + credentials["access_token"]},
                }
            }
        )
        tools = await client.get_tools()
        name = mapping.get(logical_name)
        target = next((tool for tool in tools if tool.name == name), None)
        if not target:
            raise ValueError(
                f"Verify the {logical_name} tool mapping in Settings against discovered official Upwork tools"
            )
        if logical_name.endswith("draft") and "draft" not in target.name.lower():
            raise PermissionError("Live writes require an explicitly draft-only official tool")
        result = await target.ainvoke(args)
        return json.loads(result) if isinstance(result, str) else result

    async def search_jobs(self, query="", limit=30):
        return await self.call("search_jobs", {"query": query, "limit": limit})

    async def get_job(self, job_id):
        return await self.call("get_job", {"job_id": job_id})

    async def get_client_history(self, client_id):
        return await self.call("get_client_history", {"client_id": client_id})

    async def get_connects_balance(self):
        return await self.call("get_connects_balance", {})

    async def list_messages(self, conversation_id=""):
        return await self.call("list_messages", {"conversation_id": conversation_id})

    async def create_proposal_draft(self, payload):
        if payload["dry_run"]:
            return {
                "status": "preview",
                "payload": {k: v for k, v in payload.items() if k != "approval_token"},
                "connects_cost": 0,
                "requires_upwork_confirmation": True,
            }
        validate_approval(payload, "create_proposal_draft")
        return await self.call(
            "create_proposal_draft",
            {
                k: v
                for k, v in payload.items()
                if k not in {"approval_token", "dry_run", "expected_connects_cost"}
            },
        )

    async def submit_proposal(self, payload):
        if not payload["dry_run"]:
            validate_approval(payload, "submit_proposal")
        # GigBid approval never grants permission to bypass Upwork confirmation.
        return (
            await self.create_proposal_draft({**payload, "dry_run": True})
            if payload["dry_run"]
            else await self.call(
                "create_proposal_draft",
                {
                    k: v
                    for k, v in payload.items()
                    if k not in {"approval_token", "dry_run", "expected_connects_cost"}
                },
            )
        )

    async def send_message(self, payload):
        if payload["dry_run"]:
            return {
                "status": "preview",
                "connects_cost": 0,
                "payload": {k: v for k, v in payload.items() if k != "approval_token"},
                "requires_upwork_confirmation": True,
            }
        validate_approval(payload, "send_message")
        return await self.call(
            "create_message_draft",
            {k: v for k, v in payload.items() if k not in {"approval_token", "dry_run"}},
        )
