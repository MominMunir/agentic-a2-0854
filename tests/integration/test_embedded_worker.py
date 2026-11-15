import asyncio

from fastapi.testclient import TestClient

from apps.api.main import app
from gigbid_core.config import settings


def test_compact_worker_lifecycle(monkeypatch):
    import arq.worker

    events = []

    class Worker:
        async def async_run(self):
            events.append("started")
            await asyncio.Event().wait()

        async def close(self):
            events.append("closed")

    monkeypatch.setattr(settings(), "embedded_worker", True)
    monkeypatch.setattr(arq.worker, "create_worker", lambda *args, **kwargs: Worker())
    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200
        assert "started" in events
    assert "closed" in events


def test_compact_health_reports_failed_worker(monkeypatch):
    import arq.worker

    class Worker:
        async def async_run(self):
            return

        async def close(self):
            pass

    monkeypatch.setattr(settings(), "embedded_worker", True)
    monkeypatch.setattr(arq.worker, "create_worker", lambda *args, **kwargs: Worker())
    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 503
