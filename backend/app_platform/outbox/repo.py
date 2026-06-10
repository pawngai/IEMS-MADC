from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import app_platform.contracts.events  # noqa: F401
from app_platform.contracts.registry import validate_event_payload
from app_platform.outbox.model import OutboxEvent, OutboxStatus


class OutboxRepository:
    def __init__(self, db) -> None:
        self._db = db

    @property
    def _collection(self):
        return self._db.outbox_events

    async def add_event(self, event: OutboxEvent, *, session=None) -> None:
        validated_payload = validate_event_payload(
            name=event.name,
            version=event.event_version,
            payload=event.payload,
        )
        event.payload = validated_payload

        filter_doc = {"_id": event.event_id}
        if event.idempotency_key:
            filter_doc = {
                "name": event.name,
                "event_version": event.event_version,
                "idempotency_key": event.idempotency_key,
            }

        if session is None:
            await self._collection.update_one(
                filter_doc,
                {"$setOnInsert": event.to_document()},
                upsert=True,
            )
            return
        try:
            await self._collection.update_one(
                filter_doc,
                {"$setOnInsert": event.to_document()},
                upsert=True,
                session=session,
            )
        except TypeError as exc:
            if session is None or "session" not in str(exc):
                raise
            await self._collection.update_one(
                filter_doc,
                {"$setOnInsert": event.to_document()},
                upsert=True,
            )

    async def get_pending(
        self,
        batch_size: int = 100,
        *,
        max_attempts: int = 5,
    ) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        cursor = self._collection.find(
            {
                "status": {"$in": [OutboxStatus.PENDING.value, OutboxStatus.FAILED.value]},
                "$and": [
                    {
                        "$or": [
                            {"attempts": {"$lt": max_attempts}},
                            {"attempts": {"$exists": False}},
                        ]
                    },
                    {
                        "$or": [
                            {"next_attempt_at": None},
                            {"next_attempt_at": {"$lte": now}},
                            {"next_attempt_at": {"$exists": False}},
                        ]
                    },
                ],
                "$or": [
                    {"locked_until": None},
                    {"locked_until": {"$lt": now}},
                    {"locked_until": {"$exists": False}},
                ],
            }
        ).sort("occurred_at", 1).limit(batch_size)
        return await cursor.to_list(length=batch_size)

    async def lock_for_processing(self, event_id: str, ttl_seconds: int = 30) -> bool:
        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat()
        lock_until = (now_dt + timedelta(seconds=ttl_seconds)).isoformat()
        result = await self._collection.update_one(
            {
                "_id": event_id,
                "$or": [
                    {"locked_until": None},
                    {"locked_until": {"$lt": now}},
                    {"locked_until": {"$exists": False}},
                ],
            },
            {"$set": {"locked_until": lock_until}},
        )
        return bool(result.modified_count)

    async def mark_sent(self, event_id: str) -> None:
        await self._collection.update_one(
            {"_id": event_id},
            {
                "$set": {
                    "status": OutboxStatus.SENT.value,
                    "last_error": None,
                    "locked_until": None,
                }
            },
        )

    async def mark_failed(
        self,
        event_id: str,
        err: str,
        *,
        max_attempts: int = 5,
    ) -> None:
        current = await self._collection.find_one(
            {"_id": event_id},
            {"attempts": 1},
        )
        next_attempt_count = int((current or {}).get("attempts") or 0) + 1
        dead_letter = next_attempt_count >= max_attempts
        delay_seconds = min(3600, 2 ** max(next_attempt_count - 1, 0))
        next_attempt_at = None
        if not dead_letter:
            next_attempt_at = (
                datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
            ).isoformat()
        await self._collection.update_one(
            {"_id": event_id},
            {
                "$set": {
                    "status": (
                        OutboxStatus.DEAD_LETTER.value
                        if dead_letter
                        else OutboxStatus.FAILED.value
                    ),
                    "last_error": err,
                    "locked_until": None,
                    "next_attempt_at": next_attempt_at,
                },
                "$inc": {"attempts": 1},
            },
        )

    async def get_sent(
        self,
        *,
        event_names: list[str] | None = None,
        batch_size: int = 500,
    ) -> list[dict[str, Any]]:
        """Return already-sent events for replay.  Caller applies idempotent projections."""
        query: dict[str, Any] = {"status": OutboxStatus.SENT.value}
        if event_names:
            query["name"] = {"$in": event_names}
        cursor = self._collection.find(query).sort("occurred_at", 1).limit(batch_size)
        return await cursor.to_list(length=batch_size)
