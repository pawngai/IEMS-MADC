from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from contexts.identity.infrastructure import repo
from contexts.identity.contracts.schemas import ActivityLogResponse
from contexts.identity_access.contracts.access_control import require_system_admin


def _window_start_iso(days: int) -> str:
    since = datetime.now(timezone.utc).timestamp() - (days * 86400)
    return datetime.fromtimestamp(since, tz=timezone.utc).isoformat()


async def list_activity_logs(
    db,
    *,
    skip: int,
    limit: int,
    action: Optional[str],
    user_id: Optional[str],
    current_user: dict,
) -> list[ActivityLogResponse]:
    require_system_admin(current_user)

    query: dict[str, Any] = {}
    if action:
        query["action"] = action
    if user_id:
        query["performed_by_id"] = user_id

    logs = await repo.list_user_activity_logs(db, query, skip=skip, limit=limit)
    return [ActivityLogResponse(**l) for l in logs]


async def get_activity_stats(db, *, days: int, current_user: dict) -> dict:
    require_system_admin(current_user)

    # Match existing behaviour in backend/routes/user_management.py
    since_iso = _window_start_iso(days)

    pipeline = [
        {"$match": {"timestamp": {"$gte": since_iso}}},
        {"$group": {"_id": "$action", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    stats = await repo.aggregate_user_activity_stats(db, pipeline)
    return {"days": days, "actions": stats}


async def get_role_change_history(
    db,
    *,
    skip: int,
    limit: int,
    user_id: Optional[str],
    current_user: dict,
) -> dict:
    require_system_admin(current_user)

    query: dict[str, Any] = {}
    if user_id:
        query["target_user_id"] = user_id

    history = await repo.list_role_change_history(db, query, skip=skip, limit=limit)
    # Keep both keys for compatibility across callers.
    return {"history": history, "changes": history, "skip": skip, "limit": limit}


async def get_role_change_stats(db, *, days: int, current_user: dict) -> dict:
    require_system_admin(current_user)

    since_iso = _window_start_iso(days)
    weekly_since_iso = _window_start_iso(7)

    pipeline = [
        {"$match": {"timestamp": {"$gte": since_iso}}},
        {"$group": {"_id": "$change_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    weekly_pipeline = [
        {"$match": {"timestamp": {"$gte": weekly_since_iso}}},
        {"$group": {"_id": "$change_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    stats = await repo.aggregate_role_change_stats(db, pipeline)
    weekly_stats = await repo.aggregate_role_change_stats(db, weekly_pipeline)
    total_changes = sum(int(item.get("count", 0)) for item in stats)
    changes_last_7_days = sum(int(item.get("count", 0)) for item in weekly_stats)
    return {
        "days": days,
        "stats": stats,
        "total_changes": total_changes,
        "changes_last_7_days": changes_last_7_days,
    }
