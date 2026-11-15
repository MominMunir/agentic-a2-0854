import asyncio
import json
import time
from contextlib import asynccontextmanager, suppress, AsyncExitStack

from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from agent.handoffs import ApprovalRequest
from agent.mcp_client import Tools
from agent.memory.promotion_rules import observe_edit, observe_outcome
from agent.memory.store import delete_memory, read_memory
from agent.nodes.drafting import effect_body
from agent.runtime import enqueue, graph_context, local_worker
from apps.api.auth.session import current_user
from apps.api.routers.accounts import router as accounts_router
from apps.api.schemas.models import (
    AuthResponse,
    Credentials,
    DraftEdit,
    JobListResponse,
    OutcomeInput,
    Profile,
    RunResponse,
)
from apps.api.schemas.models import CalendarHold, EmailDraft
from apps.api.schemas.models import ReplayRequest
from apps.api.streaming import event_stream, parse_event
from gigbid_core.config import ROOT, settings
from gigbid_core.db import Event, Run, User, Record, db, get, init_db, now, put, records, uid
from gigbid_core.security import fingerprint, passwords, token
from rag.ingest.loaders import load_upload
from rag.verify import compliance, verify

mounted_mcp = []


@asynccontextmanager
async def lifespan(app):
    settings().require_secrets()
    init_db()
    if settings().executor == "local":
        with db() as session:
            for run in session.query(Run).filter_by(status="running").all():
                run.status = "queued"
    async with AsyncExitStack() as stack:
        for server in mounted_mcp:
            await stack.enter_async_context(server.session_manager.run())
        task = asyncio.create_task(local_worker()) if settings().executor == "local" else None
        queue_worker = None
        if settings().embedded_worker:
            from arq.worker import create_worker
            from worker.main import WorkerSettings

            queue_worker = create_worker(WorkerSettings, handle_signals=False)
            task = asyncio.create_task(queue_worker.async_run())
        app.state.queue_worker_task = task if queue_worker else None
        try:
            yield
        finally:
            if queue_worker:
                await queue_worker.close()
            if task:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task


app = FastAPI(title="GigBid", version="1.0.0", lifespan=lifespan)
if settings().mount_mcp_servers:
    from importlib import import_module
    from gigbid_core.security import MCPAuth

    for name in ["portfolio", "marketplace", "workspace"]:
        server = import_module(f"mcp_servers.{name}.server").mcp
        child = server.streamable_http_app()
        app.mount("/" + name, MCPAuth(child, server_id=name))
        mounted_mcp.append(server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings().app_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)


@app.middleware("http")
async def protect_requests(request, call_next):
    origin = request.headers.get("origin")
    if request.method in {"POST", "PATCH", "DELETE"} and origin and origin != settings().app_url:
        return Response("Request origin rejected", status_code=403)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.exception_handler(ConnectionError)
async def unavailable(request, exc):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        {
            "detail": "Marketplace or model service unavailable. Your work is saved; retry when the connection returns."
        },
        status_code=503,
    )


def auth_result(user):
    return {"id": user.id, "email": user.email, "profile": json.loads(user.profile)}


def set_cookie(response, user):
    response.set_cookie(
        "gigbid_session",
        token(user.id),
        httponly=True,
        secure=settings().app_env == "production",
        samesite="strict",
        max_age=86400,
        path="/",
    )


login_attempts = {}


@app.post("/api/auth/register", response_model=AuthResponse)
async def register(body: Credentials, response: Response):
    with db() as session:
        if session.query(User).filter_by(email=body.email.lower()).first():
            raise HTTPException(409, "Account already exists")
        user = User(
            email=body.email.lower(),
            password_hash=passwords.hash(body.password),
            profile=Profile().model_dump_json(),
        )
        session.add(user)
        session.flush()
        from scripts.seed import seed_tenant

        seed_tenant(session, user)
        result = auth_result(user)
        set_cookie(response, user)
    return result


