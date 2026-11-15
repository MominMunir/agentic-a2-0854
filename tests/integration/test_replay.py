from fastapi.testclient import TestClient

from agent.runtime import process_run
from apps.api.main import app
from gigbid_core.security import token
from tests.integration.test_workflow import start


async def test_checkpoint_replay_requires_fresh_approval(user):
    run_id = await start(user)
    with TestClient(app) as client:
        client.headers["Authorization"] = "Bearer " + token(user.id)
        history = client.get("/api/runs/" + run_id + "/history").json()
        checkpoint = history[0]["checkpoint_id"]
        rejected = client.post(
            "/api/runs/" + run_id + "/replay", json={"checkpoint_id": checkpoint, "stage": "execute"}
        )
        assert rejected.status_code == 422
        response = client.post(
            "/api/runs/" + run_id + "/replay", json={"checkpoint_id": checkpoint, "stage": "writer"}
        )
        assert response.status_code == 200, response.text
        new_id = response.json()["id"]
    await process_run(new_id)
    with TestClient(app) as client:
        client.headers["Authorization"] = "Bearer " + token(user.id)
        result = client.get("/api/runs/" + new_id).json()
        assert result["status"] == "awaiting_approval"
        assert not result["state"].get("outcome")
