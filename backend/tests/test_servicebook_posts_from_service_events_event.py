from __future__ import annotations

import pytest

from app_platform.event_bus.bus import EventBus
from app_platform.event_bus.types import BaseEvent
from app_platform.event_bus.types import EventName
from contexts.service_book.read_side.application.subscribers import (
    register_service_book_subscribers,
)


class _FakeCollection:
    def __init__(self) -> None:
        self.inserted: list[dict] = []
        self.updated: list[dict] = []

    async def find_one(self, *_args, **_kwargs):
        return None

    async def insert_one(self, document: dict):
        self.inserted.append(document)

    async def update_one(self, query, update, upsert=False):
        # Track $setOnInsert upserts as inserts for test assertions
        set_on_insert = (update or {}).get("$setOnInsert")
        if set_on_insert and upsert:
            # Check for existing match
            for item in self.inserted:
                if all(item.get(k) == v for k, v in query.items()):
                    return None  # Already exists — no-op (idempotent)
            self.inserted.append(set_on_insert)
        else:
            self.updated.append({"query": query, "update": update, "upsert": upsert})
        return None


class _FakeDb:
    def __init__(self) -> None:
        self.service_book_entries = _FakeCollection()
        self.service_book_part_projections = _FakeCollection()


@pytest.mark.asyncio
async def test_servicebook_posts_ledger_entry_from_approved_service_event() -> None:
    bus = EventBus()
    db = _FakeDb()
    register_service_book_subscribers(event_bus=bus, db_provider=lambda: db)

    await bus.publish(
        BaseEvent(
            name=EventName.SERVICE_EVENT_APPROVED.value,
            payload={
                "event_version": 1,
                "service_event_id": "se-1",
                "employee_id": "EMP-100",
                "part_code": "IV",
                "effective_date": "2026-03-03",
                "payload": {
                    "promotion": "Senior",
                    "document_ids": ["DOC-1"],
                    "workflow_state": "APPROVED",
                },
                "status": "APPROVED",
            },
        )
    )

    assert len(db.service_book_entries.inserted) == 1
    inserted = db.service_book_entries.inserted[0]
    assert inserted["employee_id"] == "EMP-100"
    assert inserted["part_code"] == "IV"
    assert inserted["event_name"] == EventName.SERVICE_EVENT_APPROVED.value
    assert inserted["payload"] == {"promotion": "Senior"}

    assert len(db.service_book_part_projections.updated) == 1
    updated = db.service_book_part_projections.updated[0]
    assert updated["query"] == {"employee_id": "EMP-100", "part_code": "IV"}
    assert updated["update"]["$set"]["last_event_name"] == EventName.SERVICE_EVENT_APPROVED.value


@pytest.mark.asyncio
async def test_servicebook_ignores_recorded_service_event_until_approved() -> None:
    bus = EventBus()
    db = _FakeDb()
    register_service_book_subscribers(event_bus=bus, db_provider=lambda: db)

    await bus.publish(
        BaseEvent(
            name=EventName.SERVICE_EVENT_RECORDED.value,
            payload={
                "event_version": 1,
                "service_event_id": "se-draft-1",
                "employee_id": "EMP-100",
                "event_type": "PROMOTION",
                "part_code": "IV",
                "effective_from": "2026-03-03",
                "payload": {"promotion": "Senior"},
            },
        )
    )

    assert db.service_book_entries.inserted == []
    assert db.service_book_part_projections.updated == []


