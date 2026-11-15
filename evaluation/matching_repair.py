import asyncio
import json
import time

from agent.nodes.analysis import fit_matcher
from evaluation.run import save
from gigbid_core.config import ROOT, settings
from gigbid_core.db import User, db


async def main():
    settings().mcp_transport = "memory"
    source = json.loads((ROOT / "evals/datasets/synthetic_dev.json").read_text())
    jobs = [q for q in source if q["split"] == "development"][:50]
    with db() as session:
        user = session.query(User).first().id
    rows = []
    for mode in ["requirements", "whole_job"]:
        settings().match_query_mode = mode
        for query in jobs:
            state = {
                "tenant": user,
                "run_id": "matching-repair",
                "job": query["job"],
                "profile": {"persona": query["persona"]},
            }
            started = time.perf_counter()
            result = await fit_matcher(state)
            expected = query["job_type"] != "mismatch"
            predicted = result["fit"]["score"] >= 0.55
            rows.append(
                {
                    "mode": mode,
                    "id": query["id"],
                    "expected_skill_fit": expected,
                    "predicted_skill_fit": predicted,
                    "correct": expected == predicted,
                    "score": result["fit"]["score"],
                    "latency_seconds": time.perf_counter() - started,
                    "evidence_ids": result["fit"]["evidence_ids"],
                }
            )
    summary = {
        "provenance": "synthetic_dev_actual_open_embeddings_and_MCP",
        "scope": "Fit-only controlled query-alignment repair; risk and model generation excluded",
        "results": [
            {
                "mode": mode,
                "n": sum(r["mode"] == mode for r in rows),
                "accuracy": sum(r["mode"] == mode and r["correct"] for r in rows)
                / sum(r["mode"] == mode for r in rows),
            }
            for mode in ["requirements", "whole_job"]
        ],
    }
    save("matching_repair", rows, summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
