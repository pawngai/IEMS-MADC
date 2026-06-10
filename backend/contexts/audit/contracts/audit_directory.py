"""Audit context read-only contracts for cross-context consumers."""
from __future__ import annotations

from typing import Any


async def list_audit_logs(
    db,
    *,
    query: dict[str, Any],
    limit: int = 50,
    offset: int = 0,
    projection: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    cursor = db.audit_logs.find(query, projection or {"_id": 0}).sort("timestamp", -1)
    if offset:
        cursor = cursor.skip(offset)
    cursor = cursor.limit(limit)
    return await cursor.to_list(limit)


async def count_audit_logs(
    db,
    *,
    query: dict[str, Any] | None = None,
) -> int:
    return int(await db.audit_logs.count_documents(query or {}))


async def list_audit_log_action_counts(
    db,
    *,
    limit: int = 100,
) -> list[dict[str, Any]]:
    cursor = db.audit_logs.aggregate(
        [
            {"$group": {"_id": "$action", "count": {"$sum": 1}}},
            {"$sort": {"count": -1, "_id": 1}},
        ]
    )
    return await cursor.to_list(limit)
