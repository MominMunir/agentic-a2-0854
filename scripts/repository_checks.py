"""Secret and source integrity gate over releaseable source, not private runtime data."""

import re
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {
    ".git",
    ".cache",
    ".venv",
    ".private",
    "node_modules",
    "dist",
    "tmp",
    "playwright-report",
    "test-results",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
}


def source_files():
    for directory, dirs, files in os.walk(ROOT):
        relative = Path(directory).relative_to(ROOT)
        dirs[:] = [
            d
            for d in dirs
            if d not in EXCLUDED
            and not (relative == Path("data") and d in {"raw", "runtime", "processed", "uploads"})
        ]
        for filename in files:
            path = Path(directory) / filename
            if (not filename.startswith(".env") or filename == ".env.example") and path.suffix not in {
                ".pyc",
                ".db",
                ".sqlite",
                ".log",
            }:
                yield path


def main():
    suspicious = []
    patterns = [
        r"gsk_[A-Za-z0-9]{25,}",
        r"gh[pousr]_[A-Za-z0-9]{25,}",
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        r"AKIA[0-9A-Z]{16}",
    ]
    for path in source_files():
        if path.stat().st_size > 10_000_000 or path.suffix in {
            ".pdf",
            ".png",
            ".gif",
            ".zip",
            ".woff2",
            ".jpg",
        }:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(re.search(pattern, text) for pattern in patterns):
            suspicious.append(str(path.relative_to(ROOT)))
    if suspicious:
        raise SystemExit("Potential credentials in release source: " + ", ".join(suspicious))
    for path in (ROOT / "gigsim").rglob("*"):
        if path.is_file() and path.name != "README.md":
            raise SystemExit("Instructor directory changed: verify its immutable baseline before release")
    print("Release-source secret and instructor-directory integrity checks passed.")


if __name__ == "__main__":
    main()
