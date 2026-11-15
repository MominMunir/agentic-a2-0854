"""Prepare blinded human annotation packets and compute only supplied human labels."""

import argparse
import csv
import json
import math
import random

from evaluation.metrics import cohens_kappa
from gigbid_core.config import ROOT


def prepare():
    source = ROOT / "evaluation/raw/orchestration.jsonl"
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
    jobs = {q["id"]: q["job"] for q in json.loads((ROOT / "evals/datasets/synthetic_dev.json").read_text())}
    corpus = {e["id"]: e for e in json.loads((ROOT / "data/synthetic/evidence.json").read_text())}

    def context(row):
        ids = row.get("evidence_ids", []) or [e["id"] for e in row.get("evidence", [])]
        return "\n\n".join(f"[{i}] {corpus[i]['text']}" for i in ids if i in corpus)

    by_job = {}
    for row in rows:
        if row.get("cover_letter"):
            by_job.setdefault(row["id"], {})[row["architecture"]] = row["cover_letter"]
    folder = ROOT / "evaluation/annotations"
    folder.mkdir(parents=True, exist_ok=True)
    # The primary graph exhausted its quota before producing drafts. Use actual
    # available drafts across strategies and preserve the hidden provenance key.
    judge = [r for r in rows if r.get("cover_letter") and not r.get("error")][:30]
    calibration_key = []
    with (folder / "judge_calibration.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["id", "job", "evidence", "proposal", "human_score", "judge_score"]
        )
        writer.writeheader()
        for index, row in enumerate(judge):
            item_id = f"cal-{index:03}"
            writer.writerow(
                {
                    "id": item_id,
                    "job": json.dumps(jobs[row["id"]]),
                    "evidence": context(row),
                    "proposal": row["cover_letter"],
                    "human_score": "",
                    "judge_score": "",
                }
            )
            calibration_key.append({"id": item_id, "job_id": row["id"], "architecture": row["architecture"]})
    (folder / "calibration_key.json").write_text(json.dumps(calibration_key, indent=2), encoding="utf-8")
    rng = random.Random(4016)
    key = []
    with (folder / "blind_pairwise.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["pair_id", "job", "proposal_a", "proposal_b", "rater", "preferred"]
        )
        writer.writeheader()
        for job, variants in by_job.items():
            if "react" in variants and "handwritten_alt" in variants:
                order = ["react", "handwritten_alt"]
                rng.shuffle(order)
                pair = "pair-" + str(len(key))
                writer.writerow(
                    {
                        "pair_id": pair,
                        "job": json.dumps(jobs[job]),
                        "proposal_a": variants[order[0]],
                        "proposal_b": variants[order[1]],
                        "rater": "",
                        "preferred": "",
                    }
                )
                key.append({"pair_id": pair, "a": order[0], "b": order[1], "job_id": job})
    (folder / "pairwise_key.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
    print("Blinded human packets prepared. Blank human fields require real independent labels.")


def calibration(path):
    with open(path, encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    paired = [r for r in rows if r["human_score"] and r["judge_score"]]
    if len(paired) < 30:
        raise ValueError(
            "At least 30 paired, independently supplied human/judge labels are required. Calibration remains pending."
        )
    result = {
        "n": len(paired),
        "cohens_kappa": cohens_kappa([r["human_score"] for r in paired], [r["judge_score"] for r in paired]),
    }
    (ROOT / "evals/results/judge_calibration.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


def pairwise(path):
    with open(path, encoding="utf-8", newline="") as stream:
        rows = [r for r in csv.DictReader(stream) if r["preferred"] in {"a", "b", "tie"} and r["rater"]]
    if not rows:
        raise ValueError("No independent panel ratings supplied")
    key = {
        r["pair_id"]: r for r in json.loads((ROOT / "evaluation/annotations/pairwise_key.json").read_text())
    }
    strategies = sorted({k[s] for k in key.values() for s in ["a", "b"]})
    if len(strategies) != 2 or any(r["pair_id"] not in key for r in rows):
        raise ValueError("Panel rows require the corresponding two-strategy randomization key")
    winners = [key[r["pair_id"]][r["preferred"]] for r in rows if r["preferred"] != "tie"]
    a, b = (winners.count(s) for s in strategies)
    n = a + b
    p = min(1.0, 2 * sum(math.comb(n, k) for k in range(min(a, b) + 1)) / 2**n) if n else 1.0
    result = {
        "n": len(rows),
        "strategy_wins": dict(zip(strategies, [a, b])),
        "ties": len(rows) - n,
        "two_sided_sign_test_p": p,
        "note": "Strategy wins are decoded from the randomized A/B key. Repeated ratings per job are dependent; the simple sign test is descriptive, not a clustered causal estimate.",
    }
    (ROOT / "evals/results/human_panel.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "calibration", "pairwise"])
    parser.add_argument("--input")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "calibration":
        calibration(args.input)
    else:
        pairwise(args.input)
