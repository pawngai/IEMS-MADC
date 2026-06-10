from __future__ import annotations

from datetime import datetime, timezone


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def actor_id(user: dict) -> str:
    return str(user.get("sub") or user.get("id") or "unknown")


def actor_name(user: dict) -> str:
    return str(user.get("name") or user.get("email") or actor_id(user))
