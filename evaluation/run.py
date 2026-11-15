import argparse
import hashlib
import json
import platform
import time
from collections import defaultdict

import numpy as np

from evaluation.metrics import classification_metrics, retrieval_metrics
from gigbid_core.config import ROOT, settings


def save(name, rows, summary):
    for folder in ["evaluation/raw", "evals/results"]:
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
    (ROOT / "evaluation/raw" / (name + ".jsonl")).write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )
    (ROOT / "evals/results" / (name + ".json")).write_text(json.dumps(summary, indent=2), encoding="utf-8")


def rag_eval(limit=0):
    from rag.retriever import search

    source = ROOT / "evals/datasets/synthetic_dev.json"
    queries = json.loads(source.read_text())[: limit or None]
    items = json.loads((ROOT / "data/synthetic/evidence.json").read_text())
    rows = []
    for variant in ["v0", "v1", "v2", "v3", "v4", "v8"]:
        for i, q in enumerate(queries):
            start = time.perf_counter()
            found = search(items, q["query"], 10, variant, {"persona": q["persona"]})
            ids = [e["id"] for e in found]
            rows.append(
                {
                    "id": q["id"],
                    "variant": variant,
                    "persona": q["persona"],
                    "split": q["split"],
                    "job_type": q["job_type"],
                    "latency_seconds": time.perf_counter() - start,
                    "found": ids,
                    "gold": q["relevant_ids"],
                    **retrieval_metrics(ids, q["relevant_ids"]),
                }
            )
        print("Evaluated", variant, "on", len(queries), "synthetic queries", flush=True)
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["variant"], row["split"], "all")].append(row)
        grouped[(row["variant"], row["split"], row["persona"])].append(row)
    summaries = []
    for (variant, split, persona), group in grouped.items():
        result = {
            "variant": variant,
            "split": split,
            "persona": persona,
            "n": len(group),
            "p50_seconds": float(np.percentile([r["latency_seconds"] for r in group], 50)),
            "p95_seconds": float(np.percentile([r["latency_seconds"] for r in group], 95)),
        }
        for metric in ["recall_at_5", "mrr", "ndcg_at_10"]:
            values = [r[metric] for r in group if r[metric] is not None]
            result[metric] = float(np.mean(values)) if values else None
        summaries.append(result)
    candidates = [s for s in summaries if s["split"] == "development" and s["persona"] == "all"]
    selected = max(candidates, key=lambda s: (s["recall_at_5"], s["ndcg_at_10"], -s["p95_seconds"]))[
        "variant"
    ]
    summary = {
        "provenance": "synthetic_template_dev_not_instructor",
        "embedding_backend": settings().embedding_backend,
        "embedding_model": "BAAI/bge-small-en-v1.5"
        if settings().embedding_backend != "hash_smoke"
        else "nonsemantic_hash_smoke",
        "reranker": "ms-marco-MiniLM-L-12-v2",
        "python": platform.python_version(),
        "hardware": platform.platform(),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "selection_rule": "Development Recall@5, then nDCG@10, then lower p95; holdout never used for selection",
        "selected_variant": selected,
        "results": summaries,
        "limitations": "Template-derived synthetic relevance. Documents share text across industries; this measures ambiguity and retrieval behavior, not external marketplace success.",
    }
    save("retrieval", rows, summary)
    print("Selected from development split:", selected, flush=True)
    return summary


