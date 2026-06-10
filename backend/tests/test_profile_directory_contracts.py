from __future__ import annotations

import re

import pytest

from contexts.employee_profile.contracts import profile_directory


class _BoolGuardCollection:
    def __bool__(self) -> bool:
        raise NotImplementedError("Collection objects do not implement truth value testing")


class _FakeAsyncCursor:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = list(rows)

    def sort(self, field: str, direction: int = 1):
        self._rows.sort(key=lambda row: row.get(field) or "", reverse=direction < 0)
        return self

    def skip(self, count: int):
        self._rows = self._rows[count:]
        return self

    def limit(self, count: int):
        self._rows = self._rows[:count]
        return self

    async def to_list(self, length: int | None = None):
        if length is None:
            return list(self._rows)
        return list(self._rows[:length])


class _FakeCollection(_BoolGuardCollection):
    def __init__(self, rows: list[dict] | None = None) -> None:
        self.rows = list(rows or [])

    def _matches(self, row: dict, query: dict) -> bool:
        for key, expected in query.items():
            if key == "$or":
                if not any(self._matches(row, option) for option in expected):
                    return False
                continue

            actual = row.get(key)
            if isinstance(expected, dict):
                if "$in" in expected:
                    if actual not in expected["$in"]:
                        return False
                    continue
                if "$regex" in expected:
                    flags = re.IGNORECASE if "i" in str(expected.get("$options", "")) else 0
                    if not re.search(str(expected["$regex"]), str(actual or ""), flags):
                        return False
                    continue
            if actual != expected:
                return False
        return True

    def find(self, query: dict, _projection: dict | None = None):
        return _FakeAsyncCursor([dict(row) for row in self.rows if self._matches(row, query)])

    async def count_documents(self, query: dict) -> int:
        return sum(1 for row in self.rows if self._matches(row, query))


class _DbWithCollections:
    def __init__(
        self,
        *,
        projected_rows: list[dict] | None = None,
        identity_rows: list[dict] | None = None,
    ) -> None:
        self.employee_profile_read_models = _FakeCollection(projected_rows)
        self.employee_identities = _FakeCollection(identity_rows)


def test_profiles_collection_does_not_bool_test_mongo_collection_objects() -> None:
    db = _DbWithCollections(projected_rows=[], identity_rows=[])

    collection = profile_directory._profiles_collection(db)

    assert collection is db.employee_profile_read_models


@pytest.mark.asyncio
async def test_list_profiles_uses_active_identity_rows_as_draft_when_projection_is_incomplete() -> None:
    db = _DbWithCollections(
        projected_rows=[
            {
                "employee_id": "EMP-1",
                "employee_code": "EMP-2026-R0001",
                "full_name": "Alice",
                "workflow_status": "SUBMITTED",
                "current_department_id": "FIN",
            },
        ],
        identity_rows=[
            {
                "employee_id": "EMP-1",
                "employee_code": "EMP-2026-R0001",
                "full_name": "Alice",
                "workflow_status": "SUBMITTED",
                "current_department_id": "FIN",
            },
            {
                "employee_id": "EMP-2",
                "employee_code": "EMP-2026-R0002",
                "full_name": "Bob",
                "workflow_status": "ACTIVE",
                "current_department_id": "FIN",
            },
        ],
    )

    rows = await profile_directory.list_profiles(
        db,
        workflow_status="DRAFT",
        department_code="FIN",
        limit=50,
        offset=0,
    )

    assert [row["employee_id"] for row in rows] == ["EMP-2"]


@pytest.mark.asyncio
async def test_count_profiles_uses_active_identity_count_as_draft_when_projection_is_incomplete() -> None:
    db = _DbWithCollections(
        projected_rows=[
            {
                "employee_id": "EMP-1",
                "employee_code": "EMP-2026-R0001",
                "full_name": "Alice",
                "workflow_status": "SUBMITTED",
                "current_department_id": "FIN",
            },
        ],
        identity_rows=[
            {
                "employee_id": "EMP-1",
                "employee_code": "EMP-2026-R0001",
                "full_name": "Alice",
                "workflow_status": "SUBMITTED",
                "current_department_id": "FIN",
            },
            {
                "employee_id": "EMP-2",
                "employee_code": "EMP-2026-R0002",
                "full_name": "Bob",
                "workflow_status": "ACTIVE",
                "current_department_id": "FIN",
            },
        ],
    )

    count = await profile_directory.count_profiles(
        db,
        workflow_status="DRAFT",
        department_code="FIN",
    )

    assert count == 1


@pytest.mark.asyncio
async def test_list_profiles_does_not_use_identity_rows_for_submitted_profile_queue() -> None:
    db = _DbWithCollections(
        projected_rows=[],
        identity_rows=[
            {
                "employee_id": "EMP-IDENTITY-SUBMITTED",
                "employee_code": "EMP-2026-R0003",
                "full_name": "Identity Submitted",
                "workflow_status": "SUBMITTED",
                "current_department_id": "FIN",
            },
            {
                "employee_id": "EMP-ACTIVE",
                "employee_code": "EMP-2026-R0004",
                "full_name": "Activated Identity",
                "workflow_status": "ACTIVE",
                "current_department_id": "FIN",
            },
        ],
    )

    rows = await profile_directory.list_profiles(
        db,
        workflow_status="SUBMITTED",
        department_code="FIN",
        limit=50,
        offset=0,
    )
    count = await profile_directory.count_profiles(
        db,
        workflow_status="SUBMITTED",
        department_code="FIN",
    )

    assert rows == []
    assert count == 0
