import argparse
import asyncio
import json

from agent.mcp_client import Tools
from agent.runtime import process_run
from gigbid_core.config import settings
from gigbid_core.db import Run, User, db, uid


async def main(live):
    settings().mcp_transport = "memory"
    if not live:
        settings().inference_mode = "smoke"
        settings().embedding_backend = "hash_smoke"
    with db() as session:
        user = session.query(User).first()
        tenant, profile = user.id, json.loads(user.profile)
    job = await Tools(tenant, "scout").call("get_job", job_id="syn-job-001")
    rid = uid()
    with db() as session:
        session.add(
            Run(
                id=rid,
                tenant=tenant,
                job_id=job["id"],
                state=json.dumps(
                    {
                        "tenant": tenant,
                        "run_id": rid,
                        "job": job,
                        "profile": profile,
                        "usage": [],
                        "steps": 0,
                        "revision": 0,
                    }
                ),
            )
        )
    await process_run(rid)
    with db() as session:
        run = session.get(Run, rid)
        state = json.loads(run.state)
        print(
            json.dumps(
                {
                    "run_id": rid,
                    "status": run.status,
                    "error": run.error,
                    "decision": state.get("decision"),
                    "critique": state.get("critique"),
                    "draft": state.get("draft"),
                    "usage": state.get("usage"),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    asyncio.run(main(parser.parse_args().live))
