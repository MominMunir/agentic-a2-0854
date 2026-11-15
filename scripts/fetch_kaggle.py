"""Download only approved datasets; never log authentication values."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
APPROVED = [
    "asaniczka/upwork-job-postings-dataset-2024-50k-records",
    "asaniczka/all-jobs-on-upwork-200k-plus",
    "ahmedmyalo/upwork-freelance-jobs-60k",
    "asaniczka/freelance-contracts-dataset-1-3-million-entries",
    "sarveshchhetri/freelancer-success-earnings-and-churn-prediction",
    "adityammantri/trial-1",
]


def fetch(slug):
    folder = ROOT / "data/raw/kaggle" / slug.replace("/", "__")
    folder.mkdir(parents=True, exist_ok=True)
    config = Path(os.getenv("KAGGLE_CONFIG_DIR") or Path.home() / ".kaggle") / "kaggle.json"
    credentials = json.loads(config.read_text())
    auth = base64.b64encode((credentials["username"] + ":" + credentials["key"]).encode()).decode()
    headers = {"Authorization": "Basic " + auth, "User-Agent": "GigBid-research/1.0"}
    meta_request = Request("https://www.kaggle.com/api/v1/datasets/view/" + slug, headers=headers)
    try:
        with urlopen(meta_request, timeout=60) as response:
            metadata = json.load(response)
        (folder / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        archive = folder / "dataset.zip"
        if not archive.exists():
            request = Request("https://www.kaggle.com/api/v1/datasets/download/" + slug, headers=headers)
            part = folder / "dataset.zip.part"
            with urlopen(request, timeout=120) as response, part.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            part.replace(archive)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        print(
            json.dumps(
                {
                    "dataset": slug,
                    "bytes": archive.stat().st_size,
                    "sha256": digest,
                    "licenses": metadata.get("licenses", metadata.get("licenseName", "review metadata")),
                }
            )
        )
    except HTTPError as exc:
        print(json.dumps({"dataset": slug, "http_status": exc.code, "status": "access_failed"}))
    except Exception as exc:
        print(json.dumps({"dataset": slug, "status": "failed", "error_type": type(exc).__name__}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", action="append", choices=APPROVED)
    args = parser.parse_args()
    for selected in args.dataset or [APPROVED[0], APPROVED[2]]:
        fetch(selected)
