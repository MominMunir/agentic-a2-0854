from arq import cron
from arq.connections import RedisSettings

from agent.runtime import process_run
from gigbid_core.config import settings
from gigbid_core.db import init_db


async def startup(ctx):
    init_db()
    await recover_pending_runs(ctx)


async def run_graph(ctx, run_id):
    from arq import Retry
    from gigbid_core.db import Run, db
    from contextlib import suppress

    lock = ctx["redis"].lock("gigbid:run:" + run_id, timeout=650)
    if not await lock.acquire(blocking=False):
        return
    try:
        await process_run(run_id)
        with db() as session:
            run = session.get(Run, run_id)
            if run.status == "retry_queued":
                if ctx.get("job_try", 1) >= 3:
                    run.status = "needs_attention"
                    run.error = "Dead-lettered after three failed attempts. " + run.error
                else:
                    raise Retry(defer=30)
    finally:
        with suppress(Exception):
            await lock.release()


async def recover_pending_runs(ctx):
    from datetime import datetime, timezone
    from gigbid_core.db import Run, db

    tick = datetime.now(timezone.utc)
    with db() as session:
        pending = [
            r.id
            for r in session.query(Run).filter(Run.status.in_(["queued", "retry_queued", "running"])).all()
            if r.status != "running" or (tick - datetime.fromisoformat(r.updated)).total_seconds() > 650
        ]
    for rid in pending:
        await ctx["redis"].enqueue_job(
            "run_graph", rid, _job_id=f"recover:{rid}:{int(tick.timestamp() // 300)}"
        )


async def scout_saved_searches(ctx):
    import json
    from datetime import datetime, timezone
    from agent.mcp_client import Tools
    from agent.runtime import enqueue
    from gigbid_core.db import Run, User, db, get, now, put, uid
    from gigbid_core.config import policy

    with db() as session:
        users = [(u.id, json.loads(u.profile)) for u in session.query(User).all()]
    for user, profile in users:
        interval = policy()["marketplace"][
            "live_poll_seconds" if settings().marketplace_mode == "upwork" else "simulator_poll_seconds"
        ]
        with db() as session:
            last = get(session, user, "schedule", "scout") or {}
        if (
            last
            and (datetime.now(timezone.utc) - datetime.fromisoformat(last["last"])).total_seconds() < interval
        ):
            continue
        jobs = (
            await Tools(user, "scout").call(
                "search_jobs", query=profile.get("saved_search", "Python"), limit=30
            )
        )["jobs"]
        with db() as session:
            put(session, user, "schedule", "scout", {"last": now()})
            existing = {r.job_id for r in session.query(Run).filter_by(tenant=user, kind="bid").all()}
            new = []
            for job in jobs:
                if job["id"] not in existing:
                    rid = uid()
                    session.add(
                        Run(
                            id=rid,
                            tenant=user,
                            job_id=job["id"],
                            state=json.dumps(
                                {
                                    "tenant": user,
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
                    new.append(rid)
        for rid in new:
            await enqueue(rid)


class WorkerSettings:
    functions = [run_graph]
    cron_jobs = [
        cron(scout_saved_searches, minute={0, 15, 30, 45}, run_at_startup=False),
        cron(recover_pending_runs, minute=set(range(0, 60, 5)), run_at_startup=False),
    ]
    redis_settings = RedisSettings.from_dsn(settings().redis_url)
    on_startup = startup
    max_jobs = settings().worker_concurrency
    job_timeout = 600
    max_tries = 3
