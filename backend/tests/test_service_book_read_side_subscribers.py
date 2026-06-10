from __future__ import annotations

import asyncio

from app_platform.event_bus.bus import EventBus
from app_platform.event_bus.types import BaseEvent, EventName
from contexts.service_book.read_side.application.subscribers import (
    register_service_book_subscribers,
)


class _FakeCollection:
    def __init__(self) -> None:
        self.items: list[dict] = []

    async def insert_one(self, doc: dict):
        self.items.append(dict(doc))

    async def update_one(self, query: dict, update: dict, upsert: bool = False):
        existing = None
        for item in self.items:
            if all(item.get(k) == v for k, v in query.items()):
                existing = item
                break

        if existing is None and upsert:
            doc = dict(query)
            doc.update((update or {}).get("$set") or {})
            self.items.append(doc)
        elif existing is not None:
            existing.update((update or {}).get("$set") or {})

    def find(self, query: dict, _projection: dict):
        data = [
            dict(item)
            for item in self.items
            if all(item.get(key) == value for key, value in query.items())
        ]

        class _Cursor:
            def __init__(self, rows):
                self._rows = rows

            def sort(self, *_args, **_kwargs):
                return self

            async def to_list(self, length: int):
                return self._rows[:length]

        return _Cursor(data)

    async def find_one(self, query: dict, _projection: dict):
        for item in self.items:
            if all(item.get(k) == v for k, v in query.items()):
                return dict(item)
        return None


class _FakeDb:
    def __init__(self) -> None:
        self.service_book_entries = _FakeCollection()
        self.service_book_part_projections = _FakeCollection()


def test_employee_events_do_not_project_into_service_book() -> None:
    bus = EventBus()
    db = _FakeDb()

    register_service_book_subscribers(event_bus=bus, db_provider=lambda: db)

    asyncio.run(
        bus.publish(
            BaseEvent(
                name=EventName.EMPLOYEE_CREATED.value,
                payload={
                    "employee_id": "EMP-1",
                    "dept_id": "FIN",
                    "name": "Jane",
                    "dob": "1990-01-01",
                    "doj": "2020-01-01",
                    "designation_id": "DES-1",
                    "created_at": "2026-03-03T00:00:00Z",
                    "version": 1,
                    "event_version": 1,
                },
            )
        )
    )

    assert db.service_book_entries.items == []
    assert db.service_book_part_projections.items == []


