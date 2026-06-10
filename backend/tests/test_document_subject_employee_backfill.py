from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts.mongodb.backfill_document_subject_employee_support import (
    MIGRATION_MARKER,
    backfill_document_subject_employee,
)


class _FakeAsyncCursor:
    def __init__(self, rows):
        self._rows = list(rows)
        self._index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._index >= len(self._rows):
            raise StopAsyncIteration
        value = self._rows[self._index]
        self._index += 1
        return value


def _extract_value(row, dotted_key: str):
    value = row
    for part in dotted_key.split("."):
        if isinstance(value, list):
            return [item.get(part) for item in value if isinstance(item, dict)]
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


class _FakeCollection:
    def __init__(self, rows=None):
        self.rows = list(rows or [])

    def find(self, query, projection=None):
        rows = list(self.rows)
        if query.get("document_id"):
            rows = [row for row in rows if row.get("document_id") == query["document_id"]]
        return _FakeAsyncCursor([dict(row) for row in rows])

    async def find_one(self, query, projection=None):
        for row in self.rows:
            match = True
            for key, value in query.items():
                current = _extract_value(row, key)
                if isinstance(current, list):
                    if value not in current:
                        match = False
                        break
                elif current != value:
                    match = False
                    break
            if not match:
                continue
            if projection:
                return {k: row.get(k) for k, include in projection.items() if include and k != "_id"}
            return dict(row)
        return None

    async def update_one(self, query, update):
        for index, row in enumerate(self.rows):
            if row.get("document_id") != query.get("document_id"):
                continue
            next_row = dict(row)
            next_row.update((update or {}).get("$set") or {})
            self.rows[index] = next_row
            return SimpleNamespace(matched_count=1, modified_count=1)
        return SimpleNamespace(matched_count=0, modified_count=0)


class _FakeDb:
    def __init__(self):
        self.document_metadata = _FakeCollection(
            [
                {
                    "document_id": "doc-with-code",
                    "filename": "doc-with-code.pdf",
                    "subject_employee_code": "MADC-2024-0001",
                },
                {
                    "document_id": "doc-service-event",
                    "filename": "doc-service-event.pdf",
                    "entity_type": "SERVICE_EVENT",
                    "entity_id": "SE-1",
                },
                {
                    "document_id": "doc-legacy-service-event-code",
                    "filename": "doc-legacy-service-event-code.pdf",
                    "entity_type": "SERVICE_EVENT",
                    "entity_id": "SE-2",
                    "subject_employee_code": "MADC-1993-0001",
                },
                {
                    "document_id": "doc-canonical",
                    "filename": "doc-canonical.pdf",
                    "subject_employee_id": "EMP-003",
                    "subject_employee_code": "MADC-2024-0003",
                },
                {
                    "document_id": "doc-unresolved",
                    "filename": "doc-unresolved.pdf",
                    "subject_employee_code": "MADC-2099-9999",
                },
            ]
        )
        self.service_events = _FakeCollection(
            [
                {
                    "employee_id": "EMP-002",
                    "events": [{"service_event_id": "SE-1"}],
                },
                {
                    "employee_id": "EMP-004",
                    "events": [{"service_event_id": "SE-2"}],
                }
            ]
        )
        self.employee_identities = _FakeCollection(
            [
                {
                    "employee_id": "EMP-001",
                    "employee_code": "MADC-2024-0001",
                },
                {
                    "employee_id": "EMP-002",
                    "employee_code": "MADC-2024-0002",
                },
                {
                    "employee_id": "EMP-003",
                    "employee_code": "MADC-2024-0003",
                },
                {
                    "employee_id": "EMP-004",
                    "employee_code": "MADC-1993-R0001",
                },
            ]
        )

    def __getitem__(self, name: str):
        return getattr(self, name)


@pytest.mark.asyncio
async def test_backfill_document_subject_employee_updates_code_and_service_event_docs() -> None:
    db = _FakeDb()

    summary = await backfill_document_subject_employee(db, dry_run=False)

    assert summary["documents_scanned"] == 5
    assert summary["candidate_documents"] == 4
    assert summary["documents_updated"] == 3
    assert summary["skipped_already_canonical"] == 1
    assert summary["skipped_unresolved_identity"] == 1
    assert summary["skipped_missing_service_event_stream"] == 0
    assert summary["skipped_no_subject_reference"] == 0

    documents = {row["document_id"]: row for row in db.document_metadata.rows}
    assert documents["doc-with-code"]["subject_employee_id"] == "EMP-001"
    assert documents["doc-with-code"]["subject_employee_code"] == "MADC-2024-0001"
    assert documents["doc-with-code"]["document_subject_employee_backfill_marker"] == MIGRATION_MARKER

    assert documents["doc-service-event"]["subject_employee_id"] == "EMP-002"
    assert documents["doc-service-event"]["subject_employee_code"] == "MADC-2024-0002"
    assert documents["doc-service-event"]["document_subject_employee_backfill_marker"] == MIGRATION_MARKER

    assert documents["doc-legacy-service-event-code"]["subject_employee_id"] == "EMP-004"
    assert documents["doc-legacy-service-event-code"]["subject_employee_code"] == "MADC-1993-R0001"
    assert documents["doc-legacy-service-event-code"]["document_subject_employee_backfill_marker"] == MIGRATION_MARKER

    assert "subject_employee_id" not in documents["doc-unresolved"]


@pytest.mark.asyncio
async def test_backfill_document_subject_employee_dry_run_leaves_rows_unchanged() -> None:
    db = _FakeDb()

    summary = await backfill_document_subject_employee(db, dry_run=True, document_id="doc-service-event")

    assert summary["documents_scanned"] == 1
    assert summary["candidate_documents"] == 1
    assert summary["documents_updated"] == 1
    assert summary["documents"][0]["action"] == "would_update"

    document = next(row for row in db.document_metadata.rows if row["document_id"] == "doc-service-event")
    assert "subject_employee_id" not in document
    assert "document_subject_employee_backfill_marker" not in document