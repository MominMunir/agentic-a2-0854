"""One free web service, separate supervised API and Redis-worker processes."""

import os
import signal
import subprocess
import sys
import time


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
        EMBEDDING_BATCH_SIZE="2",
        EMBEDDING_THREADS="1",
        EMBEDDING_LOW_MEMORY="true",
    )
    for server in ["PORTFOLIO", "MARKETPLACE", "WORKSPACE"]:
        os.environ[f"{server}_MCP_URL"] = f"http://127.0.0.1:{port}/{server.lower()}/mcp"
    subprocess.run([sys.executable, "scripts/seed.py"], check=True)
    children = [
        subprocess.Popen(
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
            ]
        ),
        subprocess.Popen([sys.executable, "-m", "arq", "worker.main.WorkerSettings"]),
    ]
    stopped = False
    failed = False

    def stop(*args):
        nonlocal stopped
        stopped = True
        for child in children:
            if child.poll() is None:
                child.terminate()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        while not stopped:
            if any(child.poll() is not None for child in children):
                failed = True
                stop()
                break
            time.sleep(1)
    finally:
        stop()
        for child in children:
            try:
                child.wait(timeout=20)
            except subprocess.TimeoutExpired:
                child.kill()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