def decision_eval(limit=0):
    from agent.nodes.analysis import risk_rules
    from rag.verify import verify

    queries = json.loads((ROOT / "evals/datasets/synthetic_dev.json").read_text())[: limit or None]
    personas = {p: json.loads((ROOT / f"data/personas/{p}.json").read_text()) for p in ["ml", "web", "data"]}
    clients = {c["id"]: c for c in json.loads((ROOT / "data/synthetic/clients.json").read_text())}
    rows = []
    for query in queries:
        job = query["job"]
        risk = risk_rules(job, clients[job["client_id"]])
        fit = len(set(job["required_skills"]) & set(personas[query["persona"]]["skills"])) / max(
            len(job["required_skills"]), 1
        )
        action = "bid" if fit >= 0.55 and risk.score < 0.65 else "skip"
        quote = (job["budget_min"] + job["budget_max"]) / 2
        rows.append(
            {
                "id": query["id"],
                "persona": query["persona"],
                "job_type": query["job_type"],
                "gold_bid": query["gold_action"] == "bid",
                "predicted_bid": action == "bid",
                "gold_scam": query["gold_scam"],
                "predicted_scam": "unpaid_or_off_platform_request" in risk.flags,
                "price_in_band": query["fair_price_min"] <= quote <= query["fair_price_max"],
                "gold_injection": query["gold_injection"],
                "injection_blocked": risk.injection_detected,
            }
        )
    attacks = [
        "I built 100 systems.",
        "I guarantee a 100% gain.",
        "Built a Python API. [wrong-id]",
        "I have 15 years of experience.",
        "Contact me at person@example.com.",
    ]
    claim_rows = [{"text": text, **verify(text, [])} for text in attacks]
    summary = {
        "provenance": "synthetic_rule_baseline_not_LLM",
        "n": len(rows),
        "bid": classification_metrics([r["gold_bid"] for r in rows], [r["predicted_bid"] for r in rows]),
        "scam": classification_metrics([r["gold_scam"] for r in rows], [r["predicted_scam"] for r in rows]),
        "price_in_band_rate": sum(r["price_in_band"] for r in rows) / len(rows),
        "injection": {
            "n": sum(r["gold_injection"] for r in rows),
            "defended_rule_attack_success_rate": sum(
                r["gold_injection"] and not r["injection_blocked"] for r in rows
            )
            / max(1, sum(r["gold_injection"] for r in rows)),
            "limitations": "Rule-level blocked-routing metric; not a model prompt-injection benchmark or undefended LLM measurement",
        },
        "claim_challenge": {
            "n": len(attacks),
            "unsupported_before": sum(r["unsupported_before"] for r in claim_rows),
            "unsupported_after": sum(r["unsupported_after"] for r in claim_rows),
        },
        "per_persona": {
            p: classification_metrics(
                [r["gold_bid"] for r in rows if r["persona"] == p],
                [r["predicted_bid"] for r in rows if r["persona"] == p],
            )
            for p in personas
        },
        "pending": [
            "Instructor GigSim reply/hire rates",
            "Independent human panel",
            "30-item human/judge calibration",
            "Hidden test results",
        ],
    }
    save("decisions", rows, summary)
    save("claim_challenge", claim_rows, summary["claim_challenge"])
    print("Decision and claim-challenge metrics saved.", flush=True)
    return summary


def plots():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    summary = json.loads((ROOT / "evals/results/retrieval.json").read_text())
    rows = [r for r in summary["results"] if r["split"] == "holdout" and r["persona"] == "all"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.7))
    axes[0].bar([r["variant"] for r in rows], [r["recall_at_5"] for r in rows], color="#3b7560")
    axes[0].set(ylabel="Evidence Recall@5", title="Synthetic domain holdout", ylim=(0, 1))
    axes[1].bar([r["variant"] for r in rows], [r["ndcg_at_10"] for r in rows], color="#8ba66a")
    axes[1].set(ylabel="nDCG@10", title="Same corpus and queries", ylim=(0, 1))
    fig.suptitle("GigBid open CPU retrieval comparison", fontsize=12)
    fig.tight_layout()
    fig.savefig(ROOT / "evaluation/retrieval_comparison.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=["all", "rag", "decisions", "plots"], default="all")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    if args.suite in {"all", "rag"}:
        rag_eval(args.limit)
    if args.suite in {"all", "decisions"}:
        decision_eval(args.limit)
    if args.suite in {"all", "plots"}:
        plots()
