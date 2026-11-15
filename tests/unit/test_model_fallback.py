import httpx
import pytest

from agent import models
from gigbid_core.config import settings


@pytest.mark.asyncio
async def test_cheap_node_falls_back_after_bounded_rate_limits(monkeypatch):
    monkeypatch.setattr(settings(), "inference_mode", "groq")
    monkeypatch.setattr(settings(), "open_model_base_url", "https://model.test/v1")
    attempted = []

    class Client:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, *, json, **kwargs):
            attempted.append(json["model"])
            request = httpx.Request("POST", url)
            if json["model"] == "openai/gpt-oss-20b":
                return httpx.Response(429, headers={"retry-after": "0"}, request=request)
            return httpx.Response(
                200,
                request=request,
                json={
                    "choices": [{"message": {"content": "fallback response"}}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 5},
                },
            )

    monkeypatch.setattr(models.httpx, "AsyncClient", Client)
    result, observation = await models.generate("analyst", {}, profile="open")
    assert result == "fallback response"
    assert attempted == ["openai/gpt-oss-20b"] * 3 + ["openai/gpt-oss-120b"]
    assert observation["fallback_from"] == "openai/gpt-oss-20b"
    assert observation["usd_estimate"] > 0
