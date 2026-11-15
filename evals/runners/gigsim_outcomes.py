"""Score an instructor GigSim outcome export without contacting a marketplace.

Expected export: {"source":"instructor_gigsim", "jobs":[{"id":..., "submitted":
true, "replied":false, "hired":false}, ...]}. API mapping must be confirmed
against the instructor's supplied package before collecting this export.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from gigbid_core.config import ROOT


def summarize(data):
    if data.get("source") != "instructor_gigsim":
        raise ValueError("Instructor outcome metrics require an explicitly identified instructor export")
    rows = data["jobs"]
    if not rows or len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Provide nonempty, unique job observations")
    for row in rows:
        if any(type(row.get(k)) is not bool for k in ["submitted", "replied", "hired"]):
            raise ValueError("Outcome flags must be explicit booleans")
        if (row["replied"] or row["hired"]) and not row["submitted"]:
            raise ValueError("Replies and hires require a submitted proposal")
        if row["hired"] and not row["replied"]:
            raise ValueError("Hired outcomes must include a reply")
    submitted = sum(r["submitted"] for r in rows)
    if not submitted:
        raise ValueError("No submitted proposals; reply/hire rates are undefined")
    return dict(
        status="completed", source="instructor_gigsim", jobs=len(rows), submitted=submitted,
        replied=sum(r["replied"] for r in rows), hired=sum(r["hired"] for r in rows),
        reply_rate=sum(r["replied"] for r in rows)/submitted,
        hire_rate=sum(r["hired"] for r in rows)/submitted,
        denominator="submitted proposals",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path)
    args = parser.parse_args()
    path = args.input or (Path(os.environ["GIGSIM_OUTCOMES_FILE"]) if os.getenv("GIGSIM_OUTCOMES_FILE") else None)
    if path:
        content = path.read_bytes()
        result = {**summarize(json.loads(content)), "input_sha256": hashlib.sha256(content).hexdigest()}
    else:
        result = dict(status="not_conducted", reason="Instructor GigSim package and outcome export were not supplied")
    (ROOT / "evals/results/gigsim_outcomes.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
