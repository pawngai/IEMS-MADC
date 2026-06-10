from __future__ import annotations

import pytest

from app_platform.event_bus.bus import EventBus
from app_platform.event_bus.types import EventName
from app_platform.outbox.dispatcher import OutboxDispatcher
from contexts.service_book.read_side.application.subscribers import (
    register_service_book_subscribers,
)


class _FakeCollection:
    def __init__(self) -> None:
        self.items: list[dict] = []

    async def insert_one(self, document: dict):
        self.items.append(dict(document))

    async def update_one(self, query: dict, update: dict, upsert: bool = False):
        existing = None
        for row in self.items:
            if all(row.get(k) == v for k, v in query.items()):
                existing = row
                break
        if existing is None and upsert:
            set_on_insert = (update or {}).get("$setOnInsert") or {}
            set_fields = (update or {}).get("$set") or {}
            row = {**query, **set_on_insert, **set_fields}
            self.items.append(row)
        elif existing is not None:
            existing.update((update or {}).get("$set") or {})

    def find(self, query: dict, _projection: dict):
        rows = [
            dict(item)
            for item in self.items
            if all(item.get(key) == value for key, value in query.items())
        ]

        class _Cursor:
            def __init__(self, payload):
                self._payload = payload

            def sort(self, *_args, **_kwargs):
                return self

            async def to_list(self, length: int):
                return self._payload[:length]

        return _Cursor(rows)


class _FakeDb:
    def __init__(self) -> None:
        self.service_book_entries = _FakeCollection()
        self.service_book_part_projections = _FakeCollection()


class _FakeOutboxRepo:
    def __init__(self, docs: list[dict]) -> None:
        self._docs = docs
        self.sent_ids: list[str] = []

    async def get_pending(self, batch_size: int = 100, **_kwargs) -> list[dict]:
        return self._docs[:batch_size]

    async def lock_for_processing(self, event_id: str, ttl_seconds: int = 30) -> bool:
        return True

    async def mark_sent(self, event_id: str) -> None:
        self.sent_ids.append(event_id)

    async def mark_failed(self, event_id: str, err: str, **_kwargs) -> None:
        raise AssertionError(f"Unexpected failure: {event_id} {err}")


@pytest.mark.asyncio
async def test_outbox_service_event_approved_projects_service_book() -> None:
    db = _FakeDb()
    bus = EventBus()
    register_service_book_subscribers(event_bus=bus, db_provider=lambda: db)

    repo = _FakeOutboxRepo(
        [
            {
                "_id": "evt-se-1",
                "name": EventName.SERVICE_EVENT_APPROVED.value,
                "payload": {
                    "event_version": 1,
                    "service_event_id": "SE-1",
                    "employee_id": "EMP-501",
                    "event_type": "PROMOTION",
                    "part_code": "IV",
                    "status": "APPROVED",
                    "effective_date": "2026-03-01",
                    "payload": {
                        "to_post": "Senior Clerk",
                        "documents": [{"document_id": "DOC-1"}],
                        "workflow_payload": {"approved_by": "approver-1"},
                    },
                },
                "actor_id": "approver-1",
                "department_id": "EST",
                "occurred_at": "2026-03-04T10:00:00+00:00",
            }
        ]
    )
    dispatcher = OutboxDispatcher(outbox_repo=repo, event_bus=bus)

    await dispatcher._drain_once()

    assert repo.sent_ids == ["evt-se-1"]
    assert len(db.service_book_entries.items) == 1
    assert db.service_book_entries.items[0]["employee_id"] == "EMP-501"
    assert db.service_book_entries.items[0]["event_name"] == EventName.SERVICE_EVENT_APPROVED.value
    assert db.service_book_entries.items[0]["payload"] == {
        "event_type": "PROMOTION",
        "to_post": "Senior Clerk",
    }


