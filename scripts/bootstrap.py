"""Create ignored secrets, never emit credentials to logs or source files."""

import base64
import os
from pathlib import Path
import secrets

ROOT = Path(__file__).resolve().parents[1]


def main():
    for directory in [
        ".private",
        "data/runtime",
        "data/raw/kaggle",
        "data/processed/real",
        "data/synthetic",
        "data/personas",
        "data/policy_pack",
        "gigsim",
        "evaluation/raw",
        "evals/results",
        "docs/images",
    ]:
        (ROOT / directory).mkdir(parents=True, exist_ok=True)
    env = ROOT / ".env"
    if not env.exists():
        email = os.environ.get("REVIEWER_EMAIL", "reviewer@gigbid.local")
        password = os.environ.get("REVIEWER_PASSWORD", secrets.token_urlsafe(22))
        values = (ROOT / ".env.example").read_text()
        replacements = {
            "APP_SECRET_KEY=": secrets.token_urlsafe(48),
            "TOKEN_ENCRYPTION_KEY=": base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
            "REVIEWER_EMAIL=": email,
            "REVIEWER_PASSWORD=": password,
            "POSTGRES_PASSWORD=": secrets.token_urlsafe(32),
            "GIGSIM_API_TOKEN=": secrets.token_urlsafe(32),
            "INFERENCE_MODE=ollama": "groq",
            "OPEN_MODEL_BASE_URL=": "https://api.groq.com/openai/v1",
        }
        for key, value in replacements.items():
            values = values.replace(key + "\n", key.split("=")[0] + "=" + value + "\n")
        env.write_text(values, encoding="utf-8")
        (ROOT / ".private/reviewer.txt").write_text(
            f"Email: {email}\nPassword: {password}\nLocal web: http://localhost:5173\n", encoding="utf-8"
        )
    packages = [
        "gigbid_core",
        "agent",
        "agent/graphs",
        "agent/nodes",
        "agent/memory",
        "apps",
        "apps/api",
        "apps/api/routers",
        "apps/api/auth",
        "apps/api/schemas",
        "rag",
        "rag/ingest",
        "rag/index",
        "rag/variants",
        "mcp_servers",
        "mcp_servers/portfolio",
        "mcp_servers/marketplace",
        "mcp_servers/marketplace/adapters",
        "mcp_servers/workspace",
        "worker",
        "simulator",
        "evaluation",
        "evals",
        "evals/runners",
    ]
    for package in packages:
        (ROOT / package).mkdir(parents=True, exist_ok=True)
        (ROOT / package / "__init__.py").touch(exist_ok=True)
    print("Private local configuration prepared. Add OPEN_MODEL_API_KEY to .env; secrets were not printed.")


if __name__ == "__main__":
    main()
