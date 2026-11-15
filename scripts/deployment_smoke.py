"""Exercise the actual local Compose API, HTTP MCP and Postgres approval gate."""

import asyncio
import json
import subprocess
import time

import httpx
from dotenv import dotenv_values

from gigbid_core.config import ROOT, settings
from gigbid_core.security import token


async def main():
    cfg = dotenv_values(ROOT / ".env")
    base = "http://localhost:8080"
    with httpx.Client(base_url=base, timeout=30) as client:
        health = client.get("/api/health")
        health.raise_for_status()
        response = client.post(
            "/api/auth/login", json={"email": cfg["REVIEWER_EMAIL"], "password": cfg["REVIEWER_PASSWORD"]}
        )
        response.raise_for_status()
        user = response.json()
        settings().portfolio_mcp_url = "http://127.0.0.1:8101/mcp"
        settings().mcp_transport = "http"
        from langchain_mcp_adapters.client import MultiServerMCPClient

        remote = MultiServerMCPClient(
            {
                "portfolio": {
                    "transport": "streamable_http",
                    "url": settings().portfolio_mcp_url,
                    "headers": {
                        "Authorization": "Bearer " + token(user["id"], "mcp", ttl=300, server="portfolio")
                    },
                }
            }
        )
        tools = await remote.get_tools()
        assert {tool.name for tool in tools} == {"search_evidence", "get_case_study", "list_skills"}
        skills = await next(t for t in tools if t.name == "list_skills").ainvoke({})
        assert skills
        # This is a local synthetic test. It still requires a real human-approval API call.
        job_id = "syn-job-010"
        result = client.post("/api/jobs/" + job_id + "/analyze")
        result.raise_for_status()
        rid = result.json()["id"]
        deadline = time.time() + 300
        while time.time() < deadline:
            result = client.get("/api/runs/" + rid).json()
            if result["status"] not in {"queued", "running", "retry_queued"}:
                break
            await asyncio.sleep(2)
        assert result["status"] == "awaiting_approval", result
        subprocess.run(["docker", "compose", "restart", "api"], cwd=ROOT, check=True, capture_output=True)
        for _ in range(60):
            try:
                if client.get("/api/health").status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            await asyncio.sleep(1)
        else:
            raise RuntimeError("Web proxy did not recover within 60 checks after API restart")
        preserved = client.get("/api/runs/" + rid)
        preserved.raise_for_status()
        assert preserved.json()["status"] == "awaiting_approval"
        record = {
            "base_url": base,
            "public": False,
            "api_health": health.json(),
            "http_mcp_tools": [t.name for t in tools],
            "postgres_interrupt_survived_api_restart": True,
            "run_id": rid,
            "side_effect_status": "not executed; left for reviewer approval",
            "mode": "actual Compose with configured open models",
        }
        (ROOT / "evals/results/deployment_smoke.json").write_text(
            json.dumps(record, indent=2), encoding="utf-8"
        )
        print(json.dumps(record, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
