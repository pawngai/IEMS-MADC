from __future__ import annotations

from types import SimpleNamespace
from argparse import Namespace

import pytest

from scripts.mongodb.cleanup_service_book_truth_boundary import validate_args
from scripts.mongodb.service_book_truth_boundary_cleanup_support import (
    MIGRATION_MARKER,
    cleanup_service_book_truth_boundary,
    sanitized_service_book_truth_payload,
)


class _FakeCursor:
    def __init__(self, docs):
        self._docs = list(docs)
        self._index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._index >= len(self._docs):
            raise StopAsyncIteration
        item = self._docs[self._index]
        self._index += 1
        return dict(item)


class _FakeCollection:
    def __init__(self, docs):
        self.docs = list(docs)

    def find(self, query, projection=None):
        rows = [
            row
            for row in self.docs
            if not query or all(row.get(key) == value for key, value in query.items())
        ]
        return _FakeCursor(rows)

    async def delete_one(self, query):
        for index, row in enumerate(self.docs):
            if all(row.get(key) == value for key, value in query.items()):
                self.docs.pop(index)
                return SimpleNamespace(deleted_count=1)
        return SimpleNamespace(deleted_count=0)

    async def update_one(self, query, update):
        for index, row in enumerate(self.docs):
            if all(row.get(key) == value for key, value in query.items()):
                next_row = dict(row)
                next_row.update((update or {}).get("$set") or {})
                self.docs[index] = next_row
                return SimpleNamespace(modified_count=1)
        return SimpleNamespace(modified_count=0)


class _FakeDb:
    def __init__(self):
        self.service_book_entries = _FakeCollection(
            [
                {
                    "entry_id": "legacy-recorded",
                    "employee_id": "EMP-1",
                    "event_name": "ServiceEventRecorded",
                    "payload": {"post_held": "Assistant", "document_ids": ["DOC-1"]},
                },
                {
                    "entry_id": "approved-dirty",
                    "employee_id": "EMP-1",
                    "event_name": "ServiceEventLifecycleApproved",
                    "payload": {
                        "post_held": "Section Officer",
                        "documents": [{"document_id": "DOC-2"}],
                        "workflow_state": "APPROVED",
                    },
                },
                {
                    "entry_id": "approved-clean",
                    "employee_id": "EMP-1",
                    "event_name": "ServiceEventLifecycleApproved",
                    "payload": {"post_held": "Deputy Secretary"},
                },
            ]
        )

    def __getitem__(self, name):
        return getattr(self, name)


def test_sanitized_service_book_truth_payload_removes_documents_and_workflow() -> None:
    assert sanitized_service_book_truth_payload(
        {
            "post_held": "SO",
            "documents": [{"document_id": "DOC-1"}],
            "nested": {"workflow_payload": {"approved_by": "A"}, "remarks": "ok"},
        }
    ) == {"post_held": "SO", "nested": {"remarks": "ok"}}


def test_cleanup_cli_apply_requires_selected_operation() -> None:
    with pytest.raises(ValueError, match="--apply requires"):
        validate_args(
            Namespace(apply=True, delete_non_truth=False, sanitize_payloads=False),
            parser=None,
        )


def test_cleanup_cli_dry_run_allows_no_operation_flags() -> None:
    validate_args(
        Namespace(apply=False, delete_non_truth=False, sanitize_payloads=False),
        parser=None,
    )


@pytest.mark.asyncio
async def test_cleanup_service_book_truth_boundary_dry_run_classifies_legacy_rows() -> None:
    db = _FakeDb()

    summary = await cleanup_service_book_truth_boundary(db, dry_run=True)

    assert summary["dry_run"] is True
    assert summary["migration_marker"] == MIGRATION_MARKER
    assert summary["entries_scanned"] == 3
    assert summary["candidate_entries"] == 2
    assert summary["would_delete"] == 1
    assert summary["would_sanitize"] == 1
    assert len(db.service_book_entries.docs) == 3


@pytest.mark.asyncio
async def test_cleanup_service_book_truth_boundary_apply_deletes_and_sanitizes() -> None:
    db = _FakeDb()

    summary = await cleanup_service_book_truth_boundary(
        db,
        dry_run=False,
        delete_non_truth=True,
        sanitize_payloads=True,
    )

    assert summary["deleted"] == 1
    assert summary["sanitized"] == 1
    entries_by_id = {entry["entry_id"]: entry for entry in db.service_book_entries.docs}
    assert set(entries_by_id) == {"approved-dirty", "approved-clean"}
    assert entries_by_id["approved-dirty"]["payload"] == {"post_held": "Section Officer"}
    assert entries_by_id["approved-dirty"]["truth_boundary_cleanup_marker"] == MIGRATION_MARKER