import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
(ROOT / "tmp/tests").mkdir(parents=True, exist_ok=True)
os.environ.update(
    DATABASE_URL="sqlite:///tmp/tests/test.db",
    CHECKPOINT_URL="sqlite:///tmp/tests/checkpoints.db",
    MCP_TRANSPORT="memory",
    INFERENCE_MODE="smoke",
    EMBEDDING_BACKEND="hash_smoke",
    EXECUTOR="test",
)

from gigbid_core.db import User, db, init_db, uid
from gigbid_core.security import passwords
from scripts.seed import seed_tenant

init_db()


@pytest.fixture
def user():
    with db() as session:
        import json

        item = User(
            email=f"{uid()}@test.local",
            password_hash=passwords.hash("test-credential-only-000"),
            profile=json.dumps(
                {"persona": "ml", "minimum_project_budget": 200, "weekly_connects_budget": 100}
            ),
        )
        session.add(item)
        session.flush()
        seed_tenant(session, item)
    return item
