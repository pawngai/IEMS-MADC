from __future__ import annotations

import pytest

from app_platform.event_bus.types import EventName
from contexts.service_book.read_side.application.projection_rebuilder import (
    rebuild_from_approved_service_events,
)
from contexts.service_book.repository.read_repository import ServiceBookReadRepository


class _Cursor:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def sort(self, fields):
        for field, direction in reversed(fields):
            self._rows.sort(key=lambda row: row.get(field) or "", reverse=direction < 0)
        return self

    async def to_list(self, length: int):
        return self._rows[:length]


class _FakeCollection:
    def __init__(self, rows: list[dict] | None = None) -> None:
        self.items = list(rows or [])

    def find(self, query: dict, _projection: dict | None = None):
        rows = []
        for item in self.items:
            matched = True
            for key, value in query.items():
                if isinstance(value, dict) and "$ne" in value:
                    matched = item.get(key) != value["$ne"]
                elif item.get(key) != value:
                    matched = False
                if not matched:
                    break
            if matched:
                rows.append(dict(item))
        return _Cursor(rows)

    async def find_one(self, query: dict, _projection: dict | None = None):
        for item in self.items:
            if all(item.get(key) == value for key, value in query.items()):
                return dict(item)
        return None

    async def update_one(self, query: dict, update: dict, upsert: bool = False):
        existing = None
        for item in self.items:
            if all(item.get(key) == value for key, value in query.items()):
                existing = item
                break
        if existing is None and upsert:
            row = dict(query)
            row.update((update or {}).get("$setOnInsert") or {})
            row.update((update or {}).get("$set") or {})
            self.items.append(row)
            return None
        if existing is not None:
            existing.update((update or {}).get("$set") or {})
        return None

    async def insert_one(self, document: dict):
        self.items.append(dict(document))


class _FakeDb:
    def __init__(self) -> None:
        self.service_book_records = _FakeCollection(
            [
                {
                    "employee_id": "EMP-100",
                    "service_event_id": "SE-1",
                    "sequence": 1,
                    "event_type": "PROMOTION",
                    "part_code": "IV",
                    "status": "APPROVED",
                    "effective_from": "2026-04-01",
                    "order_number": "ORD/1",
                    "order_date": "2026-03-31",
                    "issuing_authority": "Commissioner",
                    "approved_at": "2026-04-02T10:00:00Z",
                    "approved_by": "approver",
                    "payload": {"to_post": "Senior Clerk", "document_ids": ["DOC-1"]},
                    "version": 1,
                },
                {
                    "employee_id": "EMP-100",
                    "service_event_id": "SE-DRAFT",
                    "sequence": 2,
                    "event_type": "TRANSFER",
                    "part_code": "IV",
                    "status": "DRAFT",
                    "payload": {"station": "Nagpur"},
                },
            ]
        )
        self.service_book_entries = _FakeCollection()
        self.service_book_part_projections = _FakeCollection()
        self.service_book_projection_status = _FakeCollection()
        self.leave_ledger_entries = _FakeCollection()


@pytest.mark.asyncio
async def test_rebuild_service_book_projection_replays_only_approved_service_events() -> None:
    db = _FakeDb()
    repo = ServiceBookReadRepository(db=db)

    result = await rebuild_from_approved_service_events(
        db=db,
        repo=repo,
        employee_id="EMP-100",
    )
    replay_result = await rebuild_from_approved_service_events(
        db=db,
        repo=repo,
        employee_id="EMP-100",
    )

    assert result["approved_events_seen"] == 1
    assert result["projected"] == 1
    assert replay_result["projected"] == 1
    assert len(db.service_book_entries.items) == 1
    projected_entry = db.service_book_entries.items[0]
    assert projected_entry["source_event_id"] == "SE-1"
    assert projected_entry["payload"] == {
        "event_type": "PROMOTION",
        "to_post": "Senior Clerk",
        "order_number": "ORD/1",
        "order_date": "2026-03-31",
        "issuing_authority": "Commissioner",
    }
    assert db.service_book_part_projections.items[0]["last_event_name"] == EventName.SERVICE_EVENT_APPROVED.value
    assert db.service_book_projection_status.items[0]["projection_name"] == "service_book.approved_service_events"
    assert db.service_book_projection_status.items[0]["last_event_id"] == "SE-1"
    assert db.service_book_projection_status.items[0]["status"] == "OK"
