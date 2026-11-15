from fastapi import HTTPException, Request

from gigbid_core.db import User, db
from gigbid_core.security import decode


def current_user(request: Request):
    raw = request.headers.get("authorization", "").removeprefix("Bearer ") or request.cookies.get(
        "gigbid_session", ""
    )
    try:
        user_id = decode(raw)["sub"]
        with db() as session:
            user = session.get(User, user_id)
            if not user:
                raise ValueError("User missing")
            return user
    except Exception:
        raise HTTPException(401, "Sign in to continue") from None
