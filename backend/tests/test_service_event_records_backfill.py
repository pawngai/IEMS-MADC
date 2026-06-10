from __future__ import annotations

import pytest

from backend.scripts.mongodb.service_event_records_backfill_support import (
    MIGRATION_MARKER,
    backfill_service_event_records,
    verify_service_event_records_cutover,
)


class _FakeCursor:
    def __init__(self, docs):
        self._docs = list(docs)

    def __aiter__(self):
        self._index = 0
        return self

    async def __anext__(self):
        if self._index >= len(self._docs):
            raise StopAsyncIteration
        item = self._docs[self._index]
        self._index += 1
        return item


class _FakeCollection:
    def __init__(self, docs=None, *, index_info=None):
        self.docs = list(docs or [])
        self._index_info = dict(index_info or {})
        self.updated = []
        self.inserted_many = []

    @staticmethod
    def _matches(doc, query):
        return all(doc.get(key) == value for key, value in query.items())

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
            doc.update(update.get("$set", {}))
            self.docs.append(doc)

    async def insert_many(self, docs):
        payload = [dict(doc) for doc in docs]
        self.inserted_many.append(payload)
        self.docs.extend(payload)

    async def index_information(self):
        return dict(self._index_info)


class _FakeDB:
    def __init__(
        self,
        *,
        legacy_streams=None,
        streams=None,
        records=None,
        record_index_info=None,
        stream_index_info=None,
    ):
        self.service_events = _FakeCollection(legacy_streams)
        self.service_event_streams = _FakeCollection(streams, index_info=stream_index_info)
        self.service_event_records = _FakeCollection(records, index_info=record_index_info)

    def __getitem__(self, name):
        return getattr(self, name)


def _legacy_stream(employee_id="EMP-1"):
    return {
        "employee_id": employee_id,
        "events": [
            {
                "service_event_id": "SE-1",
                "event_type": "PROMOTION",
                "payload": {"to_post": "SO"},
                "date_range": {"effective_from": "2026-04-01", "effective_to": None},
                "status": "APPROVED",
                "created_at": "2026-04-01T10:00:00Z",
                "updated_at": "2026-04-01T11:00:00Z",
            },
            {
                "service_event_id": "SE-2",
                "event_type": "INCREMENT",
                "payload": {"increment_type": "annual"},
                "date_range": {"effective_from": "2026-05-01", "effective_to": None},
                "status": "DRAFT",
                "created_at": "2026-05-01T10:00:00Z",
                "updated_at": "2026-05-01T10:00:00Z",
            },
        ],
    }


@pytest.mark.asyncio
async def test_backfill_service_event_records_dry_run_does_not_write() -> None:
    db = _FakeDB(legacy_streams=[_legacy_stream()])

    summary = await backfill_service_event_records(db, dry_run=True)

    assert summary["dry_run"] is True
    assert summary["streams_scanned"] == 1
    assert summary["events_found"] == 2
    assert summary["records_written"] == 2
    assert summary["stream_metadata_written"] == 1
    assert db.service_event_records.docs == []
    assert db.service_event_streams.docs == []


@pytest.mark.asyncio
async def test_backfill_service_event_records_writes_normalized_rows() -> None:
    db = _FakeDB(legacy_streams=[_legacy_stream()])

    summary = await backfill_service_event_records(db, dry_run=False)

    assert summary["records_written"] == 2
    assert db.service_event_streams.docs == [
        {
            "employee_id": "EMP-1",
            "event_count": 2,
            "updated_at": "2026-05-01T10:00:00Z",
            "migration_marker": MIGRATION_MARKER,
        }
    ]
    assert [doc["service_event_id"] for doc in db.service_event_records.docs] == ["SE-1", "SE-2"]
    assert [doc["sequence"] for doc in db.service_event_records.docs] == [1, 2]
    assert db.service_event_records.docs[0]["effective_from"] == "2026-04-01"
    assert db.service_event_records.docs[0]["migration_marker"] == MIGRATION_MARKER


@pytest.mark.asyncio
async def test_backfill_service_event_records_skips_existing_records() -> None:
    db = _FakeDB(
        legacy_streams=[_legacy_stream()],
        records=[{"service_event_id": "SE-1", "employee_id": "EMP-1"}],
    )

    summary = await backfill_service_event_records(db, dry_run=False)

    assert summary["records_written"] == 1
    assert summary["skipped_existing_records"] == 1
    assert db.service_event_streams.docs[0]["event_count"] == 2
    assert [doc["service_event_id"] for doc in db.service_event_records.docs] == ["SE-1", "SE-2"]


