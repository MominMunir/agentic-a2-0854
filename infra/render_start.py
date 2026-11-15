"""One free web service with a Redis worker sharing the API process."""

import os
import subprocess
import sys


def main():
    port = int(os.getenv("PORT", "10000"))
    os.environ["APP_URL"] = os.getenv("APP_URL") or os.getenv(
        "RENDER_EXTERNAL_URL", f"http://localhost:{port}"
    )
    os.environ["UPWORK_REDIRECT_URI"] = (
        os.getenv("UPWORK_REDIRECT_URI") or os.environ["APP_URL"] + "/api/accounts/upwork/callback"
    )
    os.environ.update(
        MOUNT_MCP_SERVERS="true",
        SERVE_FRONTEND="true",
        EXECUTOR="redis",
        MCP_TRANSPORT="http",
        WORKER_CONCURRENCY="1",
        EMBEDDED_WORKER="true",
        EMBEDDING_BATCH_SIZE="2",
        EMBEDDING_THREADS="1",
        EMBEDDING_LOW_MEMORY="true",
    )
    for server in ["PORTFOLIO", "MARKETPLACE", "WORKSPACE"]:
        os.environ[f"{server}_MCP_URL"] = f"http://127.0.0.1:{port}/{server.lower()}/mcp"
    subprocess.run([sys.executable, "scripts/seed.py"], check=True)
    os.execv(
        sys.executable,
        [
            sys.executable,
            "-m",
            "uvicorn",
            "apps.api.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(port),
            "--proxy-headers",
        ],
    )


if __name__ == "__main__":
    raise SystemExit(main())
