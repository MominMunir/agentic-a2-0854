"""Create one isolated synthetic account and verify registration on the public app.

No proposals/messages are approved or sent. Generated credentials stay private.
"""

import asyncio
import json
import secrets
from datetime import datetime, timezone
from time import perf_counter

import httpx
from sqlalchemy import create_engine, text

from gigbid_core.config import ROOT


async def main():
    cfg = json.loads((ROOT / ".private/cloud-deployment.json").read_text(encoding="utf-8"))
    base = cfg["APP_URL"].rstrip("/")
    assert base == "https://gigbid-wr80.onrender.com"
    result = {"app_url": base, "checked_at": datetime.now(timezone.utc).isoformat()}
    reviewer_run = "0a326b18-6bed-40e2-b964-0d268940210b"
    async with httpx.AsyncClient(base_url=base, timeout=90) as reviewer:
        auth = await reviewer.post(
            "/api/auth/login",
            json={"email": cfg["REVIEWER_EMAIL"], "password": cfg["REVIEWER_PASSWORD"]},
        )
        auth.raise_for_status()
        reviewer_id = auth.json()["id"]
        before = await reviewer.get("/api/runs/" + reviewer_run)
        before.raise_for_status()
        assert before.json()["status"] == "awaiting_approval"
        old_state = before.json()["state"]
        credentials = {
            "email": "registration-check-" + secrets.token_hex(6) + "@gigbid.local",
            "password": secrets.token_urlsafe(24),
        }
        (ROOT / ".private/registration-check.json").write_text(
            json.dumps({"app_url": base, **credentials}, indent=2), encoding="utf-8"
        )
        async with httpx.AsyncClient(base_url=base, timeout=90, headers={"Origin": base}) as c:
            health_samples = []
            done = asyncio.Event()

            async def observe_health():
                async with httpx.AsyncClient(base_url=base, timeout=10) as observer:
                    while not done.is_set():
                        tick = perf_counter()
                        response = await observer.get("/api/health")
                        response.raise_for_status()
                        health_samples.append(perf_counter() - tick)
                        await asyncio.sleep(0.2)

            monitor = asyncio.create_task(observe_health())
            started = perf_counter()
            try:
                registered = await c.post("/api/auth/register", json=credentials)
                elapsed = perf_counter() - started
                registered.raise_for_status()
            finally:
                done.set()
                await monitor
            tenant = registered.json()["id"]
            assert tenant != reviewer_id
            me = await c.get("/api/auth/me")
            me.raise_for_status()
            assert me.json()["id"] == tenant and me.json()["email"] == credentials["email"]
            assert (await c.get("/api/runs/" + reviewer_run)).status_code == 404
            items = await c.get("/api/portfolio")
            items.raise_for_status()
            messages = await c.get("/api/messages")
            messages.raise_for_status()
            analytics = await c.get("/api/analytics")
            analytics.raise_for_status()
            assert analytics.json()["wallet"] == {"balance": 120, "weekly_spent": 0}
            assert len(messages.json()["messages"]) == 3
            assert items.json()["count"] > 0
            duplicate = await c.post("/api/auth/register", json=credentials)
            assert duplicate.status_code == 409
            await c.post("/api/auth/logout")
            login = await c.post("/api/auth/login", json=credentials)
            login.raise_for_status()
            assert login.json()["id"] == tenant
            result.update(
                register_status=registered.status_code,
                registration_seconds=round(elapsed, 3),
                health_samples_during_registration=len(health_samples),
                max_health_seconds=round(max(health_samples), 3),
                duplicate_status=duplicate.status_code,
                login=True,
                session=True,
                cross_tenant_reviewer_run_rejected=True,
                persona_portfolio_count=items.json()["count"],
                seeded_messages=3,
                wallet_balance=120,
                wallet_spent=0,
            )
        after = await reviewer.get("/api/runs/" + reviewer_run)
        after.raise_for_status()
        assert after.json()["status"] == "awaiting_approval" and after.json()["state"] == old_state
        result["reviewer_pending_draft_unchanged"] = True
    engine = create_engine(cfg["DATABASE_URL"], connect_args={"connect_timeout": 30})
    try:
        with engine.connect() as connection:
            connection.execute(text("SET TRANSACTION READ ONLY"))
            count = connection.execute(
                text("SELECT count(*) FROM records WHERE tenant=:tenant AND kind='evidence'"),
                {"tenant": tenant},
            ).scalar_one()
            assert count == 330
            result["seeded_evidence_count"] = count
    finally:
        engine.dispose()
    result.update(passed=True, effects="One synthetic test account; no proposals or messages sent")
    (ROOT / "evals/results/registration.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
