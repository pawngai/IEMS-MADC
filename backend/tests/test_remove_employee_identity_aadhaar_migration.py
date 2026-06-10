from __future__ import annotations

import pytest

from app_platform.db.migration_runner import discover_migration_modules


def _get_migration(module_suffix: str):
    for module in discover_migration_modules():
        if module.__name__.endswith(module_suffix):
            return module
    raise AssertionError(f"Migration {module_suffix!r} not found")


migration = _get_migration("003_remove_employee_identity_aadhaar")


class _FakeEmployeeIdentitiesCollection:
    def __init__(self) -> None:
        self.update_many_calls: list[tuple[dict, dict]] = []
        self.drop_index_calls: list[str] = []

    async def update_many(self, query, update):
        self.update_many_calls.append((query, update))

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
async def test_migration_unsets_identity_aadhaar_and_drops_matching_index() -> None:
    db = _FakeDb()

    await migration.run(db)

    assert db.employee_identities.update_many_calls == [
        (
            {"aadhaar_number": {"$exists": True}},
            {"$unset": {"aadhaar_number": ""}},
        )
    ]
    assert db.employee_identities.drop_index_calls == ["aadhaar_number_1"]