@app.post("/api/auth/login", response_model=AuthResponse)
async def login(body: Credentials, response: Response, request: Request):
    key = (request.client.host if request.client else "local", body.email.lower(), int(time.time() // 300))
    login_attempts[key] = login_attempts.get(key, 0) + 1
    if login_attempts[key] > 15:
        raise HTTPException(429, "Too many sign-in attempts. Try again in five minutes.")
    with db() as session:
        user = session.query(User).filter_by(email=body.email.lower()).first()
        try:
            if not user or not passwords.verify(user.password_hash, body.password):
                raise ValueError()
        except Exception:
            raise HTTPException(401, "Email or password is incorrect") from None
        set_cookie(response, user)
        return auth_result(user)


@app.post("/api/auth/logout")
async def logout(response: Response):
    response.delete_cookie("gigbid_session", path="/")
    return {"status": "signed_out"}


@app.get("/api/auth/me", response_model=AuthResponse)
async def me(user=Depends(current_user)):
    return auth_result(user)


@app.get("/api/health")
async def health():
    queue_task = getattr(app.state, "queue_worker_task", None)
    if settings().embedded_worker and (queue_task is None or queue_task.done()):
        from fastapi.responses import JSONResponse

        return JSONResponse({"status": "degraded", "detail": "Queue worker is not running"}, status_code=503)
    return {
        "status": "ok",
        "marketplace": settings().marketplace_mode,
        "inference": settings().inference_mode,
        "version": "1.0.0",
    }


@app.get("/api/settings")
async def get_settings(user=Depends(current_user)):
    return {
        "profile": json.loads(user.profile),
        "marketplace": settings().marketplace_mode,
        "style_memory": read_memory(user.id, "style"),
        "outcome_memory": read_memory(user.id, "outcome"),
        "model_profile": settings().model_profile,
        "rag_variant": settings().rag_variant,
    }


@app.patch("/api/settings", response_model=AuthResponse)
async def update_settings(body: Profile, user=Depends(current_user)):
    with db() as session:
        stored = session.get(User, user.id)
        stored.profile = body.model_dump_json()
        return auth_result(stored)


@app.delete("/api/memory/{kind}/{key}")
async def forget(kind: str, key: str, user=Depends(current_user)):
    if kind not in {"style", "outcome"}:
        raise HTTPException(400, "Invalid memory namespace")
    delete_memory(user.id, kind, key)
    return {"status": "deleted"}


@app.get("/api/jobs", response_model=JobListResponse)
async def jobs(query: str = "", user=Depends(current_user)):
    result = await Tools(user.id, "ui").call("search_jobs", query=query, limit=60)
    profile = json.loads(user.profile)
    persona_path = ROOT / "data/personas" / (profile.get("persona", "ml") + ".json")
    skills = json.loads(persona_path.read_text())["skills"] if persona_path.exists() else []
    with db() as session:
        runs = {r.job_id: r for r in session.query(Run).filter_by(tenant=user.id, kind="bid").all()}
        skipped = {r["id"] for r in records(session, user.id, "skipped_job")}
    for job in result["jobs"]:
        job["preliminary_fit"] = sum(s in skills for s in job["required_skills"]) / max(
            1, len(job["required_skills"])
        )
        run = runs.get(job["id"])
        job["run_id"], job["run_status"] = (run.id, run.status) if run else (None, "new")
        if job["id"] in skipped:
            job["run_status"] = "skipped"
    result["jobs"].sort(key=lambda j: j["preliminary_fit"], reverse=True)
    return {
        **result,
        "marketplace": settings().marketplace_mode,
        "provenance_notice": "Preliminary fit uses skill overlap. Open a job and run analysis for verified evidence and risks. Synthetic records are labeled.",
    }


@app.get("/api/jobs/{job_id}")
async def job_detail(job_id: str, user=Depends(current_user)):
    job = await Tools(user.id, "ui").call("get_job", job_id=job_id)
    with db() as session:
        run = (
            session.query(Run)
            .filter_by(tenant=user.id, job_id=job_id, kind="bid")
            .order_by(Run.created.desc())
            .first()
        )
        state = json.loads(run.state) if run else {}
    return {
        "job": job,
        "run_id": run.id if run else None,
        "status": run.status if run else "new",
        "analysis": state,
    }


@app.post("/api/jobs/{job_id}/analyze")
async def analyze(job_id: str, agency: bool = False, user=Depends(current_user)):
    job = await Tools(user.id, "ui").call("get_job", job_id=job_id)
    profile = json.loads(user.profile)
    if agency:
        from agent.agency import route_team

        routing = await route_team(user.id, job)
        if not routing["selected"]:
            raise HTTPException(422, "No team member has enough evidence for this opportunity")
        profile["persona"] = routing["selected"]
    with db() as session:
        existing = session.query(Run).filter_by(tenant=user.id, job_id=job_id, kind="bid").first()
        if existing:
            return {"id": existing.id, "status": existing.status}
        run_id = uid()
        state = {
            "tenant": user.id,
            "run_id": run_id,
            "job": job,
            "profile": profile,
            "steps": 0,
            "usage": [],
            "revision": 0,
        }
        session.add(Run(id=run_id, tenant=user.id, job_id=job_id, state=json.dumps(state)))
    await enqueue(run_id)
    return {"id": run_id, "status": "queued"}


@app.get("/api/jobs/{job_id}/agency")
async def agency_fit(job_id: str, user=Depends(current_user)):
    from agent.agency import route_team

    job = await Tools(user.id, "ui").call("get_job", job_id=job_id)
    return await route_team(user.id, job)


@app.post("/api/jobs/{job_id}/skip")
async def skip(job_id: str, user=Depends(current_user)):
    with db() as session:
        put(session, user.id, "skipped_job", job_id, {"id": job_id})
    return {"status": "skipped"}


def owned_run(session, user, run_id):
    run = session.get(Run, run_id)
    if not run or run.tenant != user.id:
        raise HTTPException(404, "Run not found")
    return run


def run_response(run):
    return {
        "id": run.id,
        "job_id": run.job_id,
        "kind": run.kind,
        "status": run.status,
        "state": json.loads(run.state),
        "error": run.error or "",
        "created": run.created,
    }


def current_portfolio_items(session, tenant, items):
    return [value for item in items if (value := get(session, tenant, "evidence", item["id"]))]


@app.get("/api/runs", response_model=list[RunResponse])
async def runs(user=Depends(current_user)):
    with db() as session:
        return [
            run_response(r)
            for r in session.query(Run).filter_by(tenant=user.id).order_by(Run.created.desc()).all()
        ]


@app.get("/api/runs/{run_id}", response_model=RunResponse)
async def get_run(run_id: str, user=Depends(current_user)):
    with db() as session:
        return run_response(owned_run(session, user, run_id))


@app.get("/api/runs/{run_id}/events")
async def events(run_id: str, request: Request, after: int = 0, user=Depends(current_user)):
    with db() as session:
        owned_run(session, user, run_id)
    cursor = max(after, int(request.headers.get("last-event-id", "0")))
    return event_stream(request, user.id, run_id, cursor)


@app.get("/api/runs/{run_id}/trace")
async def trace(run_id: str, user=Depends(current_user)):
    with db() as session:
        owned_run(session, user, run_id)
        return [
            {"id": e.id, "node": e.node, "payload": parse_event(e.payload), "created": e.created}
            for e in session.query(Event).filter_by(tenant=user.id, run_id=run_id).order_by(Event.id).all()
        ]


@app.get("/api/runs/{run_id}/history")
async def history(run_id: str, user=Depends(current_user)):
    with db() as session:
        run = owned_run(session, user, run_id)
        kind = run.kind
    async with graph_context(kind) as graph:
        return [
            {
                "checkpoint_id": s.config["configurable"].get("checkpoint_id"),
                "next": s.next,
                "created_at": s.created_at,
            }
            async for s in graph.aget_state_history({"configurable": {"thread_id": user.id + ":" + run_id}})
        ]


@app.post("/api/runs/{run_id}/retry")
async def retry_run(run_id: str, user=Depends(current_user)):
    with db() as session:
        run = owned_run(session, user, run_id)
        if run.status not in {"retry_queued", "needs_attention"}:
            raise HTTPException(409, "Only failed or queued work can be retried")
        state = json.loads(run.state)
        refresh = (
            run.kind == "bid" and state.get("draft") and state.get("decision", {}).get("action") == "bid"
        )
        run.status, run.error = "queued", ""
        if refresh:
            pending = session.get(Record, f"{user.id}:resume:{run_id}")
            if pending:
                session.delete(pending)
    if refresh:
        async with graph_context() as graph:
            await graph.aupdate_state(
                {"configurable": {"thread_id": user.id + ":" + run_id}},
                {"approval": {}, "preview": {}, "revision": 0},
                as_node="decide",
            )
    await enqueue(run_id)
    return {"status": "queued"}


@app.patch("/api/runs/{run_id}/draft")
async def edit_draft(run_id: str, body: DraftEdit, user=Depends(current_user)):
    with db() as session:
        run = owned_run(session, user, run_id)
        if run.status != "awaiting_approval":
            raise HTTPException(409, "Draft is not awaiting review")
        state = json.loads(run.state)
        verdict = verify(body.text, current_portfolio_items(session, user.id, state.get("evidence", [])))
        if verdict["unsupported_before"] or not compliance(body.text)["allowed"]:
            raise HTTPException(
                422,
                {
                    "message": "Edited draft contains unsupported claims or a policy violation",
                    "verification": verdict,
                },
            )
        put(
            session,
            user.id,
            "draft_edit",
            run_id,
            {"text": body.text, "before": state["draft"]["cover_letter"]},
        )
    return {"status": "saved", "verification": verdict}


@app.post("/api/runs/{run_id}/approve")
async def approve(run_id: str, body: ApprovalRequest, user=Depends(current_user)):
    with db() as session:
        session.query(User).filter_by(id=user.id).with_for_update().first()
        run = owned_run(session, user, run_id)
        if run.status != "awaiting_approval":
            raise HTTPException(409, "This run is no longer awaiting approval")
        state = json.loads(run.state)
        edit = get(session, user.id, "draft_edit", run_id)
        text = body.text or (edit["text"] if edit else state["draft"]["cover_letter"])
        if body.decision == "reject" and not body.reason.strip():
            raise HTTPException(422, "Add a reason for rejection")
        if body.decision != "reject":
            checked = verify(
                text + "\n\n" + "\n\n".join(state["draft"].get("screening_answers", [])),
                current_portfolio_items(session, user.id, state.get("evidence", [])),
            )
            if checked["unsupported_before"] or not compliance(text)["allowed"]:
                raise HTTPException(422, "Fix unsupported claims and policy violations before approving")
        action = "send_message" if run.kind == "conversation" else "submit_proposal"
        capability = token(
            user.id, "approval", ttl=7 * 86400, action=action, digest=fingerprint(effect_body(state, text))
        )
        command = {**body.model_dump(), "text": text, "approval_token": capability}
        put(session, user.id, "resume", run_id, command)
        run.status, run.updated = "queued", now()
    if body.decision != "reject" and text != state["draft"]["cover_letter"]:
        observe_edit(user.id, state["draft"]["cover_letter"], text)
    await enqueue(run_id)
    return {"id": run_id, "status": "queued"}


@app.get("/api/pipeline")
async def pipeline(user=Depends(current_user)):
    with db() as session:
        return {
            "proposals": records(session, user.id, "proposal"),
            "runs": [run_response(r) for r in session.query(Run).filter_by(tenant=user.id, kind="bid").all()],
        }


@app.post("/api/runs/{run_id}/regenerate")
async def regenerate(run_id: str, body: dict, user=Depends(current_user)):
    with db() as session:
        run = owned_run(session, user, run_id)
        if run.status != "awaiting_approval" or run.kind != "bid":
            raise HTTPException(409, "Only an unsubmitted proposal can be regenerated")
        index = body.get("paragraph_index", 0)
        if not isinstance(index, int) or not 0 <= index < 30:
            raise HTTPException(422, "Invalid paragraph index")
    async with graph_context() as graph:
        await graph.aupdate_state(
            {"configurable": {"thread_id": user.id + ":" + run_id}},
            {"regenerate_index": index, "revision": 0},
            as_node="pricing",
        )
    with db() as session:
        owned_run(session, user, run_id).status = "queued"
    await enqueue(run_id)
    return {"status": "queued"}


@app.post("/api/jobs/{job_id}/outcome")
async def outcome(job_id: str, body: OutcomeInput, user=Depends(current_user)):
    observe_outcome(user.id, job_id, body.category, body.outcome)
    return {"status": "recorded"}


@app.get("/api/messages")
async def messages(user=Depends(current_user)):
    return await Tools(user.id, "ui").call("list_messages")


@app.post("/api/messages/{conversation_id}/draft")
async def draft_message(conversation_id: str, user=Depends(current_user)):
    rid = uid()
    with db() as session:
        pending = (
            session.query(Run)
            .filter_by(
                tenant=user.id, job_id=conversation_id, kind="conversation", status="awaiting_approval"
            )
            .first()
        )
        if pending:
            return {"id": pending.id}
        state = {
            "tenant": user.id,
            "run_id": rid,
            "conversation_id": conversation_id,
            "profile": json.loads(user.profile),
            "usage": [],
            "steps": 0,
            "revision": 0,
        }
        session.add(
            Run(id=rid, tenant=user.id, job_id=conversation_id, kind="conversation", state=json.dumps(state))
        )
    await enqueue(rid)
    return {"id": rid}


@app.post("/api/portfolio/upload")
async def upload(file: UploadFile = File(...), user=Depends(current_user)):
    content = await file.read(5 * 1024 * 1024 + 1)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, "Maximum file size is 5 MB")
    try:
        chunks = load_upload(
            file.filename or "portfolio.txt", content, json.loads(user.profile).get("persona", "own")
        )
    except Exception as exc:
        raise HTTPException(422, str(exc)) from None
    with db() as session:
        for chunk in chunks:
            put(session, user.id, "evidence", chunk["id"], chunk)
    return {"status": "indexed", "chunks": len(chunks)}


@app.get("/api/analytics")
async def analytics(user=Depends(current_user)):
    import numpy as np

    with db() as session:
        runs = [run_response(r) for r in session.query(Run).filter_by(tenant=user.id).all()]
        outcomes = records(session, user.id, "outcome_observation")
        wallet = get(session, user.id, "wallet", "current") or {"balance": 120, "weekly_spent": 0}
    latencies = [r["state"]["elapsed_seconds"] for r in runs if r["state"].get("elapsed_seconds")]
    usage = [u for r in runs for u in r["state"].get("usage", [])]
    return {
        "runs": len(runs),
        "awaiting_approval": sum(r["status"] == "awaiting_approval" for r in runs),
        "wallet": wallet,
        "p50_seconds": float(np.percentile(latencies, 50)) if latencies else None,
        "p95_seconds": float(np.percentile(latencies, 95)) if latencies else None,
        "tokens": sum(u.get("input_tokens", 0) + u.get("output_tokens", 0) for u in usage),
        "usd_estimate": sum(u.get("usd_estimate", 0) for u in usage),
        "outcomes": outcomes,
        "reply_rate": sum(o["outcome"] in {"replied", "won", "hired"} for o in outcomes) / len(outcomes)
        if outcomes
        else None,
        "hire_rate": sum(o["outcome"] in {"won", "hired"} for o in outcomes) / len(outcomes)
        if outcomes
        else None,
        "source": "user-confirmed outcomes; local simulation is not instructor GigSim",
    }


async def workspace_effect(user, body, action, tool):
    content = body.model_dump(exclude={"confirmed"})
    proof = (
        token(user.id, "approval", ttl=60, action=action, digest=fingerprint(content))
        if body.confirmed
        else ""
    )
    return await Tools(user.id, "workspace_approval").call(
        tool,
        **content,
        idempotency_key=fingerprint(content),
        dry_run=not body.confirmed,
        approval_token=proof,
    )


@app.post("/api/workspace/hold")
async def calendar_hold(body: CalendarHold, user=Depends(current_user)):
    return await workspace_effect(user, body, "calendar_hold", "create_interview_hold")


@app.post("/api/workspace/email-draft")
async def email_draft(body: EmailDraft, user=Depends(current_user)):
    return await workspace_effect(user, body, "email_draft", "create_email_draft")


app.include_router(accounts_router)


@app.post("/api/portfolio/access-token")
async def portfolio_access_token(user=Depends(current_user)):
    endpoint = settings().portfolio_public_url or (
        settings().app_url + "/portfolio/mcp" if settings().mount_mcp_servers else "http://localhost:8101/mcp"
    )
    return {
        "token": token(user.id, "mcp", ttl=3600, server="portfolio"),
        "expires_in": 3600,
        "server_url": endpoint,
        "scope": "portfolio:read",
    }


@app.get("/api/portfolio")
async def portfolio_items(user=Depends(current_user)):
    persona = json.loads(user.profile).get("persona", "ml")
    with db() as session:
        items = [item for item in records(session, user.id, "evidence") if item["persona"] == persona]
    items.sort(key=lambda item: (item.get("provenance") == "synthetic", item["title"]))
    return {"items": items, "count": len(items)}


@app.delete("/api/portfolio/{evidence_id}")
async def delete_evidence(evidence_id: str, user=Depends(current_user)):
    with db() as session:
        row = session.get(Record, f"{user.id}:evidence:{evidence_id}")
        if not row:
            raise HTTPException(404, "Evidence not found")
        session.delete(row)
    return {"status": "deleted", "drafts_require_reverification": True}


@app.post("/api/runs/{run_id}/replay")
async def replay_run(run_id: str, body: ReplayRequest, user=Depends(current_user)):
    with db() as session:
        run = owned_run(session, user, run_id)
        if run.kind != "bid":
            raise HTTPException(422, "Conversation threads can be redrafted from Messages")
    rid = uid()
    async with graph_context() as graph:
        snapshot = await graph.aget_state(
            {"configurable": {"thread_id": user.id + ":" + run_id, "checkpoint_id": body.checkpoint_id}}
        )
        if not snapshot.values:
            raise HTTPException(404, "Checkpoint not found for this run")
        old = dict(snapshot.values)
        state = {
            **old,
            "tenant": user.id,
            "run_id": rid,
            "usage": [],
            "steps": 0,
            "revision": 0,
            "approval": {},
            "outcome": {},
            "preview": {},
            "status": "queued",
            "replay_of": run_id,
        }
        if body.stage == "analysis":
            state = {
                key: state[key]
                for key in ["tenant", "run_id", "job", "profile", "usage", "steps", "revision", "replay_of"]
            }
        else:
            required = {
                "pricing": ["decision", "fit", "risk", "spec"],
                "writer": ["price"],
                "verifier": ["draft"],
                "critic": ["verification"],
                "compliance_guard": ["critique"],
            }[body.stage]
            if any(key not in old for key in required):
                raise HTTPException(422, "This checkpoint does not contain the selected stage prerequisites")
            predecessor = {
                "pricing": "decide",
                "writer": "pricing",
                "verifier": "writer",
                "critic": "verifier",
                "compliance_guard": "critic",
            }[body.stage]
            await graph.aupdate_state(
                {"configurable": {"thread_id": user.id + ":" + rid}}, state, as_node=predecessor
            )
    with db() as session:
        session.add(Run(id=rid, tenant=user.id, job_id=old["job"]["id"], kind="bid", state=json.dumps(state)))
    await enqueue(rid)
    return {"id": rid, "status": "queued", "replay_of": run_id, "approval_required": True}


if settings().serve_frontend:
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    frontend = ROOT / "apps/web/dist"
    if not (frontend / "index.html").exists():
        raise RuntimeError("Build the frontend before enabling SERVE_FRONTEND")
    app.mount("/assets", StaticFiles(directory=frontend / "assets"), name="frontend-assets")

    @app.get("/{path:path}", include_in_schema=False)
    async def frontend_page(path: str):
        if path == "api" or path.startswith("api/"):
            raise HTTPException(404, "API endpoint not found")
        return FileResponse(frontend / "index.html")
