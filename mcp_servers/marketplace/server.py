from pydantic import Field

from agent.handoffs import MessageWrite, ProposalWrite
from agent.marketplace_port import marketplace
from mcp_servers.common import READ, WRITE, audit_tool, create_server, serve

mcp = create_server("GigBid Marketplace", 8102)


@mcp.tool(annotations=READ)
@audit_tool
async def search_jobs(query: str = "", limit: int = Field(default=30, ge=1, le=200)) -> dict:
    """Search marketplace job postings. No writes or Connects spend."""
    return {"jobs": await marketplace().search_jobs(query, limit)}


@mcp.tool(annotations=READ)
@audit_tool
async def get_job(job_id: str) -> dict:
    """Read one complete marketplace job by its stable ID."""
    return await marketplace().get_job(job_id)


@mcp.tool(annotations=READ)
@audit_tool
async def get_client_history(client_id: str) -> dict:
    """Read client spending, payment verification and past hiring; missing data stays unknown."""
    return await marketplace().get_client_history(client_id)


@mcp.tool(annotations=READ)
@audit_tool
async def get_connects_balance() -> dict:
    """Read remaining Connects and current weekly spend."""
    return await marketplace().get_connects_balance()


@mcp.tool(annotations=READ)
@audit_tool
async def list_messages(conversation_id: str = "") -> dict:
    """Read client messages, optionally within one conversation."""
    return {"messages": await marketplace().list_messages(conversation_id)}


@mcp.tool(annotations=WRITE)
@audit_tool
async def create_proposal_draft(request: ProposalWrite) -> dict:
    """Preview or create a draft. Non-preview requires content-bound human approval and an idempotency key."""
    return await marketplace().create_proposal_draft(request.model_dump())


@mcp.tool(annotations=WRITE)
@audit_tool
async def submit_proposal(request: ProposalWrite) -> dict:
    """Preview or send an approved simulator proposal, spending displayed Connects exactly once. Live mode creates a confirmation draft only."""
    return await marketplace().submit_proposal(request.model_dump())


@mcp.tool(annotations=WRITE)
@audit_tool
async def send_message(request: MessageWrite) -> dict:
    """Preview or send a human-approved message. Live mode creates a platform confirmation draft."""
    return await marketplace().send_message(request.model_dump())


if __name__ == "__main__":
    serve(mcp)
