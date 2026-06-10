"""Notification context contracts for cross-context consumers."""
from __future__ import annotations

from typing import Any

from contexts.notifications.contracts.publisher import publish_notification


async def list_notifications_for_employee(
    db,
    *,
    employee_id: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    return (
        await db.notifications.find(
            {"employee_id": employee_id},
            {"_id": 0},
        )
        .sort("timestamp", -1)
        .to_list(limit)
    )


async def count_unread_notifications(
    db,
    *,
    employee_id: str,
) -> int:
    return await db.notifications.count_documents(
        {"employee_id": employee_id, "read": False}
    )


__all__ = [
    "publish_notification",
    "list_notifications_for_employee",
    "count_unread_notifications",
]
