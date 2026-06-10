from __future__ import annotations

from pathlib import Path

import pytest

from app_platform.event_bus.bus import EventBus
from app_platform.event_bus.types import BaseEvent, EventName
from contexts.service_book.read_side.application.subscribers import (
    register_service_book_subscribers,
)


BACKEND_ROOT = Path(__file__).resolve().parents[1]


class _FakeCollection:
    def __init__(self) -> None:
        self.items: list[dict] = []

    async def update_one(self, query: dict, update: dict, upsert: bool = False):
        set_on_insert = (update or {}).get("$setOnInsert")
        if set_on_insert and upsert:
            self.items.append(dict(set_on_insert))
            return None
        if upsert:
            self.items.append({**query, **((update or {}).get("$set") or {})})
        return None

    async def insert_one(self, document: dict):
        self.items.append(dict(document))


class _FakeDb:
    def __init__(self) -> None:
        self.service_book_entries = _FakeCollection()
        self.service_book_part_projections = _FakeCollection()


def test_service_book_service_event_subscriber_allowlist_is_approved_only() -> None:
    source = (
        BACKEND_ROOT
        / "contexts"
        / "service_book"
        / "read_side"
        / "application"
        / "subscribers.py"
    ).read_text(encoding="utf-8")

    assert "event.name == EventName.SERVICE_EVENT_APPROVED.value" in source
    assert "event.name in {EventName.SERVICE_EVENT_RECORDED" not in source
    assert "subscribe(EventName.SERVICE_EVENT_RECORDED.value" not in source
    assert "subscribe(EventName.SERVICE_EVENT_DOCUMENT_ATTACHED.value" not in source


@pytest.mark.asyncio
async def test_document_attachment_payload_never_projects_service_book_truth() -> None:
    db = _FakeDb()
    bus = EventBus()
    register_service_book_subscribers(event_bus=bus, db_provider=lambda: db)

    await bus.publish(
        BaseEvent(
            name=EventName.SERVICE_EVENT_DOCUMENT_ATTACHED.value,
            payload={
                "event_version": 1,
                "service_event_id": "SE-DOC",
                "employee_id": "EMP-1",
                "document_id": "DOC-1",
                "document_type": "ORDER",
            },
        )
    )

    assert db.service_book_entries.items == []
    assert db.service_book_part_projections.items == []


@pytest.mark.asyncio
async def test_manual_ledger_projection_requires_manual_entry_policy() -> None:
    db = _FakeDb()
    bus = EventBus()
    register_service_book_subscribers(event_bus=bus, db_provider=lambda: db)

    await bus.publish(
        BaseEvent(
            name=EventName.SERVICE_BOOK_ENTRY_APPROVED.value,
            payload={
                "event_version": 1,
                "employee_id": "EMP-1",
                "part_key": "SB_PART_IV",
                "schema_key": "SB_IV_SERVICE_HISTORY_ROW",
                "payload": {"post_held": "Section Officer"},
                "status": "APPROVED",
            },
        )
    )

    assert db.service_book_entries.items == []
    assert db.service_book_part_projections.items == []


@pytest.mark.asyncio
async def test_policy_controlled_manual_exception_projects_sanitized_payload() -> None:
    db = _FakeDb()
    bus = EventBus()
    register_service_book_subscribers(event_bus=bus, db_provider=lambda: db)

    await bus.publish(
        BaseEvent(
            name=EventName.SERVICE_BOOK_ENTRY_APPROVED.value,
            payload={
                "event_version": 1,
                "employee_id": "EMP-1",
                "part_key": "SB_PART_III",
                "schema_key": "SB_III_PREVIOUS_SERVICE_ROW",
                "effective_date": "2026-01-01",
                "payload": {
                    "department_name": "Planning",
                    "post_held": "Assistant",
                    "documents": [{"document_id": "DOC-2"}],
                    "workflow_state": "APPROVED",
                },
                "status": "APPROVED",
            },
        )
    )

    assert len(db.service_book_entries.items) == 1
    assert db.service_book_entries.items[0]["payload"] == {
        "department_name": "Planning",
        "post_held": "Assistant",
    }