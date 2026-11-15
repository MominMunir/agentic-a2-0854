"""Actual ReAct, prebuilt supervisor and handwritten LangGraph comparison."""

import argparse
import asyncio
import json
import time

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from pydantic import BaseModel
from typing import Literal

from agent.mcp_client import Tools
from agent.runtime import process_run
from evaluation.run import save
from gigbid_core.config import ROOT, policy, settings
from gigbid_core.db import Run, User, db, uid
from rag.verify import compliance, verify


class ResearchOutput(BaseModel):
    action: Literal["bid", "skip", "watch"]
    cover_letter: str
    risk_flags: list[str]
    bid_amount: float


async def baseline(query, tenant, architecture):
    evidence = {}
    finalized = []

    @tool("json", return_direct=True)
    def finalize_assessment(action: str, cover_letter: str, risk_flags: list[str], bid_amount: float) -> dict:
        """Return the final structured assessment. This records a research artifact only; no marketplace action."""
        output = ResearchOutput(
            action=action, cover_letter=cover_letter, risk_flags=risk_flags, bid_amount=bid_amount
        ).model_dump()
        finalized.append(output)
        return output

    @tool
    async def portfolio_lookup(requirement: str) -> dict:
        """Read portfolio evidence for the job requirement, scoped to this persona."""
        result = await Tools(tenant, "fit_matcher").call(
            "search_evidence",
            requirement=requirement,
            k=5,
            filters={"persona": query["persona"], "type": "case_study"},
        )
        evidence.update({item["id"]: item for item in result["items"]})
        return result

    @tool
    async def client_lookup(client_id: str) -> dict:
        """Read client hiring and payment history for the supplied client ID."""
        return await Tools(tenant, "risk_assessor").call("get_client_history", client_id=client_id)

    model = policy()["models"]["profiles"]["open"]["strong"]
    llm = ChatOpenAI(
        model=model,
        base_url=settings().open_model_base_url,
        api_key=settings().open_model_api_key,
        temperature=0,
        max_tokens=1800,
        reasoning_effort="low",
        timeout=60,
        max_retries=2,
    )
    prompt = (ROOT / "agent/prompts/research_single.md").read_text()
    if architecture == "react":
        graph = create_react_agent(llm, [portfolio_lookup, client_lookup, finalize_assessment], prompt=prompt)
    else:
        researcher = create_react_agent(
            llm, [portfolio_lookup, client_lookup, finalize_assessment], prompt=prompt, name="researcher"
        )
        specialist = create_react_agent(
            llm, [portfolio_lookup, finalize_assessment], prompt=prompt, name="proposal_specialist"
        )
        graph = create_supervisor(
            [researcher, specialist],
            model=llm,
            tools=[finalize_assessment],
            prompt=(ROOT / "agent/prompts/research_supervisor.md").read_text(),
            output_mode="full_history",
        ).compile()
    result = await graph.ainvoke(
        {
            "messages": [
                {"role": "user", "content": "<untrusted_job>" + json.dumps(query["job"]) + "</untrusted_job>"}
            ]
        },
        {"recursion_limit": 20},
    )
    messages = result["messages"]
    final = next(
        (
            m.content
            for m in reversed(messages)
            if getattr(m, "type", "") == "ai" and m.content and not getattr(m, "tool_calls", [])
        ),
        "{}",
    )
    final = str(final).strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    structured = result.get("structured_response")
    decision = (
        finalized[-1]
        if finalized
        else structured.model_dump()
        if hasattr(structured, "model_dump")
        else structured
        if isinstance(structured, dict)
        else json.loads(final)
    )
    seen, usage = set(), []
    for message in messages:
        if message.id not in seen and getattr(message, "usage_metadata", None):
            seen.add(message.id)
            usage.append(message.usage_metadata)
    claims = verify(decision.get("cover_letter", ""), list(evidence.values()))
    tokens = sum(u.get("input_tokens", 0) + u.get("output_tokens", 0) for u in usage)
    prices = policy()["models"]["pricing"][model]
    usd = (
        sum(u.get("input_tokens", 0) * prices[0] + u.get("output_tokens", 0) * prices[1] for u in usage)
        / 1_000_000
    )
    return {
        "decision": decision.get("action"),
        "cover_letter": decision.get("cover_letter", ""),
        "unsupported_before": claims["unsupported_before"],
        "unsupported_after": verify(claims["text"], list(evidence.values()))["unsupported_before"],
        "policy_violations": len(compliance(decision.get("cover_letter", ""))["violations"]),
        "tokens": tokens,
        "usd_estimate": usd,
        "usage": usage,
        "tool_calls": sum(len(getattr(m, "tool_calls", [])) for m in messages),
        "evidence_ids": list(evidence),
        "model": model,
    }


