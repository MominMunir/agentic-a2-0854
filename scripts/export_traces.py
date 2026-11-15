import json
import sqlite3

from gigbid_core.config import ROOT
from gigbid_core.security import redact
from apps.api.streaming import parse_event


def scrub(value):
    if isinstance(value, dict):
        return {
            key: scrub(item)
            for key, item in value.items()
            if key
            not in {
                "approval_token",
                "password",
                "password_hash",
                "access_token",
                "refresh_token",
                "encrypted",
                "app_secret_key",
                "token_encryption_key",
            }
        }
    if isinstance(value, list):
        return [scrub(item) for item in value]
    return value


def main():
    output = ROOT / "docs/traces"
    output.mkdir(exist_ok=True)
    selected = {}
    for source in ["tmp/tests/test.db", "tmp/e2e.db", "data/runtime/gigbid.db"]:
        path = ROOT / source
        if not path.exists():
            continue
        with sqlite3.connect(path) as connection:
            connection.row_factory = sqlite3.Row
            for run in connection.execute("select * from runs order by created desc"):
                state = json.loads(run["state"])
                label = (
                    "scam-skip"
                    if state.get("risk", {}).get("injection_detected") and run["status"] == "skip"
                    else "approved-proposal"
                    if run["status"] == "submitted"
                    else "critic-loop"
                    if state.get("revision", 0) > 0
                    else None
                )
                if not label or label in selected:
                    continue
                events = [
                    {**dict(row), "payload": parse_event(row["payload"])}
                    for row in connection.execute(
                        "select * from events where run_id=? order by id", (run["id"],)
                    )
                ]
                audit = [
                    {**dict(row), "payload": parse_event(row["payload"])}
                    for row in connection.execute(
                        "select * from audit where trace_id=? order by id", (run["id"],)
                    )
                ]
                document = scrub(
                    {
                        "trace_id": run["id"],
                        "status": run["status"],
                        "synthetic": True,
                        "execution_mode": "deterministic smoke with hash embeddings"
                        if source.startswith("tmp/")
                        else "configured open models; inspect per-node usage",
                        "source": "actual local workflow; secrets removed and PII masked for publication",
                        "state": state,
                        "events": events,
                        "tool_audit": audit,
                    }
                )
                encoded = json.dumps(json.loads(redact(document)), indent=2)
                (output / (label + ".json")).write_text(encoded, encoding="utf-8")
                selected[label] = run["id"]
    deployment = ROOT / "evals/results/deployment_smoke.json"
    if deployment.exists():
        (output / "postgres-restart.json").write_text(
            deployment.read_text(encoding="utf-8"), encoding="utf-8"
        )
    (output / "README.md").write_text(
        "# Measured synthetic traces\n\nThese are actual saved workflow observations, scrubbed for publication.\nThey are static artifacts, not claims that a public hosted tracing service exists.\n\n- [Scam and injection skip](scam-skip.json)\n- [Approved proposal and exactly-once local effect](approved-proposal.json)\n- [Bounded Critic loop](critic-loop.json)\n- [Actual Postgres/API restart check](postgres-restart.json)\n",
        encoding="utf-8",
    )
    print("Exported scrubbed trace artifacts:", ", ".join(selected))


if __name__ == "__main__":
    main()
