import asyncio
import json
import threading

import httpx
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from apps.api.main import app
from gigbid_core.db import Base, Record, User, db, get, put, uid
from scripts.seed import seed_tenant


def test_seed_batches_database_calls_and_preserves_existing_data():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    calls = []

    @event.listens_for(engine, "before_cursor_execute")
    def count(*args):
        calls.append(args[2].split()[0])

    try:
        with Session(engine) as session:
            user = User(id="seed-one")
            seed_tenant(session, user)
            session.flush()
            assert len(calls) <= 4, calls
            assert session.query(Record).filter_by(tenant=user.id, kind="evidence").count() == 330
            evidence = session.query(Record).filter_by(tenant=user.id, kind="evidence").first()
            custom = {**json.loads(evidence.payload), "text": "User's edited portfolio"}
            put(session, user.id, "evidence", evidence.record_id, custom)
            put(session, user.id, "wallet", "current", {"balance": 110, "weekly_spent": 10})
            session.flush()
            seed_tenant(session, user)
            session.flush()
            assert get(session, user.id, "evidence", evidence.record_id) == custom
            assert get(session, user.id, "wallet", "current")["balance"] == 110
            assert session.query(Record).filter_by(tenant=user.id).count() == 334
            seed_tenant(session, User(id="seed-two"))
            session.flush()
            assert session.query(Record).filter_by(tenant="seed-two").count() == 334
            assert get(session, "seed-two", "wallet", "current")["balance"] == 120
    finally:
        engine.dispose()


async def test_registration_allows_health_checks_and_login(monkeypatch):
    import scripts.seed

    started, release = threading.Event(), threading.Event()

    def slow_seed(session, user):
        started.set()
        assert release.wait(5), "Registration blocked the event loop"
        seed_tenant(session, user)

    monkeypatch.setattr(scripts.seed, "seed_tenant", slow_seed)
    credentials = {"email": uid() + "@test.local", "password": "registration-test-only-000"}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        pending = asyncio.create_task(c.post("/api/auth/register", json=credentials))
        try:
            assert await asyncio.to_thread(started.wait, 2)
            health = await asyncio.wait_for(c.get("/api/health"), timeout=1)
            assert health.status_code == 200
            assert not pending.done()
        finally:
            release.set()
        registered = await pending
        assert registered.status_code == 200, registered.text
        assert "gigbid_session" in registered.cookies
        tenant = registered.json()["id"]
        with db() as session:
            assert session.query(Record).filter_by(tenant=tenant, kind="evidence").count() == 330
            assert get(session, tenant, "wallet", "current")["balance"] == 120
        assert (await c.post("/api/auth/login", json=credentials)).status_code == 200
        assert (await c.get("/api/auth/me")).json()["id"] == tenant
        assert (await c.post("/api/auth/register", json=credentials)).status_code == 409
