from __future__ import annotations

import pytest

from app_platform.db.runtime import _drop_employee_identity_assignment_indexes


class _FakeEmployeeIdentitiesCollection:
    def __init__(self) -> None:
        self.drop_index_calls: list[str] = []

    async def index_information(self):
        return {
            "_id_": {"key": [("_id", 1)]},
            "current_department_id_1": {"key": [("current_department_id", 1)]},
            "employment_type_1": {"key": [("employment_type", 1)]},
            "employee_code_1": {"key": [("employee_code", 1)], "unique": True},
        }

    async def drop_index(self, index_name: str):
        self.drop_index_calls.append(index_name)


@pytest.mark.asyncio
async def test_drop_employee_identity_assignment_indexes_removes_matching_indexes() -> None:
    collection = _FakeEmployeeIdentitiesCollection()

    await _drop_employee_identity_assignment_indexes(collection)

    assert collection.drop_index_calls == ["current_department_id_1", "employment_type_1"]