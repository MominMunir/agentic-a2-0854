import base64
import hashlib
import json
import secrets
from urllib.parse import urlencode, urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException

from apps.api.auth.session import current_user
from apps.api.schemas.models import GithubInput
from gigbid_core.config import settings
from gigbid_core.db import db, get, put
from gigbid_core.security import decrypt, encrypt, token, decode

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


def official_url(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not (
        parsed.hostname == "upwork.com" or (parsed.hostname or "").endswith(".upwork.com")
    ):
        raise HTTPException(400, "OAuth endpoint must be on an official HTTPS Upwork domain")
    return url


@router.get("/upwork/connect")
async def connect(user=Depends(current_user)):
    cfg = settings()
    async with httpx.AsyncClient(timeout=20) as client:
        base = "https://mcp.upwork.com"
        resource_response = await client.get(base + "/.well-known/oauth-protected-resource")
        resource_response.raise_for_status()
        issuer = official_url(resource_response.json()["authorization_servers"][0]).rstrip("/")
        metadata_response = await client.get(issuer + "/.well-known/oauth-authorization-server")
        metadata_response.raise_for_status()
        metadata = metadata_response.json()
        client_id = cfg.upwork_client_id
        if not client_id:
            registration = await client.post(
                official_url(metadata["registration_endpoint"]),
                json={
                    "client_name": "GigBid",
                    "redirect_uris": [cfg.upwork_redirect_uri],
                    "grant_types": ["authorization_code", "refresh_token"],
                    "response_types": ["code"],
                    "token_endpoint_auth_method": "none",
                },
            )
            registration.raise_for_status()
            client_id = registration.json()["client_id"]
        verifier = secrets.token_urlsafe(48)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        state = token(user.id, "oauth_state", ttl=600, nonce=secrets.token_urlsafe(24))
        with db() as session:
            put(
                session,
                user.id,
                "oauth_pending",
                "upwork",
                {
                    "encrypted": encrypt(
                        {"verifier": verifier, "state": state, "metadata": metadata, "client_id": client_id}
                    )
                },
            )
        url = (
            official_url(metadata["authorization_endpoint"])
            + "?"
            + urlencode(
                {
                    "client_id": client_id,
                    "redirect_uri": cfg.upwork_redirect_uri,
                    "response_type": "code",
                    "state": state,
                    "code_challenge": challenge,
                    "code_challenge_method": "S256",
                    "resource": cfg.upwork_mcp_url,
                }
            )
        )
        return {"authorization_url": url}


@router.get("/upwork/callback")
async def callback(code: str, state: str):
    try:
        user_id = decode(state, "oauth_state")["sub"]
        with db() as session:
            pending = decrypt(get(session, user_id, "oauth_pending", "upwork")["encrypted"])
        if not secrets.compare_digest(state, pending["state"]):
            raise ValueError()
    except Exception:
        raise HTTPException(400, "OAuth state expired or invalid; restart connection") from None
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            official_url(pending["metadata"]["token_endpoint"]),
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": pending["client_id"],
                "redirect_uri": settings().upwork_redirect_uri,
                "code_verifier": pending["verifier"],
                "resource": settings().upwork_mcp_url,
            },
        )
        response.raise_for_status()
    from gigbid_core.db import Record

    with db() as session:
        import time

        values = response.json()
        put(
            session,
            user_id,
            "oauth",
            "upwork",
            {
                "encrypted": encrypt(
                    {
                        **values,
                        "expires_at": time.time() + values.get("expires_in", 3600),
                        "token_endpoint": pending["metadata"]["token_endpoint"],
                        "client_id": pending["client_id"],
                    }
                )
            },
        )
        row = session.get(Record, f"{user_id}:oauth_pending:upwork")
        if row:
            session.delete(row)
    from fastapi.responses import RedirectResponse

    return RedirectResponse(settings().app_url + "/settings?connected=upwork", status_code=303)


@router.get("/upwork/tools")
async def official_tools(user=Depends(current_user)):
    from langchain_mcp_adapters.client import MultiServerMCPClient

    with db() as session:
        record = get(session, user.id, "oauth", "upwork")
    if not record:
        raise HTTPException(409, "Connect Upwork first")
    credentials = decrypt(record["encrypted"])
    client = MultiServerMCPClient(
        {
            "upwork": {
                "transport": "streamable_http",
                "url": settings().upwork_mcp_url,
                "headers": {"Authorization": "Bearer " + credentials["access_token"]},
            }
        }
    )
    return [
        {"name": t.name, "description": t.description, "schema": t.args_schema}
        for t in await client.get_tools()
    ]


@router.post("/upwork/tool-map")
async def tool_map(mapping: dict[str, str], user=Depends(current_user)):
    allowed = {
        "search_jobs",
        "get_job",
        "get_client_history",
        "get_connects_balance",
        "list_messages",
        "create_proposal_draft",
        "create_message_draft",
    }
    if set(mapping) - allowed or any(
        "draft" in key and "draft" not in value.lower() for key, value in mapping.items()
    ):
        raise HTTPException(422, "Only approved read tools and explicit draft tools can be mapped")
    with db() as session:
        put(session, user.id, "tool_map", "upwork", mapping)
    return {"status": "saved"}


@router.post("/github/ingest")
async def github_ingest(body: GithubInput, user=Depends(current_user)):
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from agent.mcp_client import parse_result
    from rag.ingest.loaders import load_upload

    if not settings().github_token:
        raise HTTPException(
            409, "Set GITHUB_TOKEN privately on the server to enable official GitHub MCP reads"
        )
    client = MultiServerMCPClient(
        {
            "github": {
                "transport": "streamable_http",
                "url": settings().github_mcp_url,
                "headers": {"Authorization": "Bearer " + settings().github_token, "X-MCP-Readonly": "true"},
            }
        }
    )
    tools = await client.get_tools()
    target = next((t for t in tools if t.name == "get_file_contents"), None)
    if not target:
        raise HTTPException(503, "Official GitHub file-read tool unavailable")
    result = parse_result(await target.ainvoke(body.model_dump()))
    if isinstance(result, list):
        result = result[0]
    content = result.get("content", "")
    if result.get("encoding") == "base64":
        content = base64.b64decode(content).decode("utf-8")
    chunks = load_upload(body.path, content.encode(), json.loads(user.profile).get("persona", "own"))
    with db() as session:
        for chunk in chunks:
            chunk.update(
                source=f"https://github.com/{body.owner}/{body.repo}/blob/HEAD/{body.path}",
                provenance="github_mcp",
            )
            put(session, user.id, "evidence", chunk["id"], chunk)
    return {"status": "indexed", "chunks": len(chunks), "source": "official GitHub MCP"}
