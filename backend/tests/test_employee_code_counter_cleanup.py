from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts.mongodb.employee_code_migration_support import (
    cleanup_legacy_employee_code_counter,
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


class _FakeCollection:
    def __init__(self, rows=None):
        self.rows = list(rows or [])

    def find(self, _query, _projection=None):
        return _FakeAsyncCursor([dict(row) for row in self.rows])

    async def delete_one(self, query):
        deleted = 0
        next_rows = []
        for row in self.rows:
            if row.get("_id") == query.get("_id") and deleted == 0:
                deleted = 1
                continue
            next_rows.append(row)
        self.rows = next_rows
        return SimpleNamespace(deleted_count=deleted)


class _FakeDb:
    def __init__(self, rows=None):
        self.counters = _FakeCollection(rows)

    def __getitem__(self, name: str):
        return getattr(self, name)


@pytest.mark.asyncio
async def test_cleanup_legacy_employee_code_counter_dry_run_reports_deletion_candidate() -> None:
    db = _FakeDb(
        [
            {"_id": "employee_code", "seq": 556},
            {"_id": "employee_code:2024", "seq": 222},
            {"_id": "employee_code:2025", "seq": 80},
        ]
    )

    summary = await cleanup_legacy_employee_code_counter(db, dry_run=True)

    assert summary["legacy_counter_present"] is True
    assert summary["year_scoped_counter_count"] == 2
    assert summary["deleted"] is False
    assert summary["skip_reason"] is None
    assert any(row["_id"] == "employee_code" for row in db.counters.rows)


@pytest.mark.asyncio
async def test_cleanup_legacy_employee_code_counter_deletes_only_legacy_doc() -> None:
    db = _FakeDb(
        [
            {"_id": "employee_code", "seq": 556},
            {"_id": "employee_code:2020", "seq": 1},
            {"_id": "employee_code:2024", "seq": 222},
        ]
    )

    summary = await cleanup_legacy_employee_code_counter(db, dry_run=False)

    assert summary["deleted"] is True
    assert {row["_id"] for row in db.counters.rows} == {
        "employee_code:2020",
        "employee_code:2024",
    }


@pytest.mark.asyncio
async def test_cleanup_legacy_employee_code_counter_skips_without_year_scoped_counters() -> None:
    db = _FakeDb([
        {"_id": "employee_code", "seq": 556},
    ])

    summary = await cleanup_legacy_employee_code_counter(db, dry_run=False)

    assert summary["deleted"] is False
    assert summary["skip_reason"] == "year_scoped_counters_missing"
    assert {row["_id"] for row in db.counters.rows} == {"employee_code"}