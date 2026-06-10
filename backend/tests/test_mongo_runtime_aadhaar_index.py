from __future__ import annotations

import pytest

from app_platform.db.runtime import _drop_employee_identity_aadhaar_indexes


class _FakeEmployeeIdentitiesCollection:
    def __init__(self) -> None:
        self.drop_index_calls: list[str] = []

    async def index_information(self):
        return {
            "_id_": {"key": [("_id", 1)]},
            "aadhaar_number_1": {"key": [("aadhaar_number", 1)], "unique": True},
            "employee_code_1": {"key": [("employee_code", 1)], "unique": True},
        }

    async def drop_index(self, index_name: str):
        self.drop_index_calls.append(index_name)


class _FakeDb:
    def __init__(self) -> None:
        self.employee_identities = _FakeEmployeeIdentitiesCollection()


@pytest.mark.asyncio
async def test_drop_employee_identity_aadhaar_indexes_removes_matching_index() -> None:
    db = _FakeDb()

    await _drop_employee_identity_aadhaar_indexes(db.employee_identities)

    assert db.employee_identities.drop_index_calls == ["aadhaar_number_1"]