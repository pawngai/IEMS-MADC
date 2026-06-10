from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts.mongodb.service_book_pcf_cutover_support import (
    MIGRATION_MARKER,
    migrate_service_book_pcf_cutover,
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

    async def replace_one(self, query, replacement, upsert=False):
        for index, row in enumerate(self.docs):
            if all(row.get(key) == value for key, value in query.items()):
                self.docs[index] = dict(replacement)
                return SimpleNamespace(matched_count=1, modified_count=1, upserted_id=None)
        if upsert:
            self.docs.append(dict(replacement))
            return SimpleNamespace(matched_count=0, modified_count=0, upserted_id=query)
        return SimpleNamespace(matched_count=0, modified_count=0, upserted_id=None)


class _FakeDb:
    def __init__(self):
        self.service_book_entries = _FakeCollection(
            [
                {
                    "entry_id": "entry-1",
                    "employee_id": "EMP-1",
                    "schema_key": "SB_IIB_GPF_NOMINATION_ROW",
                    "payload": {
                        "gpf_account_number": "GPF-100",
                        "gpf_nomination": [{"name": "Nominee", "relationship": "SPOUSE", "share_percent": 100}],
                        "gpf_nomination_date": "2026-01-01",
                    },
                    "fields_changed": ["gpf_account_number", "gpf_nomination", "gpf_nomination_date"],
                },
                {
                    "entry_id": "entry-2",
                    "employee_id": "EMP-2",
                    "schema_key": "SB_IIB_PCF_NOMINATION_ROW",
                    "payload": {"pcf_account_number": "PCF-200"},
                    "fields_changed": ["pcf_account_number"],
                },
            ]
        )
        self.service_book_workflow_entries = _FakeCollection(
            [
                {
                    "id": "wf-1",
                    "employee_id": "EMP-1",
                    "schema_key": "SB_PART_IIB_GPF_NOMINATION_ROW",
                    "payload": {"gpf_account_number": "GPF-100"},
                }
            ]
        )
        self.service_book_part_projections = _FakeCollection(
            [
                {
                    "employee_id": "EMP-1",
                    "part_code": "II-B",
                    "gpf_account_number": "GPF-100",
                    "gpf_nomination": [{"name": "Nominee", "relationship": "SPOUSE", "share_percent": 100}],
                }
            ]
        )
        self.service_book_openings = _FakeCollection(
            [
                {
                    "employee_id": "EMP-1",
                    "parts": {
                        "part_iib": {
                            "gpf_account_number": "GPF-100",
                            "gpf_nomination": [{"name": "Nominee", "relationship": "SPOUSE", "share_percent": 100}],
                            "gpf_nomination_date": "2026-01-01",
                        }
                    },
                }
            ]
        )

    def __getitem__(self, name):
        return getattr(self, name)


@pytest.mark.asyncio
async def test_service_book_pcf_cutover_dry_run_reports_changed_documents() -> None:
    db = _FakeDb()

    summary = await migrate_service_book_pcf_cutover(db, dry_run=True)

    assert summary["dry_run"] is True
    assert summary["migration_marker"] == MIGRATION_MARKER
    assert summary["collections"]["service_book_entries"] == {"scanned": 2, "would_update": 1, "updated": 0}
    assert summary["collections"]["service_book_workflow_entries"] == {"scanned": 1, "would_update": 1, "updated": 0}
    assert summary["collections"]["service_book_part_projections"] == {"scanned": 1, "would_update": 1, "updated": 0}
    assert summary["collections"]["service_book_openings"] == {"scanned": 1, "would_update": 1, "updated": 0}
    assert db.service_book_entries.docs[0]["schema_key"] == "SB_IIB_GPF_NOMINATION_ROW"


@pytest.mark.asyncio
async def test_service_book_pcf_cutover_apply_rewrites_all_persisted_surfaces() -> None:
    db = _FakeDb()

    summary = await migrate_service_book_pcf_cutover(db, dry_run=False)

    assert summary["collections"]["service_book_entries"]["updated"] == 1
    assert summary["collections"]["service_book_workflow_entries"]["updated"] == 1
    assert summary["collections"]["service_book_part_projections"]["updated"] == 1
    assert summary["collections"]["service_book_openings"]["updated"] == 1

    migrated_entry = db.service_book_entries.docs[0]
    assert migrated_entry["schema_key"] == "SB_IIB_PCF_NOMINATION_ROW"
    assert migrated_entry["payload"] == {
        "pcf_account_number": "GPF-100",
        "pcf_nomination": [{"name": "Nominee", "relationship": "SPOUSE", "share_percent": 100}],
        "pcf_nomination_date": "2026-01-01",
    }
    assert migrated_entry["fields_changed"] == ["pcf_account_number", "pcf_nomination", "pcf_nomination_date"]

    migrated_workflow = db.service_book_workflow_entries.docs[0]
    assert migrated_workflow["schema_key"] == "SB_PART_IIB_PCF_NOMINATION_ROW"
    assert migrated_workflow["payload"] == {"pcf_account_number": "GPF-100"}

    migrated_projection = db.service_book_part_projections.docs[0]
    assert migrated_projection["pcf_account_number"] == "GPF-100"
    assert "gpf_account_number" not in migrated_projection
    assert "gpf_nomination" not in migrated_projection

    migrated_opening = db.service_book_openings.docs[0]
    assert migrated_opening["parts"]["part_iib"] == {
        "pcf_account_number": "GPF-100",
        "pcf_nomination": [{"name": "Nominee", "relationship": "SPOUSE", "share_percent": 100}],
        "pcf_nomination_date": "2026-01-01",
    }