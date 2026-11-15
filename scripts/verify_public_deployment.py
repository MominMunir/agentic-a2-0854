"""Read-only checks of the public app, scoped MCP, Neon and Qdrant.

Credentials are read only from an ignored private JSON file. No proposal is sent.
"""

import argparse
import asyncio
import json
from datetime import datetime, timezone

import httpx
from langchain_mcp_adapters.client import MultiServerMCPClient
from qdrant_client import QdrantClient
from sqlalchemy import create_engine, text

from gigbid_core.config import ROOT


def unpack(value):
    if isinstance(value, list):
        return json.loads("\n".join(item.get("text", "") for item in value if isinstance(item, dict)))
    return json.loads(value) if isinstance(value, str) else value


async def main(run_id, private_path):
    cfg = json.loads(private_path.read_text(encoding="utf-8"))
    base = cfg["APP_URL"].rstrip("/")
    if not base.startswith("https://"):
        raise ValueError("Public verification requires the intended HTTPS deployment origin")
    result = {
        "app_url": base,
        "portfolio_mcp_url": base + "/portfolio/mcp",
        "public": True,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "mode": "actual Groq inference on synthetic evidence; local marketplace simulator",
        "side_effect": "proposal left awaiting human approval; no submission requested",
    }
    try:
        async with httpx.AsyncClient(base_url=base, timeout=90) as client:
            health = await client.get("/api/health")
            health.raise_for_status()
            result["health"] = health.json()
            auth = await client.post(
                "/api/auth/login", json={"email": cfg["REVIEWER_EMAIL"], "password": cfg["REVIEWER_PASSWORD"]}
            )
            auth.raise_for_status()
            tenant = auth.json()["id"]
            result["reviewer_login"] = True
            response = await client.get("/api/runs/" + run_id)
            response.raise_for_status()
            run = response.json()
            assert run["status"] == "awaiting_approval"
            state = run["state"]
            assert state["draft"]["cover_letter"].strip()
            assert state["critique"]["accepted"] and state["compliance"]["allowed"]
            usage = state.get("usage", [])
            result.update(
                approval_state=run["status"],
                critic_accepted=True,
                compliance_passed=True,
                model_ids=sorted({u["model"] for u in usage}),
                tokens=sum(u.get("input_tokens", 0) + u.get("output_tokens", 0) for u in usage),
                usd_list_price_estimate=sum(u.get("usd_estimate", 0) for u in usage),
                synthetic_evidence=all(e.get("provenance") == "synthetic" for e in state["evidence"]),
            )
            assert result["tokens"] > 0
            scoped = await client.post("/api/portfolio/access-token")
            scoped.raise_for_status()
            body = scoped.json()
            bearer = body.get("access_token", body.get("token"))
            assert bearer
            headers = {"Authorization": "Bearer " + bearer}
            rpc = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
            unauth = await client.post("/portfolio/mcp", json=rpc)
            wrong_scope = await client.post("/marketplace/mcp", headers=headers, json=rpc)
            assert unauth.status_code == wrong_scope.status_code == 401
            remote = MultiServerMCPClient(
                {
                    "portfolio": {
                        "transport": "streamable_http",
                        "url": result["portfolio_mcp_url"],
                        "headers": headers,
                    }
                }
            )
            tools = await remote.get_tools()
            assert {t.name for t in tools} == {"search_evidence", "get_case_study", "list_skills"}
            evidence = unpack(
                await next(t for t in tools if t.name == "search_evidence").ainvoke(
                    {"requirement": "RAG FastAPI Python retail", "k": 3, "filters": {"persona": "ml"}}
                )
            )
            assert evidence["items"]
            result.update(
                http_mcp_tools=[t.name for t in tools],
                authenticated_retrieval=True,
                unauthenticated_mcp_rejected=True,
                cross_server_token_rejected=True,
            )
            for _ in range(3):
                repeated = await client.post(
                    "/api/auth/login",
                    json={"email": cfg["REVIEWER_EMAIL"], "password": cfg["REVIEWER_PASSWORD"]},
                )
                repeated.raise_for_status()
            result["repeat_login_after_retrieval"] = 3
        engine = create_engine(cfg["DATABASE_URL"], connect_args={"connect_timeout": 30})
        try:
            with engine.connect() as connection:
                connection.execute(text("SET TRANSACTION READ ONLY"))
                assert (
                    connection.execute(
                        text("select status from runs where id=:rid and tenant=:tenant"),
                        {"rid": run_id, "tenant": tenant},
                    ).scalar_one()
                    == "awaiting_approval"
                )
                count = connection.execute(
                    text("select count(*) from checkpoints where thread_id=:tid"),
                    {"tid": tenant + ":" + run_id},
                ).scalar_one()
                assert count > 0
                result.update(neon_run_persisted=True, neon_checkpoint_count=count)
        finally:
            engine.dispose()
        qdrant = QdrantClient(url=cfg["QDRANT_URL"], api_key=cfg["QDRANT_API_KEY"], timeout=30)
        try:
            collections = qdrant.get_collections().collections
            assert collections
            result["qdrant_collection_count"] = len(collections)
            result["qdrant_authenticated"] = True
        finally:
            qdrant.close()
        result["passed"] = True
    except Exception as exc:
        result.update(passed=False, error_type=type(exc).__name__)
        if isinstance(exc, httpx.HTTPStatusError):
            result["http_status"] = exc.response.status_code
            result["failed_path"] = exc.request.url.path
    (ROOT / "evals/results/public_deployment.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    with (ROOT / "evaluation/raw/public_deployment.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(result) + "\n")
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--private-config", type=lambda s: ROOT / s, default=ROOT / ".private/cloud-deployment.json"
    )
    args = parser.parse_args()
    asyncio.run(main(args.run_id, args.private_config))
