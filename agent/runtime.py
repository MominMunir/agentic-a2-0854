import asyncio
import json
from contextlib import asynccontextmanager
from time import perf_counter

from langgraph.types import Command

from agent.graphs.bid_graph import build_graph as bid_graph
from agent.graphs.conversation_graph import build_graph as conversation_graph
from agent.memory.store import store
from gigbid_core.config import ROOT, settings
from gigbid_core.db import Event, Run, db, get, now
from gigbid_core.security import redact


@asynccontextmanager
async def graph_context(kind="bid"):
    url = settings().checkpoint_url
    if url.startswith("postgres"):
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

        async with AsyncPostgresSaver.from_conn_string(url) as saver:
            await saver.setup()
            yield (conversation_graph if kind == "conversation" else bid_graph)(saver, store)
    else:
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

        path = str(ROOT / url.removeprefix("sqlite:///"))
        async with AsyncSqliteSaver.from_conn_string(path) as saver:
            yield (conversation_graph if kind == "conversation" else bid_graph)(saver, store)


def public_state(state):
    # Approval capability belongs only in the durable checkpoint, never the UI/trace.
    result = {k: v for k, v in state.items() if k != "__interrupt__"}
    if "approval" in result:
        result["approval"] = {k: v for k, v in result["approval"].items() if k != "approval_token"}
    return result


async def process_run(run_id):
    from gigbid_core.tracing import span

    with span("gigbid.run", run_id=run_id):
        return await _process_run(run_id)


async def _process_run(run_id):
    with db() as session:
        run = session.get(Run, run_id)
        if not run or run.status not in {"queued", "running", "retry_queued"}:
            return
        user, kind = run.tenant, run.kind
        initial = json.loads(run.state)
        resume = get(session, user, "resume", run_id)
        run.status, run.updated = "running", now()
    config = {"configurable": {"thread_id": user + ":" + run_id}, "recursion_limit": 40}
    started = perf_counter()
    try:
        async with graph_context(kind) as graph:
            checkpoint = await graph.aget_state(config)
            argument = (
                Command(resume=resume)
                if resume and checkpoint.interrupts
                else None
                if checkpoint.values
                else initial
            )
            async for updates in graph.astream(argument, config=config, stream_mode="updates"):
                with db() as session:
                    for node, payload in updates.items():
                        if node != "__interrupt__":
                            session.add(
                                Event(
                                    tenant=user,
                                    run_id=run_id,
                                    node=node,
                                    payload=redact(
                                        {
                                            "status": "completed",
                                            "usage": payload.get("usage", [])
                                            if isinstance(payload, dict)
                                            else [],
                                        }
                                    ),
                                )
                            )
            snapshot = await graph.aget_state(config)
            state = public_state(snapshot.values)
            state["elapsed_seconds"] = perf_counter() - started
            pending = bool(snapshot.interrupts)
            with db() as session:
                run = session.get(Run, run_id)
                run.state = json.dumps(state)
                run.status = "awaiting_approval" if pending else state.get("status", "completed")
                run.updated = now()
                session.add(
                    Event(
                        tenant=user,
                        run_id=run_id,
                        node="run",
                        payload=json.dumps(
                            {"status": run.status, "elapsed_seconds": state["elapsed_seconds"]}
                        ),
                    )
                )
    except Exception as exc:
        from agent.models import ModelUnavailable

        retry = (
            isinstance(exc, (ConnectionError, TimeoutError, OSError, ModelUnavailable))
            or "unavailable" in str(exc).lower()
        )
        with db() as session:
            run = session.get(Run, run_id)
            run.status = "retry_queued" if retry else "needs_attention"
            run.error = redact(str(exc))[:1000]
            run.updated = now()
            session.add(
                Event(
                    tenant=user,
                    run_id=run_id,
                    node="error",
                    payload=json.dumps({"status": run.status, "reason": run.error}),
                )
            )
        if not retry:
            raise


async def enqueue(run_id):
    if settings().executor == "redis":
        from arq import create_pool
        from arq.connections import RedisSettings

        pool = await create_pool(RedisSettings.from_dsn(settings().redis_url))
        await pool.enqueue_job("run_graph", run_id, _job_id=run_id + ":" + now())
        await pool.aclose()


async def local_worker():
    while True:
        with db() as session:
            queued = [
                (r.id, r.updated)
                for r in session.query(Run).filter(Run.status.in_(["queued", "retry_queued"])).all()
            ]
        for run_id, updated in queued:
            try:
                await process_run(run_id)
            except Exception:
                pass  # Persisted needs_attention state remains visible in the UI.
        await asyncio.sleep(5)
