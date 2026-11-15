import csv
import hashlib
import io
import json
import re
import zipfile

from gigbid_core.config import ROOT
from gigbid_core.security import redact

SKILLS = [
    "Python",
    "scikit-learn",
    "classification",
    "PyTorch",
    "RAG",
    "FastAPI",
    "TypeScript",
    "React",
    "PostgreSQL",
    "Node.js",
    "Docker",
    "SQL",
    "pandas",
    "dbt",
    "Power BI",
    "statistics",
]


def number(value):
    try:
        return float(re.sub(r"[^\d.]", "", str(value or "")))
    except ValueError:
        return 0.0


def main():
    jobs, fingerprints, manifest = [], set(), []
    for archive in sorted((ROOT / "data/raw/kaggle").glob("*/dataset.zip")):
        dataset = archive.parent.name.replace("__", "/")
        metadata = json.loads((archive.parent / "metadata.json").read_text(encoding="utf-8"))
        kept, total, duplicates, filtered = 0, 0, 0, 0
        with zipfile.ZipFile(archive) as bundle:
            filename = next(name for name in bundle.namelist() if name.endswith(".csv"))
            reader = csv.DictReader(
                io.TextIOWrapper(bundle.open(filename), encoding="utf-8-sig", errors="replace")
            )
            for row in reader:
                total += 1
                title = (row.get("title") or row.get("Job Title") or "").strip()
                description = (row.get("description") or row.get("Description") or "").strip()
                if not title or len(description) < 50:
                    filtered += 1
                    continue
                text = title + " " + description
                skills = [
                    skill
                    for skill in SKILLS
                    if re.search(r"(?<!\w)" + re.escape(skill) + r"(?!\w)", text, re.I)
                ]
                if not skills:
                    filtered += 1
                    continue
                digest = hashlib.sha256(re.sub(r"\s+", " ", text.lower()).encode()).hexdigest()
                if digest in fingerprints:
                    duplicates += 1
                    continue
                fingerprints.add(digest)
                # Preserve genuine type: hourly ranges are never misrepresented as fixed budgets.
                hourly = (
                    str(row.get("is_hourly", "")).lower() == "true"
                    or "hour" in str(row.get("Payment_type", "")).lower()
                )
                lo = number(row.get("hourly_low") or row.get("Start_rate"))
                hi = number(row.get("hourly_high") or row.get("End_rate"))
                fixed = number(row.get("budget") or row.get("Job_Cost"))
                if hourly or fixed <= 0:
                    filtered += 1
                    continue
                if kept >= 500:
                    continue
                cleaned_title, cleaned_description = redact(title), redact(description)
                jobs.append(
                    {
                        "id": "kaggle-" + digest[:20],
                        "title": cleaned_title,
                        "description": cleaned_description[:15000],
                        "required_skills": skills,
                        "budget_min": fixed,
                        "budget_max": fixed,
                        "budget_type": "fixed",
                        "source_hourly_low": lo or None,
                        "source_hourly_high": hi or None,
                        "duration_days": 14,
                        "duration_estimated": True,
                        "screening_questions": [],
                        "connects_cost": 8,
                        "connects_estimated": True,
                        "client_id": "unknown-" + digest[:16],
                        "category": "unclassified",
                        "industry": "unspecified",
                        "provenance": "kaggle",
                        "synthetic": False,
                        "dataset": dataset,
                        "source_row": total,
                        "source_url": row.get("link") or row.get("Job_URL"),
                        "source_date": row.get("published_date"),
                        "license": metadata.get("licenseName"),
                        "limitations": "Historical snapshot; client history unavailable; duration and Connects are application assumptions, not dataset facts.",
                    }
                )
                kept += 1
        manifest.append(
            {
                "dataset": dataset,
                "url": "https://www.kaggle.com/datasets/" + dataset,
                "license": metadata.get("licenseName"),
                "rows_scanned": total,
                "kept": kept,
                "duplicates_seen": duplicates,
                "filtered": filtered,
                "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            }
        )
    folder = ROOT / "data/processed/real"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "jobs.json").write_text(json.dumps(jobs, indent=2), encoding="utf-8")
    (ROOT / "data/real_manifest.json").write_text(
        json.dumps(
            {
                "datasets": manifest,
                "total_jobs": len(jobs),
                "redistribution": "Raw data excluded from release. Fetch and reproduce locally; licenses and attribution retained.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"normalized_real_jobs": len(jobs), "datasets": manifest}, indent=2))


if __name__ == "__main__":
    main()
