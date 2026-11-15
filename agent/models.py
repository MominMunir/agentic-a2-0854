import asyncio
import json
import time

import httpx

from gigbid_core.config import SOURCE_ROOT, policy, settings


class ModelUnavailable(ConnectionError):
    pass


async def generate(node, payload, schema=None, profile=None):
    cfg, config = settings(), policy()
    selected = profile or cfg.model_profile
    profile_config = config["models"]["profiles"][selected]
    model = profile_config[config["models"]["nodes"].get(node, "small")]
    primary_model = model
    fallback = config["models"].get("cheap_node_fallbacks", {}).get(selected)
    candidates = [model]
    if config["models"]["nodes"].get(node, "small") == "small" and fallback and fallback != model:
        candidates.append(fallback)
    prompt = (SOURCE_ROOT / "agent/prompts" / f"{node}.md").read_text(encoding="utf-8")
    if schema:
        prompt += "\nReturn only a JSON object matching this JSON Schema: " + json.dumps(
            schema.model_json_schema()
        )
    messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": "<untrusted_context>\n"
            + json.dumps(payload, ensure_ascii=False)
            + "\n</untrusted_context>",
        },
    ]
    if cfg.inference_mode == "smoke":
        raise ModelUnavailable("Smoke mode does not impersonate a language model")
    base = (
        cfg.ollama_base_url.rstrip("/") + "/v1" if cfg.inference_mode == "ollama" else cfg.open_model_base_url
    )
    key = cfg.open_model_api_key or "local"
    started = time.perf_counter()
    body = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 5000 if node == "router" else config["models"].get("max_output_tokens", 1800),
    }
    if "gpt-oss" in model:
        body["reasoning_effort"] = "low"
    if schema:
        body["response_format"] = {"type": "json_object"}
    async with httpx.AsyncClient(timeout=60) as client:
        for model in candidates:
            body["model"] = model
            for attempt in range(3):
                try:
                    response = await client.post(
                        base.rstrip("/") + "/chat/completions",
                        headers={"Authorization": "Bearer " + key},
                        json=body,
                    )
                    if response.status_code in {429, 500, 502, 503, 504}:
                        if attempt < 2:
                            await asyncio.sleep(
                                min(float(response.headers.get("retry-after", 2**attempt)), 10)
                            )
                        continue
                    response.raise_for_status()
                    result = response.json()
                    content = result["choices"][0]["message"]["content"] or ""
                    content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                    usage = result.get("usage", {})
                    input_tokens, output_tokens = (
                        usage.get("prompt_tokens", 0),
                        usage.get("completion_tokens", 0),
                    )
                    prices = config["models"].get("pricing", {}).get(model, [0, 0])
                    usd = (
                        (input_tokens * prices[0] + output_tokens * prices[1]) / 1_000_000
                        if cfg.inference_mode != "ollama"
                        else 0
                    )
                    observation = {
                        "node": node,
                        "model": model,
                        "fallback_from": primary_model if model != primary_model else None,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "usd_estimate": usd,
                        "pricing_basis": "public list price; not account invoice",
                        "latency_seconds": time.perf_counter() - started,
                    }
                    from gigbid_core.tracing import span

                    with span(
                        "llm." + node,
                        model=model,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        usd_estimate=usd,
                    ):
                        pass
                    return (schema.model_validate_json(content) if schema else content), observation
                except httpx.HTTPStatusError:
                    raise ModelUnavailable(
                        "Open model rejected the request; check provider configuration"
                    ) from None
                except httpx.TransportError:
                    if attempt < 2:
                        await asyncio.sleep(2**attempt)
    raise ModelUnavailable(
        "Open model quota or transport unavailable after bounded retries and configured fallback"
    )
