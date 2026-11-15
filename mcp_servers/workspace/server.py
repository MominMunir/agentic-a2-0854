from datetime import datetime, timedelta, timezone

from pydantic import Field

from gigbid_core.db import db, get, put
from gigbid_core.security import decode, fingerprint, tenant
from mcp_servers.common import READ, WRITE, audit_tool, create_server, serve

mcp = create_server("GigBid Workspace (local calendar/email)", 8103)


@mcp.tool(annotations=READ)
@audit_tool
async def free_calendar_slots(days: int = Field(default=7, ge=1, le=30)) -> dict:
    """Read available 30-minute UTC slots from the local demonstration calendar."""
    slots = []
    with db() as session:
        for offset in range(1, days + 1):
            day = (datetime.now(timezone.utc) + timedelta(days=offset)).replace(
                hour=10, minute=0, second=0, microsecond=0
            )
            if day.weekday() < 5:
                for hour in [10, 14]:
                    start = day.replace(hour=hour).isoformat()
                    if not get(session, tenant(), "calendar_hold", start):
                        slots.append(
                            {
                                "start": start,
                                "end": (day.replace(hour=hour) + timedelta(minutes=30)).isoformat(),
                            }
                        )
    return {"slots": slots, "source": "local_mock", "timezone": "UTC"}


async def write_local(kind, body, approval_token, idempotency_key, dry_run):
    if dry_run:
        return {"status": "preview", "payload": body, "connects_cost": 0}
    claims = decode(approval_token, "approval")
    if claims["sub"] != tenant() or claims.get("digest") != fingerprint(body) or claims.get("action") != kind:
        raise PermissionError("Explicit human approval required")
    with db() as session:
        existing = get(session, tenant(), "workspace_effect", idempotency_key)
        if existing:
            return existing
        result = {"status": "created", "source": "local_mock", **body}
        put(session, tenant(), kind, body.get("start", idempotency_key), result)
        put(session, tenant(), "workspace_effect", idempotency_key, result)
        return result


@mcp.tool(annotations=WRITE)
@audit_tool
async def create_interview_hold(
    start: str, end: str, title: str, idempotency_key: str, approval_token: str = "", dry_run: bool = True
) -> dict:
    """Create a tentative local calendar hold after approval; never an external invitation."""
    if datetime.fromisoformat(end) <= datetime.fromisoformat(start):
        raise ValueError("End must follow start")
    return await write_local(
        "calendar_hold",
        {"start": start, "end": end, "title": title},
        approval_token,
        idempotency_key,
        dry_run,
    )


@mcp.tool(annotations=WRITE)
@audit_tool
async def create_email_draft(
    subject: str, body: str, idempotency_key: str, approval_token: str = "", dry_run: bool = True
) -> dict:
    """Save a local email draft after approval. Does not send email."""
    return await write_local(
        "email_draft", {"subject": subject, "body": body}, approval_token, idempotency_key, dry_run
    )


if __name__ == "__main__":
    serve(mcp)
