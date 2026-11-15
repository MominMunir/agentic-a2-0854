"""Copy actual run logs into release evidence, removing credentials/account IDs."""

import json
import re
import shutil

from gigbid_core.config import ROOT


def sanitize(value):
    value = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", value)
    value = re.sub(r"org_[A-Za-z0-9]+", "[PROVIDER_ORGANIZATION]", value)
    value = re.sub(r"gsk_[A-Za-z0-9]+", "[API_KEY]", value)
    return re.sub(r"(?i)(bearer\s+)[\w.\-]+", r"\1[REDACTED]", value)


def main():
    output = ROOT / "evaluation/logs"
    output.mkdir(parents=True, exist_ok=True)
    for name in [
        "orchestration",
        "retrieval-final",
        "pytest-final",
        "playwright-final",
        "wheel-build",
        "wheel-smoke",
        "compact-smoke",
        "compose-final",
        "uv-sync",
    ]:
        source = ROOT / "tmp" / (name + ".log")
        if source.exists():
            (output / (name + ".txt")).write_text(
                sanitize(source.read_text(encoding="utf-8", errors="replace")), encoding="utf-8"
            )
    raw = ROOT / "evaluation/raw/orchestration.jsonl"
    if raw.exists():
        original = ROOT / ".private/orchestration-before-public-redaction.jsonl"
        if not original.exists():
            shutil.copy2(raw, original)
        rows = [json.loads(line) for line in raw.read_text(encoding="utf-8").splitlines()]
        for row in rows:
            if row.get("error"):
                row["error"] = sanitize(row["error"])
        raw.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    print("Archived actual evaluation logs; removed keys and provider organization identifiers.")


if __name__ == "__main__":
    main()
