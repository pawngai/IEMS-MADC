from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts.mongodb.employee_code_migration_support import (
    MIGRATION_MARKER,
    build_employee_code_migration_plan,
    migrate_employee_codes_to_madc_format,
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


def _matches_condition(value, condition):
    if isinstance(condition, dict):
        if "$in" in condition:
            return value in condition["$in"]
        return False
    return value == condition


def _matches_query(row, query):
    if not query:
        return True
    if "$or" in query:
        return any(_matches_query(row, part) for part in query["$or"])
    for key, value in query.items():
        if key == "$or":
            continue
        if not _matches_condition(row.get(key), value):
            return False
    return True


class _FakeCollection:
    def __init__(self, rows=None):
        self.rows = list(rows or [])

    def find(self, query, projection=None):
        return _FakeAsyncCursor([dict(row) for row in self.rows if _matches_query(row, query)])

    async def update_one(self, query, update, upsert=False):
        for index, row in enumerate(self.rows):
            if not _matches_query(row, query):
                continue
            next_row = dict(row)
            next_row.update(update.get("$set", {}))
            self.rows[index] = next_row
            return SimpleNamespace(matched_count=1, modified_count=1, upserted_id=None)

        if upsert:
            next_row = dict(query)
            next_row.update(update.get("$set", {}))
            self.rows.append(next_row)
            return SimpleNamespace(matched_count=0, modified_count=0, upserted_id=query.get("_id"))

        return SimpleNamespace(matched_count=0, modified_count=0, upserted_id=None)

    async def update_many(self, query, update):
        modified = 0
        for index, row in enumerate(self.rows):
            if not _matches_query(row, query):
                continue
            next_row = dict(row)
            next_row.update(update.get("$set", {}))
            self.rows[index] = next_row
            modified += 1
        return SimpleNamespace(modified_count=modified, matched_count=modified)


class _FakeDb:
    def __init__(self):
        self.employee_identities = _FakeCollection(
            [
                {
                    "employee_id": "EMP-2",
                    "employee_code": "EMP-2026-R0002",
                    "employment_type": "CONTRACTUAL",
                    "date_of_initial_engagement": "2020-06-01",
                    "created_at": "2026-01-03T00:00:00+00:00",
                },
                {
                    "employee_id": "EMP-1",
                    "employee_code": "MADC-2020-0001",
                    "employment_type": "REGULAR",
                    "date_of_initial_engagement": "2020-04-01",
                    "created_at": "2026-01-02T00:00:00+00:00",
                },
                {
                    "employee_id": "EMP-3",
                    "employee_code": "EMP-2026-D0003",
                    "employment_type": "DAILY_WAGE",
                    "date_of_initial_engagement": "2021-01-10",
                    "created_at": "2026-01-04T00:00:00+00:00",
                },
            ]
        )
        self.employee_profile_read_models = _FakeCollection(
            [
                {"employee_id": "EMP-1", "employee_code": "MADC-2020-0001"},
                {"employee_id": "EMP-2", "employee_code": "EMP-2026-R0002"},
                {"employee_id": "EMP-3", "employee_code": "EMP-2026-D0003"},
            ]
        )
        self.employee_profiles = _FakeCollection(
            [
                {"employee_id": "EMP-2", "employee_code": "EMP-2026-R0002"},
                {"employee_id": "EMP-3", "employee_code": "EMP-2026-D0003"},
            ]
        )
        self.document_metadata = _FakeCollection(
            [
                {
                    "filename": "doc-1.pdf",
                    "uploaded_employee_id": "EMP-2",
                    "uploaded_employee_code": "EMP-2026-R0002",
                },
                {
                    "filename": "doc-2.pdf",
                    "uploaded_employee_id": "",
                    "uploaded_employee_code": "EMP-2026-R0002",
                },
                {
                    "filename": "doc-3.pdf",
                    "uploaded_employee_id": "EMP-1",
                    "uploaded_employee_code": "MADC-2020-0001",
                },
            ]
        )
        self.counters = _FakeCollection([])

    def __getitem__(self, name: str):
        return getattr(self, name)


def test_build_employee_code_migration_plan_assigns_year_scoped_codes() -> None:
    plan = build_employee_code_migration_plan(
        [
            {
                "employee_id": "EMP-2",
                "employee_code": "EMP-2026-R0002",
                "employment_type": "CONTRACTUAL",
                "date_of_initial_engagement": "2020-06-01",
                "created_at": "2026-01-03T00:00:00+00:00",
            },
            {
                "employee_id": "EMP-1",
                "employee_code": "EMP-2026-R0001",
                "employment_type": "REGULAR",
                "date_of_initial_engagement": "2020-04-01",
                "created_at": "2026-01-02T00:00:00+00:00",
            },
            {
                "employee_id": "EMP-3",
                "employee_code": "EMP-2026-D0003",
                "employment_type": "DAILY_WAGE",
                "date_of_initial_engagement": "2021-01-10",
                "created_at": "2026-01-04T00:00:00+00:00",
            },
        ]
    )

    assert plan["employees"] == [
        {
            "employee_id": "EMP-1",
            "appointment_year": 2020,
            "date_of_initial_engagement": "2020-04-01",
            "old_code": "EMP-2026-R0001",
            "new_code": "MADC-2020-R0001",
            "changed": True,
        },
        {
            "employee_id": "EMP-2",
            "appointment_year": 2020,
            "date_of_initial_engagement": "2020-06-01",
            "old_code": "EMP-2026-R0002",
            "new_code": "MADC-2020-C0002",
            "changed": True,
        },
        {
            "employee_id": "EMP-3",
            "appointment_year": 2021,
            "date_of_initial_engagement": "2021-01-10",
            "old_code": "EMP-2026-D0003",
            "new_code": "MADC-2021-D0001",
            "changed": True,
        },
    ]
    assert plan["years"] == [
        {"year": 2020, "count": 2, "counter_id": "employee_code:2020"},
        {"year": 2021, "count": 1, "counter_id": "employee_code:2021"},
    ]
    assert plan["errors"] == []


@pytest.mark.asyncio
async def test_migrate_employee_codes_updates_dependent_collections_and_counters() -> None:
    db = _FakeDb()

    summary = await migrate_employee_codes_to_madc_format(db, dry_run=False)

    assert summary["identities_scanned"] == 3
    assert summary["identities_needing_update"] == 3
    assert summary["identity_rows_updated"] == 3
    assert summary["read_models_updated"] == 3
    assert summary["legacy_profiles_updated"] == 2
    assert summary["document_metadata_updated"] == 3
    assert summary["counters_updated"] == 2

    identity_by_id = {row["employee_id"]: row for row in db.employee_identities.rows}
    assert identity_by_id["EMP-1"]["employee_code"] == "MADC-2020-R0001"
    assert identity_by_id["EMP-2"]["employee_code"] == "MADC-2020-C0002"
    assert identity_by_id["EMP-2"]["employee_code_migration_marker"] == MIGRATION_MARKER
    assert identity_by_id["EMP-3"]["employee_code"] == "MADC-2021-D0001"

    read_model_by_id = {row["employee_id"]: row for row in db.employee_profile_read_models.rows}
    assert read_model_by_id["EMP-1"]["employee_code"] == "MADC-2020-R0001"
    assert read_model_by_id["EMP-2"]["employee_code"] == "MADC-2020-C0002"
    assert read_model_by_id["EMP-3"]["employee_code"] == "MADC-2021-D0001"

    legacy_by_id = {row["employee_id"]: row for row in db.employee_profiles.rows}
    assert legacy_by_id["EMP-2"]["employee_code"] == "MADC-2020-C0002"
    assert legacy_by_id["EMP-3"]["employee_code"] == "MADC-2021-D0001"

    metadata_by_filename = {row["filename"]: row for row in db.document_metadata.rows}
    assert metadata_by_filename["doc-1.pdf"]["uploaded_employee_code"] == "MADC-2020-C0002"
    assert metadata_by_filename["doc-2.pdf"]["uploaded_employee_code"] == "MADC-2020-C0002"
    assert metadata_by_filename["doc-3.pdf"]["uploaded_employee_code"] == "MADC-2020-R0001"

    counters_by_id = {row["_id"]: row for row in db.counters.rows}
    assert counters_by_id["employee_code:2020"]["seq"] == 2
    assert counters_by_id["employee_code:2021"]["seq"] == 1


@pytest.mark.asyncio
async def test_migrate_employee_codes_dry_run_leaves_data_unchanged() -> None:
    db = _FakeDb()

    summary = await migrate_employee_codes_to_madc_format(db, dry_run=True)

    assert summary["identities_needing_update"] == 3
    assert db.employee_identities.rows[0]["employee_code"] == "EMP-2026-R0002"
    assert db.employee_profile_read_models.rows[1]["employee_code"] == "EMP-2026-R0002"
    assert db.employee_profiles.rows[0]["employee_code"] == "EMP-2026-R0002"
    assert db.document_metadata.rows[0]["uploaded_employee_code"] == "EMP-2026-R0002"
    assert db.counters.rows == []