from __future__ import annotations

import pytest

from scripts.mongodb.employee_code_migration_support import verify_employee_code_cutover


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
        if "$type" in condition and condition["$type"] == "string" and not isinstance(value, str):
            return False
        if "$ne" in condition and value == condition["$ne"]:
            return False
        if "$gt" in condition and not (value > condition["$gt"]):
            return False
        return True
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
    def __init__(self, rows=None, *, index_info=None):
        self.rows = list(rows or [])
        self._index_info = dict(index_info or {})

    def find(self, query, projection=None):
        rows = [dict(row) for row in self.rows if _matches_query(row, query)]
        return _FakeAsyncCursor(rows)

    def aggregate(self, pipeline):
        rows = [dict(row) for row in self.rows]
        for stage in pipeline:
            if "$match" in stage:
                rows = [row for row in rows if _matches_query(row, stage["$match"])]
            elif "$group" in stage:
                grouped = {}
                for row in rows:
                    key_field = stage["$group"]["_id"].lstrip("$")
                    key = row.get(key_field)
                    bucket = grouped.setdefault(key, {"_id": key, "count": 0, "employee_ids": []})
                    bucket["count"] += 1
                    bucket["employee_ids"].append(row.get("employee_id"))
                rows = list(grouped.values())
            elif "$sort" in stage:
                sort_items = list(stage["$sort"].items())
                rows.sort(
                    key=lambda row: tuple(
                        (-row[field] if direction < 0 and isinstance(row[field], int) else row[field])
                        for field, direction in sort_items
                    )
                )
            elif "$limit" in stage:
                rows = rows[: stage["$limit"]]
        return _FakeAsyncCursor(rows)

    async def index_information(self):
        return dict(self._index_info)


class _FakeDb:
    def __init__(self, *, identity_rows, read_model_rows, counter_rows, index_info):
        self.employee_identities = _FakeCollection(identity_rows, index_info=index_info)
        self.employee_profile_read_models = _FakeCollection(read_model_rows)
        self.counters = _FakeCollection(counter_rows)

    def __getitem__(self, name: str):
        return getattr(self, name)


@pytest.mark.asyncio
async def test_verify_employee_code_cutover_passes_when_cutover_state_is_clean() -> None:
    db = _FakeDb(
        identity_rows=[
            {"employee_id": "EMP-1", "employee_code": "MADC-2020-R0001"},
            {"employee_id": "EMP-2", "employee_code": "MADC-2024-R0001"},
            {"employee_id": "EMP-3", "employee_code": "MADC-2024-C0002"},
        ],
        read_model_rows=[
            {"employee_id": "EMP-1", "employee_code": "MADC-2020-R0001"},
            {"employee_id": "EMP-2", "employee_code": "MADC-2024-R0001"},
            {"employee_id": "EMP-3", "employee_code": "MADC-2024-C0002"},
        ],
        counter_rows=[
            {"_id": "employee_code:2020", "seq": 1},
            {"_id": "employee_code:2024", "seq": 2},
        ],
        index_info={
            "employee_code_1": {
                "key": [("employee_code", 1)],
                "unique": True,
                "background": True,
            }
        },
    )

    result = await verify_employee_code_cutover(db)

    assert result["ok"] is True
    assert all(result["checks"].values())
    assert result["legacy_counter"] is None
    assert result["missing_year_scoped_counters"] == []
    assert result["mismatched_year_scoped_counters"] == []


@pytest.mark.asyncio
async def test_verify_employee_code_cutover_reports_failed_checks() -> None:
    db = _FakeDb(
        identity_rows=[
            {"employee_id": "EMP-1", "employee_code": "MADC-2024-R0001"},
            {"employee_id": "EMP-2", "employee_code": "MADC-2024-R0001"},
            {"employee_id": "EMP-3", "employee_code": "MADC-2024-C0002"},
            {"employee_id": "EMP-4", "employee_code": "EMP-LEGACY-1"},
        ],
        read_model_rows=[
            {"employee_id": "EMP-1", "employee_code": "MADC-2024-R0001"},
            {"employee_id": "EMP-2", "employee_code": "MADC-2024-R0001"},
        ],
        counter_rows=[
            {"_id": "employee_code", "seq": 556},
            {"_id": "employee_code:2024", "seq": 1},
        ],
        index_info={
            "employee_code_1": {
                "key": [("employee_code", 1)],
                "background": True,
            }
        },
    )

    result = await verify_employee_code_cutover(db)

    assert result["ok"] is False
    assert result["checks"]["identity_duplicates"] is False
    assert result["checks"]["read_model_duplicates"] is False
    assert result["checks"]["canonical_format"] is False
    assert result["checks"]["employee_code_unique_index"] is False
    assert result["checks"]["legacy_counter_absent"] is False
    assert result["checks"]["year_scoped_counter_values"] is False