import json
import os

from dotenv import load_dotenv

from gigbid_core.config import ROOT
from gigbid_core.db import User, db, get, init_db, put
from gigbid_core.security import passwords


def seed_tenant(session, user):
    for item in json.loads((ROOT / "data/synthetic/evidence.json").read_text()):
        if not get(session, user.id, "evidence", item["id"]):
            put(session, user.id, "evidence", item["id"], item)
    for message in json.loads((ROOT / "data/synthetic/conversations.json").read_text()):
        put(session, user.id, "message", message["id"], message)
    if not get(session, user.id, "wallet", "current"):
        put(session, user.id, "wallet", "current", {"balance": 120, "weekly_spent": 0})


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
