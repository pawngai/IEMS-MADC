"""Cross-context read-only facade for change-request existence checks."""
from __future__ import annotations

from typing import Any


async def change_request_exists(db, *, request_id: str) -> bool:
    """Return True if a change request with *request_id* exists."""
    return await get_change_request_by_id(db, request_id=request_id) is not None


async def get_change_request_by_id(
    db,
    *,
    request_id: str,
    projection: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Return a change request by public or Mongo id for read-only cross-context checks."""
    if db is None or not request_id:
        return None
    col = db["change_requests"]
    doc = await col.find_one({"_id": request_id}, projection)
    if doc is None:
        doc = await col.find_one({"request_id": request_id}, projection)
    return doc
