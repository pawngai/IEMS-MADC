from __future__ import annotations

from contexts.notifications.domain.model import NotificationMessage
from contexts.notifications.infrastructure.repo import NotificationRepository


async def publish_notification(
    db,
    *,
    notification_id: str,
    employee_id: str,
    message_type: str,
    title: str,
    message: str,
    level: str,
    timestamp: str,
    action_url: str | None = None,
) -> None:
    repo = NotificationRepository(db)
    await repo.add(
        NotificationMessage(
            id=notification_id,
            employee_id=employee_id,
            type=message_type,
            title=title,
            message=message,
            level=level,
            timestamp=timestamp,
            read=False,
            action_url=action_url,
        )
    )
