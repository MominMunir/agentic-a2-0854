import json

import pytest
from fastapi.testclient import TestClient

from agent.mcp_client import Tools
from agent.runtime import process_run
from apps.api.main import app
from gigbid_core.db import Effect, Run, db, get, put, uid
from gigbid_core.security import fingerprint, token


async def start(user, job_id="syn-job-001"):
    job = await Tools(user.id, "scout").call("get_job", job_id=job_id)
    rid = uid()
    with db() as session:
        session.add(
            Run(
                id=rid,
                tenant=user.id,
                job_id=job_id,
                state=json.dumps(
                    {
                        "tenant": user.id,
                        "run_id": rid,
                        "job": job,
                        "profile": json.loads(user.profile),
                        "usage": [],
                        "steps": 0,
                        "revision": 0,
                    }
                ),
            )
        )
    await process_run(rid)
    return rid


async def test_durable_interrupt_resume_and_idempotency(user):
    rid = await start(user)
    with db() as session:
        run = session.get(Run, rid)
        assert run.status == "awaiting_approval"
        state = json.loads(run.state)
        assert session.query(Effect).filter_by(tenant=user.id).count() == 0
        body = {
            "job_id": run.job_id,
            "text": state["draft"]["cover_letter"],
            "bid": state["price"]["amount"],
            "expected_connects_cost": state["preview"]["connects_cost"],
            "screening_answers": state["draft"]["screening_answers"],
        }
        proof = token(user.id, "approval", action="submit_proposal", digest=fingerprint(body))
        put(session, user.id, "resume", rid, {"decision": "approve", "approval_token": proof})
        run.status = "queued"
    # New checkpointer/graph object opens the on-disk interrupted thread.
    await process_run(rid)
    with db() as session:
        assert session.get(Run, rid).status == "submitted"
        spent = get(session, user.id, "wallet", "current")["weekly_spent"]
    request = {**body, "idempotency_key": rid, "dry_run": False, "approval_token": proof}
    first = await Tools(user.id, "approval").call("submit_proposal", request=request)
    second = await Tools(user.id, "approval").call("submit_proposal", request=request)
    assert first == second
    with db() as session:
        assert session.query(Effect).filter_by(tenant=user.id).count() == 1
        assert get(session, user.id, "wallet", "current")["weekly_spent"] == spent


async def test_scam_stops_before_writes(user):
    rid = await start(user, "syn-job-000")
    with db() as session:
        run = session.get(Run, rid)
        assert run.status == "skip"
        assert json.loads(run.state)["risk"]["injection_detected"]
        assert session.query(Effect).filter_by(tenant=user.id).count() == 0


async def test_rejection_has_no_effect(user):
    rid = await start(user)
    with db() as session:
        put(session, user.id, "resume", rid, {"decision": "reject", "reason": "Scope is not appropriate"})
        session.get(Run, rid).status = "queued"
    await process_run(rid)
    with db() as session:
        assert session.get(Run, rid).status == "rejected"
        assert session.query(Effect).filter_by(tenant=user.id).count() == 0


async def test_tool_permissions_and_unapproved_write(user):
    with pytest.raises(PermissionError):
        await Tools(user.id, "writer").call("submit_proposal", request={})
    with pytest.raises(Exception):
        await Tools(user.id, "approval").call(
            "submit_proposal",
            request={
                "job_id": "syn-job-001",
                "text": "I propose a validation step.",
                "bid": 600,
                "idempotency_key": uid(),
                "dry_run": False,
            },
        )


def test_tenant_isolation_and_bad_edit(user):
    with TestClient(app) as client:
        client.headers["Authorization"] = "Bearer " + token(user.id)
        assert client.get("/api/auth/me").status_code == 200
        assert client.get("/api/runs/not-owned").status_code == 404
        with db() as session:
            rid = uid()
            session.add(Run(id=rid, tenant="another-user", job_id="private-job"))
        assert client.get("/api/runs/" + rid).status_code == 404
        assert client.get("/api/analytics").status_code == 200


async def test_critic_exhaustion_stops_without_approval_or_effect(user, monkeypatch):
    import agent.graphs.bid_graph as graph_module
    from gigbid_core.config import policy

    calls = []

    async def inadequate_writer(state):
        calls.append(state.get("revision", 0))
        return {
            "draft": {
                "cover_letter": "I would clarify acceptance criteria.",
                "evidence_ids": [],
                "screening_answers": [],
            },
            "usage": [],
            "steps": 1,
        }

    monkeypatch.setattr(graph_module, "writer", inadequate_writer)
    rid = await start(user)
    with db() as session:
        run = session.get(Run, rid)
        state = json.loads(run.state)
        assert run.status == "needs_attention"
        assert len(calls) == policy()["budgets"]["max_revisions"] + 1
        assert not state["compliance"]["allowed"]
        assert session.query(Effect).filter_by(tenant=user.id).count() == 0
        assert "preview" not in state


async def test_ui_edits_rechecked(user):
    rid = await start(user)
    with TestClient(app) as client:
        client.headers["Authorization"] = "Bearer " + token(user.id)
        assert (
            client.patch(
                "/api/runs/" + rid + "/draft", json={"text": "I built systems for 200 major clients."}
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/runs/" + rid + "/approve", json={"decision": "reject", "reason": ""}
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/runs/" + rid + "/approve",
                json={"decision": "approve", "text": "I guarantee 100% success."},
            ).status_code
            == 422
        )
