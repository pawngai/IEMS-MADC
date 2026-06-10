from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts.mongodb.service_book_msgegis_cleanup_support import (
    MIGRATION_MARKER,
    cleanup_service_book_msgegis_data,
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

    async def delete_one(self, query):
        for index, row in enumerate(self.docs):
            if all(row.get(key) == value for key, value in query.items()):
                del self.docs[index]
                return SimpleNamespace(deleted_count=1)
        return SimpleNamespace(deleted_count=0)


class _FakeDb:
    def __init__(self):
        self.service_book_entries = _FakeCollection(
            [
                {
                    "entry_id": "entry-delete",
                    "employee_id": "EMP-1",
                    "schema_key": "SB_IIB_MSGEGIS_NOMINATION_ROW",
                    "payload": {"msgegis_nomination": [{"name": "Nominee"}]},
                },
                {
                    "entry_id": "entry-update",
                    "employee_id": "EMP-1",
                    "schema_key": "SB_IIB_FAMILY_SHEET",
                    "payload": {
                        "family_members": [{"name": "Alice"}],
                        "msgegis_nomination": [{"name": "Nominee"}],
                        "msgegis_nomination_date": "2026-01-01",
                        "msgegis_policy_number": "MSG-100",
                        "insurance_nominee_name": "Nominee",
                    },
                    "fields_changed": [
                        "family_members",
                        "msgegis_nomination",
                        "msgegis_nomination_date",
                        "msgegis_policy_number",
                    ],
                },
                {
                    "entry_id": "entry-keep",
                    "employee_id": "EMP-2",
                    "schema_key": "SB_IIB_NPS_PRAN",
                    "payload": {"nps_pran_number": "NPS-200"},
                },
            ]
        )
        self.service_book_workflow_entries = _FakeCollection(
            [
                {
                    "id": "wf-delete",
                    "employee_id": "EMP-1",
                    "schema_key": "SB_PART_VII_MSGEGIS_ROW",
                    "payload": {"policy_number": "MSG-100"},
                }
            ]
        )
        self.service_book_part_projections = _FakeCollection(
            [
                {
                    "employee_id": "EMP-1",
                    "part_code": "II-B",
                    "msgegis_nomination": [{"name": "Nominee"}],
                    "msgegis_policy_number": "MSG-100",
                    "insurance_nominee_name": "Nominee",
                    "schema_keys": [
                        "SB_IIB_FAMILY_SHEET",
                        "SB_IIB_MSGEGIS_NOMINATION_ROW",
                        "SB_IIB_MSGEGIS_POLICY",
                    ],
                },
                {
                    "employee_id": "EMP-1",
                    "part_code": "VII",
                    "msgegis_records": [{"policy_number": "MSG-100"}],
                    "schema_keys": ["SB_VII_LTC_ROW", "SB_VII_MSGEGIS_ROW"],
                },
            ]
        )
        self.service_book_openings = _FakeCollection(
            [
                {
                    "employee_id": "EMP-1",
                    "part_iib": {
                        "msgegis_nomination": [{"name": "Nominee"}],
                        "msgegis_policy_number": "MSG-100",
                        "insurance_nominee_relation": "SPOUSE",
                        "nps_pran_number": "NPS-100",
                    },
                    "parts": {
                        "part_iib": {
                            "msgegis_nomination": [{"name": "Nominee"}],
                            "msgegis_policy_number": "MSG-100",
                            "insurance_nominee_share_percent": 100,
                            "bank_name": "Bank",
                        }
                    },
                }
            ]
        )

    def __getitem__(self, name):
        return getattr(self, name)


@pytest.mark.asyncio
async def test_service_book_msgegis_cleanup_dry_run_reports_deletes_and_updates() -> None:
    db = _FakeDb()

    summary = await cleanup_service_book_msgegis_data(db, dry_run=True)

    assert summary["dry_run"] is True
    assert summary["migration_marker"] == MIGRATION_MARKER
    assert summary["collections"]["service_book_entries"] == {
        "scanned": 3,
        "would_delete": 1,
        "deleted": 0,
        "would_update": 1,
        "updated": 0,
    }
    assert summary["collections"]["service_book_workflow_entries"] == {
        "scanned": 1,
        "would_delete": 1,
        "deleted": 0,
        "would_update": 0,
        "updated": 0,
    }
    assert summary["collections"]["service_book_part_projections"] == {
        "scanned": 2,
        "would_delete": 0,
        "deleted": 0,
        "would_update": 2,
        "updated": 0,
    }
    assert summary["collections"]["service_book_openings"] == {
        "scanned": 1,
        "would_delete": 0,
        "deleted": 0,
        "would_update": 1,
        "updated": 0,
    }
    assert db.service_book_entries.docs[0]["schema_key"] == "SB_IIB_MSGEGIS_NOMINATION_ROW"


@pytest.mark.asyncio
async def test_service_book_msgegis_cleanup_apply_removes_historical_data() -> None:
    db = _FakeDb()

    summary = await cleanup_service_book_msgegis_data(db, dry_run=False)

    assert summary["collections"]["service_book_entries"]["deleted"] == 1
    assert summary["collections"]["service_book_entries"]["updated"] == 1
    assert summary["collections"]["service_book_workflow_entries"]["deleted"] == 1
    assert summary["collections"]["service_book_part_projections"]["updated"] == 2
    assert summary["collections"]["service_book_openings"]["updated"] == 1

    remaining_entry_ids = {doc.get("entry_id") for doc in db.service_book_entries.docs}
    assert "entry-delete" not in remaining_entry_ids

    updated_entry = next(doc for doc in db.service_book_entries.docs if doc.get("entry_id") == "entry-update")
    assert updated_entry["payload"] == {"family_members": [{"name": "Alice"}]}
    assert updated_entry["fields_changed"] == ["family_members"]

    assert db.service_book_workflow_entries.docs == []

    part_iib_projection = next(doc for doc in db.service_book_part_projections.docs if doc.get("part_code") == "II-B")
    assert part_iib_projection["schema_keys"] == ["SB_IIB_FAMILY_SHEET"]
    assert "msgegis_nomination" not in part_iib_projection
    assert "msgegis_policy_number" not in part_iib_projection
    assert "insurance_nominee_name" not in part_iib_projection

    part_vii_projection = next(doc for doc in db.service_book_part_projections.docs if doc.get("part_code") == "VII")
    assert part_vii_projection["schema_keys"] == ["SB_VII_LTC_ROW"]
    assert "msgegis_records" not in part_vii_projection

    opening = db.service_book_openings.docs[0]
    assert opening["part_iib"] == {"nps_pran_number": "NPS-100"}
    assert opening["parts"]["part_iib"] == {"bank_name": "Bank"}