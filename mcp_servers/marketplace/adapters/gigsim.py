"""REST adapter. Endpoint mapping must be verified against supplied instructor API."""

import asyncio
import time
from collections import defaultdict, deque

import httpx

from gigbid_core.config import settings
from gigbid_core.security import tenant, trace_context
from mcp_servers.marketplace.adapters.local import validate_approval

windows = defaultdict(deque)


def polite_rate_limit():
    from gigbid_core.config import policy

    queue = windows[tenant()]
    tick = time.monotonic()
    while queue and tick - queue[0] >= 60:
        queue.popleft()
    if len(queue) >= policy()["marketplace"]["requests_per_minute"]:
        raise ConnectionError("Marketplace rate limit reached; work queued for a polite retry")
    queue.append(tick)


class GigSimAdapter:
    async def request(self, method, path, **kwargs):
        cfg = settings()
        polite_rate_limit()
        headers = {
            "Authorization": "Bearer " + cfg.gigsim_api_token,
            "X-Tenant-ID": tenant(),
            "X-Trace-ID": trace_context.get(),
        }
        async with httpx.AsyncClient(base_url=cfg.gigsim_base_url, timeout=20) as client:
            for attempt in range(3):
                response = await client.request(method, path, headers=headers, **kwargs)
                if response.status_code not in {429, 500, 502, 503, 504}:
                    response.raise_for_status()
                    data = response.json()
                    return data
                await asyncio.sleep(min(float(response.headers.get("Retry-After", 2**attempt)), 10))
        raise ConnectionError("Marketplace unavailable; queued for retry")

    async def search_jobs(self, query="", limit=30):
        data = await self.request("GET", "/jobs", params={"query": query, "limit": limit})
        return data.get("jobs", data) if isinstance(data, dict) else data

    async def get_job(self, job_id):
        return await self.request("GET", f"/jobs/{job_id}")

    async def get_client_history(self, client_id):
        return await self.request("GET", f"/clients/{client_id}/history")

    async def get_connects_balance(self):
        return await self.request("GET", "/connects")

    async def list_messages(self, conversation_id=""):
        return await self.request("GET", "/messages", params={"conversation_id": conversation_id})

    async def write(self, action, payload):
        if not payload["dry_run"]:
            validate_approval(payload, action)
        return await self.request(
            "POST",
            {
                "create_proposal_draft": "/proposals/drafts",
                "submit_proposal": "/proposals",
                "send_message": "/messages",
            }[action],
            json={k: v for k, v in payload.items() if k != "approval_token"},
        )

    async def create_proposal_draft(self, payload):
        return await self.write("create_proposal_draft", payload)

    async def submit_proposal(self, payload):
        return await self.write("submit_proposal", payload)

    async def send_message(self, payload):
        return await self.write("send_message", payload)