@pytest.mark.asyncio
async def test_backfill_service_event_records_updates_stream_metadata_when_records_exist() -> None:
    db = _FakeDB(
        legacy_streams=[_legacy_stream()],
        records=[
            {"service_event_id": "SE-1", "employee_id": "EMP-1"},
            {"service_event_id": "SE-2", "employee_id": "EMP-1"},
        ],
    )

    summary = await backfill_service_event_records(db, dry_run=False)

    assert summary["records_written"] == 0
    assert summary["skipped_existing_records"] == 2
    assert summary["stream_metadata_written"] == 1
    assert db.service_event_streams.docs[0]["event_count"] == 2


@pytest.mark.asyncio
async def test_backfill_service_event_records_skips_duplicate_and_missing_event_ids() -> None:
    stream = _legacy_stream()
    stream["events"].append({"service_event_id": "SE-2", "event_type": "PROMOTION"})
    stream["events"].append({"event_type": "PROMOTION"})
    db = _FakeDB(legacy_streams=[stream])

    summary = await backfill_service_event_records(db, dry_run=False)

    assert summary["events_found"] == 4
    assert summary["records_written"] == 2
    assert summary["skipped_duplicate_event_ids"] == 1
    assert summary["skipped_missing_event_id"] == 1


@pytest.mark.asyncio
async def test_backfill_service_event_records_filters_by_employee_id() -> None:
    db = _FakeDB(legacy_streams=[_legacy_stream("EMP-1"), _legacy_stream("EMP-2")])

    summary = await backfill_service_event_records(db, dry_run=False, employee_id="EMP-2")

    assert summary["employee_filter"] == "EMP-2"
    assert summary["streams_scanned"] == 1
    assert db.service_event_streams.docs[0]["employee_id"] == "EMP-2"


@pytest.mark.asyncio
async def test_verify_service_event_records_cutover_passes_when_normalized_state_matches_legacy() -> None:
    db = _FakeDB(
        legacy_streams=[_legacy_stream()],
        streams=[{"employee_id": "EMP-1", "event_count": 2}],
        records=[
            {"employee_id": "EMP-1", "sequence": 1, "service_event_id": "SE-1"},
            {"employee_id": "EMP-1", "sequence": 2, "service_event_id": "SE-2"},
        ],
        record_index_info={
            "service_event_id_1": {"key": [("service_event_id", 1)], "unique": True},
        },
        stream_index_info={
            "employee_id_1": {"key": [("employee_id", 1)], "unique": True},
        },
    )

    result = await verify_service_event_records_cutover(db)

    assert result["ok"] is True
    assert all(result["checks"].values())
    assert result["legacy_event_count"] == 2
    assert result["normalized_record_count"] == 2
    assert result["missing_record_event_ids"] == []
    assert result["orphan_record_event_ids"] == []


@pytest.mark.asyncio
async def test_verify_service_event_records_cutover_reports_failed_checks() -> None:
    legacy_stream = _legacy_stream()
    legacy_stream["events"].append({"service_event_id": "SE-2", "event_type": "TRANSFER"})
    legacy_stream["events"].append({"event_type": "PROMOTION"})
    db = _FakeDB(
        legacy_streams=[legacy_stream],
        streams=[{"employee_id": "EMP-1", "event_count": 1}],
        records=[
            {"employee_id": "EMP-1", "sequence": 1, "service_event_id": "SE-1"},
            {"employee_id": "EMP-X", "sequence": 1, "service_event_id": "SE-ORPHAN"},
            {"employee_id": "EMP-X", "sequence": 2, "service_event_id": "SE-ORPHAN"},
        ],
        record_index_info={"service_event_id_1": {"key": [("service_event_id", 1)]}},
        stream_index_info={"employee_id_1": {"key": [("employee_id", 1)]}},
    )

    result = await verify_service_event_records_cutover(db)

    assert result["ok"] is False
    assert result["checks"]["all_legacy_events_backfilled"] is False
    assert result["checks"]["no_orphan_normalized_records"] is False
    assert result["checks"]["legacy_event_ids_unique"] is False
    assert result["checks"]["normalized_event_ids_unique"] is False
    assert result["checks"]["legacy_events_have_ids"] is False
    assert result["checks"]["stream_metadata_counts_match"] is False
    assert result["checks"]["record_service_event_id_unique_index"] is False
    assert result["checks"]["stream_employee_id_unique_index"] is False
    assert result["missing_record_event_ids"] == ["SE-2"]
    assert result["orphan_record_event_ids"] == ["SE-ORPHAN"]

