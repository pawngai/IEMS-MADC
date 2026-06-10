from __future__ import annotations

from app_platform.domain_separation.data_ownership import assert_collection_ownership
from contexts.notifications.domain.model import NotificationMessage


class NotificationRepository:
    def __init__(self, db) -> None:
        self._db = db
        assert_collection_ownership(
            context="notifications", collection_name="notifications", write=True,
        )

    async def add(self, message: NotificationMessage) -> None:
        document = {
            "id": message.id,
            "notification_id": message.id,
            "employee_id": message.employee_id,
            "type": message.type,
            "title": message.title,
            "message": message.message,
            "level": message.level,
            "timestamp": message.timestamp,
            "read": message.read,
            "action_url": message.action_url,
        }
        if message.source_event_id:
            document["source_event_id"] = message.source_event_id
            await self._db.notifications.update_one(
                {
                    "source_event_id": message.source_event_id,
                    "type": message.type,
                    "employee_id": message.employee_id,
                },
                {"$setOnInsert": document},
                upsert=True,
            )
            return
        await self._db.notifications.insert_one(document)
