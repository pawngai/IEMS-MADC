from __future__ import annotations

from fastapi import HTTPException

from app_platform.auth.current_user import get_current_user


def get_db():
    """Return MongoDB handle, raising 503 when the database is offline."""
    from app_platform.db.runtime import mongo_state

    if mongo_state.db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    return mongo_state.db