async def handwritten(query, tenant, profile):
    settings().model_profile = profile
    rid = uid()
    state = {
        "tenant": tenant,
        "run_id": rid,
        "job": query["job"],
        "profile": {
            "persona": query["persona"],
            "minimum_project_budget": 200,
            "weekly_connects_budget": 100,
        },
        "steps": 0,
        "usage": [],
        "revision": 0,
    }
    with db() as session:
        session.add(Run(id=rid, tenant=tenant, job_id=query["id"], state=json.dumps(state)))
    await process_run(rid)
    with db() as session:
        run = session.get(Run, rid)
        output = json.loads(run.state)
        if run.status in {"retry_queued", "needs_attention"} and run.error:
            raise RuntimeError(run.error)
    verification = output.get("verification", {})
    return {
        "run_id": rid,
        "status": run.status,
        "decision": output.get("decision", {}).get("action"),
        "cover_letter": output.get("draft", {}).get("cover_letter", ""),
        "unsupported_before": verification.get("unsupported_before", 0),
        "unsupported_after": verify(
            output.get("draft", {}).get("cover_letter", ""), output.get("evidence", [])
        )["unsupported_before"],
        "policy_violations": len(output.get("compliance", {}).get("violations", [])),
        "tokens": sum(u["input_tokens"] + u["output_tokens"] for u in output.get("usage", [])),
        "usd_estimate": sum(u["usd_estimate"] for u in output.get("usage", [])),
        "usage": output.get("usage", []),
        "fit": output.get("fit", {}),
        "risk": output.get("risk", {}),
        "verification": verification,
        "evidence": output.get("evidence", []),
    }


async def main(limit, architectures):
    settings().mcp_transport = "memory"
    source = json.loads((ROOT / "evals/datasets/synthetic_dev.json").read_text())
    queries = [q for q in source if q["split"] == "development"][:limit]
    with db() as session:
        tenant = session.query(User).filter(User.email.notlike("%@test.local")).first().id
    rows = []
    raw_path = ROOT / "evaluation/raw/orchestration-progress.jsonl"
    for architecture in architectures:
        for i, query in enumerate(queries):
            started = time.perf_counter()
            try:
                result = (
                    await handwritten(
                        query, tenant, "open_alt" if architecture == "handwritten_alt" else "open"
                    )
                    if architecture.startswith("handwritten")
                    else await baseline(query, tenant, architecture)
                )
                row = {
                    "architecture": architecture,
                    "id": query["id"],
                    "persona": query["persona"],
                    "job_type": query["job_type"],
                    "gold_action": query["gold_action"],
                    "latency_seconds": time.perf_counter() - started,
                    "error": None,
                    "matching_strategy": settings().match_query_mode,
                    **result,
                }
            except Exception as exc:
                row = {
                    "architecture": architecture,
                    "id": query["id"],
                    "gold_action": query["gold_action"],
                    "error": type(exc).__name__ + ": " + str(exc)[:300],
                    "matching_strategy": settings().match_query_mode,
                    "latency_seconds": time.perf_counter() - started,
                }
            rows.append(row)
            with raw_path.open("a", encoding="utf-8") as output:
                output.write(json.dumps(row) + "\n")
            print(architecture, i + 1, "/", len(queries), row.get("decision", row["error"]), flush=True)
            await asyncio.sleep(1)
    import numpy as np

    results = []
    for architecture in architectures:
        group = [r for r in rows if r["architecture"] == architecture]
        good = [r for r in group if not r["error"]]
        results.append(
            {
                "architecture": architecture,
                "attempted": len(group),
                "completed": len(good),
                "failed": len(group) - len(good),
                "decision_accuracy": sum(
                    (r.get("decision") == "bid") == (r["gold_action"] == "bid") for r in good
                )
                / max(1, len(good)),
                "unsupported_before_per_draft": sum(r.get("unsupported_before", 0) for r in good)
                / max(1, len(good)),
                "unsupported_after_per_draft": sum(r.get("unsupported_after", 0) for r in good)
                / max(1, len(good)),
                "policy_violations": sum(r.get("policy_violations", 0) for r in good),
                "mean_tokens": float(np.mean([r["tokens"] for r in good])) if good else None,
                "p50_seconds": float(np.percentile([r["latency_seconds"] for r in group], 50)),
                "p95_seconds": float(np.percentile([r["latency_seconds"] for r in group], 95)),
                "usd_estimate": sum(r.get("usd_estimate", 0) for r in good),
                "reply_rate": None,
                "hire_rate": None,
            }
        )
    save(
        "orchestration",
        rows,
        {
            "provenance": "synthetic_jobs_actual_Groq_inference",
            "n_per_architecture": len(queries),
            "results": results,
            "limitations": "No instructor GigSim service; reply/hire rates unavailable. Common conservative post-verifier used for all designs; raw unsupported claims reported separately. Latency includes tool transport and model retries. Failed attempts are reported, not scored as successful.",
        },
    )
    # Canonical reporting retains failed attempts and uses actual draft denominators.
    from evaluation.summarize import main as summarize

    summarize()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument(
        "--match-query-mode",
        choices=["legacy", "whole_job"],
        default="legacy",
        help="legacy reproduces the recorded historical architecture study",
    )
    parser.add_argument(
        "--architectures",
        nargs="+",
        choices=["react", "supervisor", "handwritten", "handwritten_alt"],
        default=["react", "supervisor", "handwritten", "handwritten_alt"],
    )
    args = parser.parse_args()
    settings().match_query_mode = args.match_query_mode
    asyncio.run(main(args.limit, args.architectures))
