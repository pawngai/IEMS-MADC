from __future__ import annotations

from fastapi import HTTPException, Request
import jwt

from app_platform.config.settings import settings


async def get_current_user(request: Request) -> dict:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = auth_header.replace("Bearer ", "", 1).strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if not isinstance(payload, dict):
            raise HTTPException(status_code=401, detail="Invalid token")
        await _validate_live_user(request, payload)
        requested_role = str(request.headers.get("X-IEMS-Active-Role") or "").strip().upper()
        authorities = payload.get("authorities", [])
        if requested_role and isinstance(authorities, list) and requested_role in authorities:
            payload["active_role"] = requested_role
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def _validate_live_user(request: Request, payload: dict) -> None:
    """Reject access tokens invalidated by role/password/deactivation changes."""

    db = getattr(getattr(request, "app", None), "state", None)
    db = getattr(db, "db", None)
    if db is None:
        return

    user_id = str(payload.get("sub") or "").strip()
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    users = getattr(db, "users", None)
    if users is None or not hasattr(users, "find_one"):
        return

    user = await users.find_one(
        {"id": user_id},
        {"_id": 0, "id": 1, "is_active": 1, "token_version": 1},
    )
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")
    if user.get("is_active") is False:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    if "token_version" not in payload:
        raise HTTPException(status_code=401, detail="Token has been revoked")

    token_version = int(payload.get("token_version") or 0)
    live_version = int(user.get("token_version") or 0)
    if token_version != live_version:
        raise HTTPException(status_code=401, detail="Token has been revoked")
