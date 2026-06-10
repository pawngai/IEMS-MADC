from __future__ import annotations

from pathlib import Path

import pytest

from contexts.service_book.records.repository.service_record_repository import ServiceRecordRepository


def test_service_event_runtime_indexes_cover_production_queries() -> None:
    runtime_source = (Path(__file__).resolve().parents[1] / "app_platform" / "db" / "runtime.py").read_text(
        encoding="utf-8"
    )

    assert '("employee_id", ASCENDING), ("event_type", ASCENDING), ("effective_from", DESCENDING)' in runtime_source
    assert '("recorded_at", DESCENDING)' in runtime_source
    assert '("correlation_id", ASCENDING)' in runtime_source


class _FakeCursor:
    def __init__(self, docs):
        self._docs = list(docs)
        self._sort_key = None
        self._sort_direction = 1

    def sort(self, key, direction):
        self._sort_key = key
        self._sort_direction = direction
        return self

    async def to_list(self, length=None):
        docs = list(self._docs)
        if self._sort_key:
            docs.sort(
                key=lambda item: item.get(self._sort_key) or 0,
                reverse=self._sort_direction < 0,
            )
        return docs[:length] if length is not None else docs


class _FakeCollection:
    def __init__(self, docs=None):
        self.docs = list(docs or [])
        self.updated = []
        self.deleted_queries = []
        self.inserted_many = []

    @staticmethod
    def _value_matches(doc, key, expected):
        if "." not in key:
            return doc.get(key) == expected

        head, tail = key.split(".", 1)
        value = doc.get(head)
        if isinstance(value, list):
            return any(
                isinstance(item, dict) and _FakeCollection._value_matches(item, tail, expected)
                for item in value
            )
        if isinstance(value, dict):
            return _FakeCollection._value_matches(value, tail, expected)
        return False

    @staticmethod
    def _matches(doc, query):
        return all(_FakeCollection._value_matches(doc, key, value) for key, value in query.items())

    @staticmethod
    def _project(doc, projection):
        if not projection:
            return dict(doc)
        if all(value == 0 for value in projection.values()):
            return {key: value for key, value in doc.items() if projection.get(key) != 0}
        return {
            key: doc.get(key)
            for key, enabled in projection.items()
            if enabled and key in doc
        }

    def find(self, query, projection=None):
        return _FakeCursor(
            self._project(doc, projection)
            for doc in self.docs
            if self._matches(doc, query)
        )

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if self._matches(doc, query):
                return self._project(doc, projection)
        return None

    async def update_one(self, query, update, upsert=False):
        self.updated.append((query, update, upsert))
        for doc in self.docs:
            if self._matches(doc, query):
                doc.update(update.get("$set", {}))
                return
        if upsert:
            doc = dict(query)
            doc.update(update.get("$setOnInsert", {}))
            doc.update(update.get("$set", {}))
            self.docs.append(doc)

    async def delete_many(self, query):
        self.deleted_queries.append(query)
        self.docs = [doc for doc in self.docs if not self._matches(doc, query)]

    async def insert_many(self, docs):
        payload = [dict(doc) for doc in docs]
        self.inserted_many.append(payload)
        self.docs.extend(payload)


class _FakeDB:
    def __init__(self):
        self.service_book_record_streams = _FakeCollection()
        self.service_book_records = _FakeCollection()
        self.service_events = _FakeCollection()


@pytest.mark.asyncio
async def test_repository_persists_normalized_records_only() -> None:
    db = _FakeDB()
    repository = ServiceRecordRepository(db=db)

    await repository.upsert_stream(
        employee_id="EMP-1",
        document={
            "employee_id": "EMP-1",
            "events": [
                {
                    "service_event_id": "SE-2",
                    "event_type": "PROMOTION",
                    "payload": {"to_post": "SO"},
                    "date_range": {"effective_from": "2026-04-01", "effective_to": None},
                    "status": "DRAFT",
                    "created_at": "2026-04-01T10:00:00Z",
                    "updated_at": "2026-04-01T10:00:00Z",
                },
                {
                    "service_event_id": "SE-1",
                    "event_type": "INCREMENT",
                    "payload": {"increment_type": "annual"},
                    "date_range": {"effective_from": "2026-03-01", "effective_to": None},
                    "status": "APPROVED",
                    "created_at": "2026-03-01T10:00:00Z",
                    "updated_at": "2026-03-01T10:00:00Z",
                },
            ],
        },
    )

    assert db.service_book_record_streams.docs == [
        {
            "employee_id": "EMP-1",
            "event_count": 2,
            "updated_at": "2026-04-01T10:00:00Z",
        }
    ]
    assert db.service_book_records.deleted_queries == []
    assert [doc["service_event_id"] for doc in db.service_book_records.docs] == ["SE-2", "SE-1"]
    assert [doc["sequence"] for doc in db.service_book_records.docs] == [1, 2]
    assert db.service_book_records.docs[0]["effective_from"] == "2026-04-01"
    assert db.service_events.docs == []

    stream = await repository.get_stream("EMP-1")
    assert stream == {
        "employee_id": "EMP-1",
        "events": [
            {
                "service_event_id": "SE-2",
                "event_type": "PROMOTION",
                "payload": {"to_post": "SO"},
                "date_range": {"effective_from": "2026-04-01", "effective_to": None},
                "status": "DRAFT",
                "created_at": "2026-04-01T10:00:00Z",
                "updated_at": "2026-04-01T10:00:00Z",
            },
            {
                "service_event_id": "SE-1",
                "event_type": "INCREMENT",
                "payload": {"increment_type": "annual"},
                "date_range": {"effective_from": "2026-03-01", "effective_to": None},
                "status": "APPROVED",
                "created_at": "2026-03-01T10:00:00Z",
                "updated_at": "2026-03-01T10:00:00Z",
            },
        ],
    }


@pytest.mark.asyncio
async def test_repository_returns_none_when_normalized_records_absent() -> None:
    db = _FakeDB()
    db.service_events.docs.append(
        {
            "employee_id": "EMP-LEGACY",
            "events": [
                {
                    "service_event_id": "SE-LEGACY",
                    "event_type": "PROMOTION",
                    "payload": {},
                }
            ],
        }
    )
    repository = ServiceRecordRepository(db=db)

    stream = await repository.get_stream("EMP-LEGACY")
    event = await repository.get_event(service_event_id="SE-LEGACY")

    assert stream is None
    assert event is None


@pytest.mark.asyncio
async def test_repository_finds_normalized_stream_by_event_id() -> None:
    db = _FakeDB()
    db.service_book_records.docs.extend(
        [
            {"employee_id": "EMP-9", "sequence": 2, "service_event_id": "SE-B", "event_type": "PROMOTION"},
            {"employee_id": "EMP-9", "sequence": 1, "service_event_id": "SE-A", "event_type": "INCREMENT"},
        ]
    )
    repository = ServiceRecordRepository(db=db)

    stream = await repository.find_stream_by_event_id(service_event_id="SE-B")

    assert stream == {
        "employee_id": "EMP-9",
        "events": [
            {"service_event_id": "SE-A", "event_type": "INCREMENT"},
            {"service_event_id": "SE-B", "event_type": "PROMOTION"},
        ],
    }
