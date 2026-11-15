import asyncio
import json
import time

from agent.agency import route_team
from evaluation.run import save
from gigbid_core.config import ROOT, settings
from gigbid_core.db import User, db


async def main():
    settings().mcp_transport = "memory"
    queries = json.loads((ROOT / "evals/datasets/synthetic_dev.json").read_text())
    with db() as session:
        user = session.query(User).first().id
    rows = []
    for query in queries:
        started = time.perf_counter()
        result = await route_team(user, query["job"])
        expected = None if query["job_type"] == "mismatch" else query["persona"]
        rows.append(
            {
                "id": query["id"],
                "gold": expected,
                "selected": result["selected"],
                "correct": expected == result["selected"],
                "latency_seconds": time.perf_counter() - started,
                "candidates": result["candidates"],
            }
        )
    save(
        "agency",
        rows,
        {
            "provenance": "synthetic_portfolio_actual_open_embeddings",
            "n": len(rows),
            "accuracy": sum(r["correct"] for r in rows) / len(rows),
            "limitations": "This measures skill routing, not hiring outcomes. Risk/compliance still run after routing.",
        },
    )
    print("Agency routing accuracy:", sum(r["correct"] for r in rows) / len(rows))


if __name__ == "__main__":
    asyncio.run(main())
