"""Recompute published tables from immutable raw observations; retain failed attempts."""

import json
from datetime import datetime

import numpy as np

from gigbid_core.config import ROOT, policy
from gigbid_core.db import Event, Run, db


def main():
    path = ROOT / "evaluation/raw/orchestration.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def cost(row):
        if "usd_estimate" in row:
            return row["usd_estimate"]
        # Earlier baseline rows preserved tokens but predate the cost field.
        # Derive list-price estimates from those observations, never substitute zero.
        usages = row.get("usage", [])
        if not usages:
            return None
        total = 0.0
        for usage in usages:
            model = usage.get("model", row.get("model"))
            prices = policy()["models"]["pricing"].get(model)
            if "usd_estimate" in usage:
                total += usage["usd_estimate"]
            elif prices:
                total += (
                    usage.get("input_tokens", 0) * prices[0] + usage.get("output_tokens", 0) * prices[1]
                ) / 1_000_000
            else:
                return None
        return total

    results = []
    for architecture in dict.fromkeys(row["architecture"] for row in rows):
        group = [r for r in rows if r["architecture"] == architecture]
        valid = [r for r in group if not r.get("error") and r.get("decision") in {"bid", "skip", "watch"}]
        drafts = [r for r in valid if r.get("cover_letter", "").strip()]
        correct = sum((r["decision"] == "bid") == (r["gold_action"] == "bid") for r in valid)
        analysis = []
        for row in valid:
            if row.get("run_id"):
                with db() as session:
                    run = session.get(Run, row["run_id"])
                    event = session.query(Event).filter_by(run_id=row["run_id"], node="decide").first()
                    if run and event:
                        analysis.append(
                            (
                                datetime.fromisoformat(event.created) - datetime.fromisoformat(run.created)
                            ).total_seconds()
                        )
        results.append(
            {
                "architecture": architecture,
                "attempted": len(group),
                "completed": len(valid),
                "failed": len(group) - len(valid),
                "drafts": len(drafts),
                "decision_accuracy": correct / max(1, len(group)),
                "accuracy_on_completed": correct / max(1, len(valid)),
                "unsupported_before_per_draft": sum(r.get("unsupported_before", 0) for r in drafts)
                / len(drafts)
                if drafts
                else None,
                "unsupported_after_per_draft": sum(r.get("unsupported_after", 0) for r in drafts)
                / len(drafts)
                if drafts
                else None,
                "policy_violations": sum(r.get("policy_violations", 0) for r in valid),
                "mean_tokens": float(np.mean([r["tokens"] for r in valid])) if valid else None,
                "p50_seconds": float(np.percentile([r["latency_seconds"] for r in group], 50)),
                "p95_seconds": float(np.percentile([r["latency_seconds"] for r in group], 95)),
                "completed_p95_seconds": float(np.percentile([r["latency_seconds"] for r in valid], 95))
                if valid
                else None,
                "analysis_p95_seconds": float(np.percentile(analysis, 95)) if analysis else None,
                "proposal_p95_seconds": float(np.percentile([r["latency_seconds"] for r in drafts], 95))
                if drafts
                else None,
                "usd_estimate": sum(cost(r) for r in valid if cost(r) is not None),
                "mean_usd_per_completed_job": float(np.mean([cost(r) for r in valid if cost(r) is not None]))
                if any(cost(r) is not None for r in valid)
                else None,
                "mean_usd_per_draft": float(np.mean([cost(r) for r in drafts if cost(r) is not None]))
                if any(cost(r) is not None for r in drafts)
                else None,
                "cost_basis": "Returned input/output token usage times configured public list prices; no invoice or failed-call estimate",
                "completion_errors": {
                    kind: sum(str(r.get("error", "")).split(":")[0] == kind for r in group)
                    for kind in sorted({str(r["error"]).split(":")[0] for r in group if r.get("error")})
                },
                "failed_call_usage": "unknown when provider did not return usage",
                "reply_rate": None,
                "hire_rate": None,
            }
        )
    summary = {
        "provenance": "synthetic_jobs_actual_Groq_inference",
        "n_per_architecture": max(r["attempted"] for r in results),
        "matching_strategy": sorted({r.get("matching_strategy", "legacy") for r in rows}),
        "deployment_repair": "whole-job query aligned to retrieval evaluation; separately validated after failure analysis",
        "accuracy_denominator": "All attempted jobs; failed/invalid outputs count as incorrect. Accuracy on completed also reported. Claim denominators include actual nonempty drafts only.",
        "results": results,
        "limitations": "Instructor GigSim reply/hire unavailable. Rate-limit delays retained. Sequential architecture groups encounter unequal daily token availability; inspect completion_errors alongside every score. This is a quota-constrained operational study, not a fair architecture ranking. No independent human judge scores. Provider errors can hide partial token usage. Recorded legacy rows predate whole-job-query and approval freshness changes; the shipped runner also includes subsequent reliability fixes.",
    }
    (ROOT / "evals/results/orchestration.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("Recomputed orchestration summaries from raw rows with explicit failure/draft denominators.")


if __name__ == "__main__":
    main()
