"""Independent synthetic simulator, intentionally separate from instructor gigsim/."""

import json
from contextlib import contextmanager

from sqlalchemy.orm import Session as SQLSession

from gigbid_core.config import ROOT, policy
from gigbid_core.db import Effect, db, engine, get, put, records, uid
from gigbid_core.security import decode, fingerprint, tenant


@contextmanager
def atomic():
    with engine.connect() as connection:
        if engine.dialect.name == "sqlite":
            connection.exec_driver_sql("BEGIN IMMEDIATE")
        else:
            connection.begin()
        try:
            with SQLSession(bind=connection) as session:
                yield session
                session.flush()
            connection.commit()
        except Exception:
            connection.rollback()
            raise


def validate_approval(payload, action):
    claims = decode(payload.get("approval_token", ""), "approval")
    body = {k: v for k, v in payload.items() if k not in {"approval_token", "dry_run", "idempotency_key"}}
    if (
        claims["sub"] != tenant()
        or claims.get("action") != action
        or claims.get("digest") != fingerprint(body)
    ):
        raise PermissionError("Approval does not match this user, action and content")


class LocalSimulatorAdapter:
    async def search_jobs(self, query="", limit=30):
        jobs = json.loads((ROOT / "data/synthetic/jobs.json").read_text())
        real_path = ROOT / "data/processed/real/jobs.json"
        if real_path.exists():
            jobs += json.loads(real_path.read_text(encoding="utf-8"))
        terms = query.lower().split()
        jobs.sort(
            key=lambda j: sum(t in (j["title"] + j["description"]).lower() for t in terms), reverse=True
        )
        return jobs[:limit]

    async def get_job(self, job_id):
        jobs = await self.search_jobs("", 100000)
        job = next((j for j in jobs if j["id"] == job_id), None)
        if not job:
            raise ValueError("Job not found")
        return job

    async def get_client_history(self, client_id):
        clients = json.loads((ROOT / "data/synthetic/clients.json").read_text())
        return next(
            (c for c in clients if c["id"] == client_id),
            {
                "id": client_id,
                "payment_verified": None,
                "completed_projects": None,
                "total_spend": None,
                "rating": None,
                "provenance": "unavailable",
            },
        )

    async def get_connects_balance(self):
        with db() as session:
            wallet = get(session, tenant(), "wallet", "current") or {"balance": 120, "weekly_spent": 0}
            return wallet

    async def list_messages(self, conversation_id=""):
        with db() as session:
            data = records(session, tenant(), "message")
            return [m for m in data if not conversation_id or m["conversation_id"] == conversation_id]

    async def create_proposal_draft(self, payload):
        return await self._write("create_proposal_draft", payload)

    async def submit_proposal(self, payload):
        return await self._write("submit_proposal", payload)

    async def send_message(self, payload):
        return await self._write("send_message", payload)

    async def _write(self, action, payload):
        job = await self.get_job(payload["job_id"]) if "job_id" in payload else None
        cost = (
            (job["connects_cost"] + policy()["marketplace"]["connect_surcharge"])
            if action == "submit_proposal"
            else 0
        )
        clean = {k: v for k, v in payload.items() if k not in {"approval_token", "dry_run"}}
        if payload["dry_run"]:
            return {
                "status": "preview",
                "action": action,
                "connects_cost": cost,
                "payload": clean,
                "marketplace": "local_simulator",
            }
        validate_approval(payload, action)
        digest = fingerprint(clean)
        key = f"{tenant()}:{action}:{payload['idempotency_key']}"
        with atomic() as session:
            previous = session.get(Effect, key)
            if previous:
                if previous.request_hash != digest:
                    raise ValueError("Idempotency key already belongs to different content")
                return json.loads(previous.result)
            if action == "submit_proposal" and payload.get("expected_connects_cost") != cost:
                raise ValueError(
                    "Connects cost changed. Refresh the preview and approve the new cost before submitting."
                )
            # Serialize the wallet in Postgres, alongside the unique effect ledger.
            from gigbid_core.db import Record, User

            session.query(User).filter_by(id=tenant()).with_for_update().first()
            session.query(Record).filter_by(key=f"{tenant()}:wallet:current").with_for_update().first()
            wallet = get(session, tenant(), "wallet", "current") or {"balance": 120, "weekly_spent": 0}
            user = session.get(User, tenant())
            profile = json.loads(user.profile) if user else {}
            if cost > wallet["balance"] or wallet["weekly_spent"] + cost > profile.get(
                "weekly_connects_budget", 100
            ):
                raise ValueError("Insufficient Connects or weekly budget exceeded")
            wallet["balance"] -= cost
            wallet["weekly_spent"] += cost
            put(session, tenant(), "wallet", "current", wallet)
            record_id = uid()
            result = {
                "id": record_id,
                "status": "submitted"
                if action == "submit_proposal"
                else "sent"
                if action == "send_message"
                else "drafted",
                "connects_cost": cost,
                **clean,
                "marketplace": "local_simulator",
                "synthetic": True,
            }
            put(session, tenant(), "message" if action == "send_message" else "proposal", record_id, result)
            if action == "submit_proposal":
                # Deterministic local outcome, never represented as an LLM or GigSim outcome.
                reply = {
                    "id": uid(),
                    "conversation_id": job["id"],
                    "role": "client",
                    "text": "Thanks for the proposal. How would you validate the deliverable? Could you suggest interview slots?",
                    "synthetic": True,
                    "provenance": "local_rule_simulator",
                }
                put(session, tenant(), "message", reply["id"], reply)
                result["local_outcome"] = "replied"
            session.add(
                Effect(key=key, tenant=tenant(), request_hash=digest, result=json.dumps(result), cost=cost)
            )
            return result
