from __future__ import annotations


async def mark_notification_read(
    db,
    *,
    notification_id: str,
) -> None:
    await db.notifications.update_one(
        {"id": notification_id},
        {"$set": {"read": True}},
    )


__all__ = ["mark_notification_read"]