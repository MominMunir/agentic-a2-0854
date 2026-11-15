import json
import os

from dotenv import load_dotenv
from sqlalchemy import insert

from gigbid_core.config import ROOT
from gigbid_core.db import Record, User, db, init_db, now
from gigbid_core.security import passwords


def seed_tenant(session, user):
    # Fetch once and insert as a batch: per-item get/put caused 999 database
    # statements for a new tenant over the remote database connection.
    existing = {
        item.key: item
        for item in session.query(Record)
        .filter(Record.tenant == user.id, Record.kind.in_(["evidence", "message", "wallet"]))
        .all()
    }
    missing = []
    timestamp = now()

    def stage(kind, record_id, payload, refresh=False):
        key = f"{user.id}:{kind}:{record_id}"
        encoded = json.dumps(payload)
        if key in existing:
            if refresh:
                existing[key].payload = encoded
                existing[key].updated = timestamp
        else:
            missing.append(
                dict(
                    key=key,
                    tenant=user.id,
                    kind=kind,
                    record_id=record_id,
                    payload=encoded,
                    updated=timestamp,
                )
            )

    for item in json.loads((ROOT / "data/synthetic/evidence.json").read_text()):
        stage("evidence", item["id"], item)
    for message in json.loads((ROOT / "data/synthetic/conversations.json").read_text()):
        stage("message", message["id"], message, refresh=True)
    stage("wallet", "current", {"balance": 120, "weekly_spent": 0})
    if missing:
        session.execute(insert(Record), missing)


def main():
    load_dotenv(ROOT / ".env")
    init_db()
    email, password = os.getenv("REVIEWER_EMAIL"), os.getenv("REVIEWER_PASSWORD")
    if not email or not password:
        raise SystemExit(
            "REVIEWER_EMAIL and REVIEWER_PASSWORD must be supplied through environment variables."
        )
    with db() as session:
        user = session.query(User).filter_by(email=email.lower()).first()
        if not user:
            user = User(
                email=email.lower(),
                password_hash=passwords.hash(password),
                profile=json.dumps(
                    {
                        "persona": "ml",
                        "hourly_rate": 45,
                        "minimum_project_budget": 200,
                        "weekly_connects_budget": 100,
                        "saved_search": "Python",
                        "autonomy": "review",
                    }
                ),
            )
            session.add(user)
            session.flush()
        seed_tenant(session, user)
    print("Reviewer account seeded from environment. Credentials were not printed.")


if __name__ == "__main__":
    main()
