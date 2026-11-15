"""Test the compact image at the free host's 512 MiB ceiling, locally only."""

import asyncio
import json
import secrets
import subprocess
import time

import httpx
from dotenv import dotenv_values
from langchain_mcp_adapters.client import MultiServerMCPClient

from gigbid_core.config import ROOT


def docker(*args, check=True):
    return subprocess.run(["docker", *args], cwd=ROOT, capture_output=True, text=True, check=check)


async def main():
    cfg = dict(dotenv_values(ROOT / ".env"))
    # Keep benchmark/reviewer runs in the main database untouched on repeat tests.
    docker("exec", "gigbid-postgres-1", "createdb", "-U", "gigbid", "gigbid_free_smoke", check=False)
    cfg.update(
        APP_ENV="development",
        APP_URL="http://localhost:10000",
        PORT="10000",
        DATABASE_URL=f"postgresql+psycopg://gigbid:{cfg['POSTGRES_PASSWORD']}@postgres:5432/gigbid_free_smoke",
        CHECKPOINT_URL=f"postgresql://gigbid:{cfg['POSTGRES_PASSWORD']}@postgres:5432/gigbid_free_smoke",
        REDIS_URL="redis://redis:6379/2",
        QDRANT_URL="http://qdrant:6333",
        OTEL_EXPORTER_OTLP_ENDPOINT="",
        INFERENCE_MODE="smoke",
        EMBEDDING_BACKEND="fastembed",
        RAG_VARIANT="v0",
    )
    private = ROOT / ".private/compact.env"
    private.write_text("\n".join(f"{k}={v}" for k, v in cfg.items() if v is not None), encoding="utf-8")
    name = "gigbid-free-test"
    prior = docker("inspect", name, check=False)
    if prior.returncode == 0:
        old = json.loads(prior.stdout)[0]
        if old["State"]["Running"]:
            raise RuntimeError("The prior project test container is still running")
        docker("rm", name)
    docker(
        "run",
        "--detach",
        "--name",
        name,
        "--memory",
        "512m",
        "--memory-swap",
        "512m",
        "--cpus",
        "1",
        "--network",
        "gigbid_default",
        "-p",
        "127.0.0.1:10000:10000",
        "--env-file",
        str(private),
        "gigbid-free-demo:latest",
    )
    started = time.monotonic()
    result = {
        "public": False,
        "image": "gigbid-free-demo:latest",
        "memory_limit_mib": 512,
        "inference": "deterministic smoke; actual CPU embeddings, HTTP MCP, Postgres and Redis",
    }
    try:
        async with httpx.AsyncClient(base_url=cfg["APP_URL"], timeout=10) as client:
            for _ in range(100):
                try:
                    if (await client.get("/api/health")).status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                await asyncio.sleep(1)
            else:
                raise RuntimeError("Compact container did not become healthy")
            result["startup_seconds"] = time.monotonic() - started
            home = await client.get("/")
            home.raise_for_status()
            assert 'id="root"' in home.text
            auth = await client.post(
                "/api/auth/register",
                json={
                    "email": "compact-" + secrets.token_hex(4) + "@test.local",
                    "password": secrets.token_urlsafe(24),
                },
            )
            auth.raise_for_status()
            scoped = await client.post("/api/portfolio/access-token")
            scoped.raise_for_status()
            values = scoped.json()
            bearer = values.get("access_token", values.get("token"))
            assert bearer
            headers = {"Authorization": "Bearer " + bearer}
            remote = MultiServerMCPClient(
                {
                    "portfolio": {
                        "transport": "streamable_http",
                        "url": cfg["APP_URL"] + "/portfolio/mcp",
                        "headers": headers,
                    }
                }
            )
            tools = await remote.get_tools()
            assert {t.name for t in tools} == {"search_evidence", "get_case_study", "list_skills"}
            evidence = await next(t for t in tools if t.name == "search_evidence").ainvoke(
                {"requirement": "Python classification retail", "k": 5}
            )
            assert evidence
            wrong = await client.post(
                "/marketplace/mcp", headers=headers, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
            )
            assert wrong.status_code == 401
            run = await client.post("/api/jobs/syn-job-010/analyze")
            run.raise_for_status()
            rid = run.json()["id"]
            for _ in range(100):
                state = (await client.get("/api/runs/" + rid)).json()
                if state["status"] not in {"queued", "running", "retry_queued"}:
                    break
                await asyncio.sleep(1)
            assert state["status"] == "awaiting_approval", state.get("error", state["status"])
            result.update(
                frontend=True,
                authenticated_mcp=True,
                cross_server_token_rejected=True,
                postgres_redis_interrupt=True,
                side_effect="not executed",
                run_id=rid,
            )
        result["docker_memory"] = docker(
            "stats", "--no-stream", "--format", "{{.MemUsage}}", name
        ).stdout.strip()
        peak = docker("exec", name, "cat", "/sys/fs/cgroup/memory.peak", check=False)
        result["cgroup_peak_mib"] = (
            round(int(peak.stdout.strip()) / 1024**2, 2) if peak.returncode == 0 else None
        )
        result["passed"] = True
    except Exception as exc:
        result.update(passed=False, error=f"{type(exc).__name__}: {str(exc)[:200]}")
        raise
    finally:
        inspect = json.loads(docker("inspect", name).stdout)[0]["State"]
        result["oom_killed"] = inspect["OOMKilled"]
        (ROOT / "evals/results/free_deployment_smoke.json").write_text(
            json.dumps(result, indent=2), encoding="utf-8"
        )
        with (ROOT / "evaluation/raw/free_deployment.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(result) + "\n")
        docker("stop", name, check=False)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
