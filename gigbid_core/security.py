import hashlib
import json
import re
import time
from contextvars import ContextVar
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from cryptography.fernet import Fernet

from gigbid_core.config import settings

tenant_context = ContextVar("tenant", default="")
trace_context = ContextVar("trace_id", default="")
passwords = PasswordHasher()


def token(tenant, purpose="session", ttl=86400, **claims):
    settings().require_secrets()
    return jwt.encode(
        {
            "sub": tenant,
            "purpose": purpose,
            "exp": datetime.now(timezone.utc) + timedelta(seconds=ttl),
            **claims,
        },
        settings().app_secret_key,
        algorithm="HS256",
    )


def decode(value, purpose="session"):
    claims = jwt.decode(
        value, settings().app_secret_key, algorithms=["HS256"], options={"require": ["sub", "purpose", "exp"]}
    )
    if claims["purpose"] != purpose:
        raise ValueError("Invalid token purpose")
    return claims


def tenant():
    value = tenant_context.get() or settings().mcp_stdio_tenant
    if not value:
        raise PermissionError("Authenticated tenant required")
    return value


def redact(value):
    def mask_string(text):
        text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[EMAIL]", text)

        def mask_number(match):
            candidate = match.group(0)
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", candidate) or len(re.sub(r"\D", "", candidate)) < 10:
                return candidate
            return "[PHONE_OR_ACCOUNT]"

        text = re.sub(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)", mask_number, text)
        return re.sub(r"(?i)(bearer\s+)[\w.\-]+", r"\1[REDACTED]", text)

    def mask(item):
        if isinstance(item, dict):
            return {key: mask(content) for key, content in item.items()}
        if isinstance(item, list):
            return [mask(content) for content in item]
        return mask_string(item) if isinstance(item, str) else item

    if isinstance(value, str):
        if value.lstrip().startswith(("{", "[")):
            try:
                return json.dumps(mask(json.loads(value)))
            except json.JSONDecodeError:
                pass
        return mask_string(value)
    return json.dumps(mask(value))


def fingerprint(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def encrypt(value):
    return Fernet(settings().token_encryption_key.encode()).encrypt(json.dumps(value).encode()).decode()


def decrypt(value):
    return json.loads(Fernet(settings().token_encryption_key.encode()).decrypt(value.encode()))


class MCPAuth:
    """Validate per-tenant, short-lived internal MCP tokens before SDK dispatch."""

    def __init__(self, app, server_id=None):
        self.app = app
        self.server_id = server_id
        self.windows = {}

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        try:
            claims = decode(headers.get(b"authorization", b"").decode().removeprefix("Bearer "), "mcp")
            if self.server_id and claims.get("server") not in {self.server_id, "*"}:
                raise PermissionError("Token is scoped to another MCP server")
            user = claims["sub"]
            tick = int(time.time() // 60)
            key = (user, tick)
            self.windows = {k: v for k, v in self.windows.items() if k[1] >= tick}
            self.windows[key] = self.windows.get(key, 0) + 1
            if self.windows[key] > 180:
                raise OverflowError("MCP rate limit exceeded")
        except Exception as exc:
            status = 429 if isinstance(exc, OverflowError) else 401
            await send(
                {
                    "type": "http.response.start",
                    "status": status,
                    "headers": [(b"content-type", b"application/json")],
                }
            )
            return await send(
                {"type": "http.response.body", "body": b'{"detail":"Authentication or rate limit failure"}'}
            )
        t = tenant_context.set(user)
        tr = trace_context.set(headers.get(b"x-trace-id", b"").decode())
        from opentelemetry.context import attach, detach
        from opentelemetry.propagate import extract

        parent = attach(extract({k.decode(): v.decode() for k, v in headers.items()}))
        try:
            await self.app(scope, receive, send)
        finally:
            detach(parent)
            tenant_context.reset(t)
            trace_context.reset(tr)
