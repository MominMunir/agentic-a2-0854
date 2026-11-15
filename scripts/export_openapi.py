import json
from gigbid_core.config import ROOT
from apps.api.main import app

if __name__ == "__main__":
    (ROOT / "docs/openapi.json").write_text(json.dumps(app.openapi(), indent=2), encoding="utf-8")
    print("OpenAPI schema exported; generate TypeScript via npm run api:generate.")
