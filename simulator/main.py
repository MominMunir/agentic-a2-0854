"""Independent REST simulator for adapter contracts; not instructor GigSim."""

from fastapi import Depends, FastAPI, Header, HTTPException

from agent.handoffs import MessageWrite, ProposalWrite
from gigbid_core.config import settings
from gigbid_core.db import init_db
from gigbid_core.security import tenant_context, token, tenant, fingerprint
from mcp_servers.marketplace.adapters.local import LocalSimulatorAdapter

init_db()
app = FastAPI(title="GigBid local synthetic simulator (not instructor GigSim)")


async def auth(authorization: str = Header(""), x_tenant_id: str = Header("")):
    key = settings().gigsim_api_token
    if not key or authorization != "Bearer " + key or not x_tenant_id:
        raise HTTPException(401, "Simulator authentication required")
    marker = tenant_context.set(x_tenant_id)
    try:
        yield
    finally:
        tenant_context.reset(marker)


@app.get("/jobs", dependencies=[Depends(auth)])
async def jobs(query: str = "", limit: int = 30):
    return {"jobs": await LocalSimulatorAdapter().search_jobs(query, limit)}


@app.get("/jobs/{job_id}", dependencies=[Depends(auth)])
async def job(job_id: str):
    return await LocalSimulatorAdapter().get_job(job_id)


@app.get("/clients/{client_id}/history", dependencies=[Depends(auth)])
async def client(client_id: str):
    return await LocalSimulatorAdapter().get_client_history(client_id)


@app.get("/connects", dependencies=[Depends(auth)])
async def balance():
    return await LocalSimulatorAdapter().get_connects_balance()


@app.get("/messages", dependencies=[Depends(auth)])
async def messages(conversation_id: str = ""):
    return await LocalSimulatorAdapter().list_messages(conversation_id)


@app.post("/proposals", dependencies=[Depends(auth)])
async def submit(body: ProposalWrite):
    return await LocalSimulatorAdapter().submit_proposal(trusted_payload(body, "submit_proposal"))


@app.post("/proposals/drafts", dependencies=[Depends(auth)])
async def draft(body: ProposalWrite):
    return await LocalSimulatorAdapter().create_proposal_draft(trusted_payload(body, "create_proposal_draft"))


@app.post("/messages", dependencies=[Depends(auth)])
async def send(body: MessageWrite):
    return await LocalSimulatorAdapter().send_message(trusted_payload(body, "send_message"))


def trusted_payload(body, action):
    payload = body.model_dump()
    if not payload["dry_run"]:
        content = {
            k: v for k, v in payload.items() if k not in {"approval_token", "dry_run", "idempotency_key"}
        }
        payload["approval_token"] = token(
            tenant(), "approval", ttl=60, action=action, digest=fingerprint(content)
        )
    return payload
