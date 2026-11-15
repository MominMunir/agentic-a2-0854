import copy
import json
import re

import pytest
from fastapi.testclient import TestClient

from agent.mcp_client import Tools
from agent.runtime import process_run
from apps.api.main import app
from gigbid_core.db import Effect, Run, db, get, uid
from gigbid_core.security import token
from tests.integration.test_workflow import start


async def test_deleted_evidence_cannot_authorize_a_stale_claim(user):
    rid = await start(user)
    with db() as session:
        state = json.loads(session.get(Run, rid).state)
    cited = re.findall(r"\[([^\]]+)\]", state["draft"]["cover_letter"])[0]
    with TestClient(app) as client:
        client.headers["Authorization"] = "Bearer " + token(user.id)
        assert client.delete("/api/portfolio/" + cited).status_code == 200
        assert client.post("/api/runs/" + rid + "/approve", json={"decision": "approve"}).status_code == 422
    with db() as session:
        assert session.query(Effect).filter_by(tenant=user.id).count() == 0


async def test_cost_change_needs_a_new_preview_and_approval(user, monkeypatch):
    rid = await start(user)
    with TestClient(app) as client:
        client.headers["Authorization"] = "Bearer " + token(user.id)
        assert client.post("/api/runs/" + rid + "/approve", json={"decision": "approve"}).status_code == 200
    from mcp_servers.marketplace.adapters import local

    changed = copy.deepcopy(local.policy())
    changed["marketplace"]["connect_surcharge"] = 3
    monkeypatch.setattr(local, "policy", lambda: changed)
    with pytest.raises(Exception):
        await process_run(rid)
    with db() as session:
        assert session.get(Run, rid).status == "needs_attention"
        assert get(session, user.id, "wallet", "current")["weekly_spent"] == 0
        assert session.query(Effect).filter_by(tenant=user.id).count() == 0


async def test_conversation_approval_sends_only_after_review(user):
    rid = uid()
    state = {
        "tenant": user.id,
        "run_id": rid,
        "conversation_id": "ml-client-demo",
        "profile": json.loads(user.profile),
        "usage": [],
        "steps": 0,
        "revision": 0,
    }
    with db() as session:
        session.add(
            Run(id=rid, tenant=user.id, job_id="ml-client-demo", kind="conversation", state=json.dumps(state))
        )
    await process_run(rid)
    with db() as session:
        assert session.get(Run, rid).status == "awaiting_approval"
        assert session.query(Effect).filter_by(tenant=user.id).count() == 0
    with TestClient(app) as client:
        client.headers["Authorization"] = "Bearer " + token(user.id)
        assert client.post("/api/runs/" + rid + "/approve", json={"decision": "approve"}).status_code == 200
    await process_run(rid)
    with db() as session:
        assert session.get(Run, rid).status == "sent"
        assert get(session, user.id, "wallet", "current")["weekly_spent"] == 0


async def test_calendar_hold_requires_explicit_confirmation_and_is_idempotent(user):
    slot = (await Tools(user.id, "ui").call("free_calendar_slots", days=7))["slots"][0]
    with TestClient(app) as client:
        client.headers["Authorization"] = "Bearer " + token(user.id)
        body = {**slot, "title": "Tentative interview"}
        assert client.post("/api/workspace/hold", json=body).json()["status"] == "preview"
        first = client.post("/api/workspace/hold", json={**body, "confirmed": True})
        assert first.status_code == 200, first.text
        assert first.json()["status"] == "created"
        second = client.post("/api/workspace/hold", json={**body, "confirmed": True})
        assert second.json() == first.json()
    remaining = (await Tools(user.id, "ui").call("free_calendar_slots", days=7))["slots"]
    assert slot not in remaining
