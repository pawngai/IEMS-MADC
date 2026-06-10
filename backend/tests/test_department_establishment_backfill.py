from __future__ import annotations

import pytest

from scripts.mongodb.department_establishment_backfill_support import (
    CLEANUP_MARKER,
    MIGRATION_MARKER,
    backfill_department_establishments,
    build_establishment_document,
    cleanup_legacy_department_establishment_metadata,
)


def test_build_establishment_document_normalizes_legacy_rows() -> None:
    document = build_establishment_document(
        {
            "code": "fin",
            "created_at": "2026-03-01T00:00:00+00:00",
            "updated_at": "2026-03-10T00:00:00+00:00",
            "updated_by": "admin@madc.gov.in",
            "metadata": {
                "sanctioned_strength": [
                    {
                        "designation_code": "so",
                        "employment_type": None,
                        "sanctioned_count": 5,
                        "order_number": "12/2026",
                        "order_date": "2026-04-01",
                        "remarks": "Revised",
                    }
                ]
            },
        },
        migrated_at="2026-04-04T00:00:00+00:00",
    )

    assert document["department_code"] == "FIN"
    assert document["items"] == [
        {
            "designation_code": "SO",
            "employment_type": None,
            "sanctioned_count": 5,
            "order_number": "12/2026",
            "order_date": "2026-04-01",
            "remarks": "Revised",
        }
    ]
    assert document["created_at"] == "2026-03-10T00:00:00+00:00"
    assert document["created_by"] == "admin@madc.gov.in"
    assert document["updated_at"] == "2026-04-04T00:00:00+00:00"
    assert document["updated_by"] == "migration-script"
    assert document["migration_marker"] == MIGRATION_MARKER


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


class _FakeCollection:
    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.inserted = []

    def find(self, query, projection=None):
        code = query.get("code")
        if code:
            rows = [row for row in self.rows if row.get("code") == code]
        else:
            rows = list(self.rows)
        return _FakeAsyncCursor(rows)

    async def find_one(self, query, projection=None):
        if "department_code" in query:
            for row in self.rows:
                if row.get("department_code") == query["department_code"]:
                    return dict(row)
            return None
        if "code" in query:
            for row in self.rows:
                if row.get("code") == query["code"]:
                    return dict(row)
            return None
        return None

    async def replace_one(self, query, document, upsert=False):
        for index, row in enumerate(self.rows):
            if row.get("department_code") == query.get("department_code"):
                self.rows[index] = dict(document)
                return
        if upsert:
            self.rows.append(dict(document))

    async def update_one(self, query, update):
        for index, row in enumerate(self.rows):
            if row.get("code") == query.get("code"):
                next_row = dict(row)
                unset_fields = (update or {}).get("$unset") or {}
                if "metadata.sanctioned_strength" in unset_fields:
                    metadata = dict(next_row.get("metadata") or {})
                    metadata.pop("sanctioned_strength", None)
                    next_row["metadata"] = metadata
                self.rows[index] = next_row
                return

    async def insert_one(self, document):
        self.inserted.append(dict(document))


class _FakeDb:
    def __init__(self):
        self.departments = _FakeCollection(
            [
                {
                    "code": "FIN",
                    "updated_at": "2026-04-01T00:00:00+00:00",
                    "updated_by": "system@madc.gov.in",
                    "metadata": {
                        "sanctioned_strength": [
                            {
                                "designation_code": "SO",
                                "employment_type": None,
                                "sanctioned_count": 5,
                            }
                        ]
                    },
                },
                {
                    "code": "HR",
                    "metadata": {},
                },
            ]
        )
        self.department_establishments = _FakeCollection([])
        self.department_establishment_logs = _FakeCollection([])


@pytest.mark.asyncio
async def test_backfill_department_establishments_writes_only_configured_departments() -> None:
    db = _FakeDb()

    result = await backfill_department_establishments(db, dry_run=False, overwrite=False)

    assert result["departments_scanned"] == 2
    assert result["departments_backfilled"] == 1
    assert result["establishments_written"] == 1
    assert result["logs_written"] == 1
    assert result["skipped_empty"] == 1
    assert result["skipped_existing"] == 0
    assert result["errors"] == []
    assert db.department_establishments.rows[0]["department_code"] == "FIN"
    assert db.department_establishments.rows[0]["items"][0]["designation_code"] == "SO"
    assert db.department_establishment_logs.inserted[0]["department_code"] == "FIN"
    assert db.department_establishment_logs.inserted[0]["migration_marker"] == MIGRATION_MARKER


@pytest.mark.asyncio
async def test_cleanup_legacy_department_establishment_metadata_removes_matching_legacy_rows() -> None:
    db = _FakeDb()
    await backfill_department_establishments(db, dry_run=False, overwrite=False)

    result = await cleanup_legacy_department_establishment_metadata(
        db,
        dry_run=False,
        force=False,
    )

    assert result["departments_scanned"] == 2
    assert result["departments_cleaned"] == 1
    assert result["departments_updated"] == 1
    assert result["logs_written"] == 1
    assert result["skipped_empty"] == 1
    assert result["skipped_missing_establishment"] == 0
    assert result["skipped_mismatch"] == 0
    assert result["errors"] == []
    assert "sanctioned_strength" not in (db.departments.rows[0].get("metadata") or {})
    assert db.department_establishment_logs.inserted[-1]["migration_marker"] == CLEANUP_MARKER


@pytest.mark.asyncio
async def test_cleanup_legacy_department_establishment_metadata_skips_mismatch_without_force() -> None:
    db = _FakeDb()
    db.department_establishments.rows.append(
        {
            "department_code": "FIN",
            "items": [
                {
                    "designation_code": "SO",
                    "employment_type": None,
                    "sanctioned_count": 9,
                }
            ],
        }
    )

    result = await cleanup_legacy_department_establishment_metadata(
        db,
        dry_run=False,
        force=False,
    )

    assert result["departments_cleaned"] == 0
    assert result["skipped_mismatch"] == 1
    assert "sanctioned_strength" in (db.departments.rows[0].get("metadata") or {})