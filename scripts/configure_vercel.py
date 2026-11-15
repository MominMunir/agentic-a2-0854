import argparse
import json
from urllib.parse import urlparse

from gigbid_core.config import ROOT

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend-url", required=True)
    args = parser.parse_args()
    parsed = urlparse(args.backend_url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
    ):
        raise SystemExit("Provide the public HTTPS backend origin, without credentials or a path.")
    target = args.backend_url.rstrip("/")
    config = {
        "buildCommand": "npm run build",
        "outputDirectory": "dist",
        "framework": "vite",
        "rewrites": [
            {"source": "/api/:path*", "destination": target + "/api/:path*"},
            {"source": "/:path*", "destination": "/index.html"},
        ],
    }
    (ROOT / "apps/web/vercel.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(
        "Vercel same-origin API proxy configured for the supplied backend. Set backend APP_URL to the Vercel frontend origin."
    )
