from __future__ import annotations

import pytest

from app_platform.db.migration_runner import discover_migration_modules


def _get_migration(module_suffix: str):
    for module in discover_migration_modules():
        if module.__name__.endswith(module_suffix):
            return module
    raise AssertionError(f"Migration {module_suffix!r} not found")


migration = _get_migration("004_move_employee_identity_assignment_fields_to_profile")


class _FakeCursor:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    async def to_list(self, length=None):
        if length is None:
            return list(self._rows)
        return list(self._rows[:length])


class _FakeEmployeeIdentitiesCollection:
    def __init__(self) -> None:
        self.docs = [
            {
                "employee_id": "EMP-1",
                "employment_type": "REGULAR",
                "date_of_initial_engagement": "2020-01-01",
                "current_department_id": "FIN",
                "created_at": "2020-01-01T00:00:00+00:00",
                "version": 2,
            }
        ]
        self.drop_index_calls: list[str] = []

    def find(self, query, projection=None):
        _ = (query, projection)
        return _FakeCursor([dict(doc) for doc in self.docs])

    async def update_one(self, query, update):
        for doc in self.docs:
            if doc.get("employee_id") != query.get("employee_id"):
                continue
            for field_name in update.get("$unset", {}):
                doc.pop(field_name, None)
            doc.update(update.get("$set", {}))
            return
        raise AssertionError("employee identity row not found")

    async def index_information(self):
        return {
            "_id_": {"key": [("_id", 1)]},
            "current_department_id_1": {"key": [("current_department_id", 1)]},
            "employment_type_1": {"key": [("employment_type", 1)]},
        }

    async def drop_index(self, index_name: str):
        self.drop_index_calls.append(index_name)


class _FakeUpsertCollection:
    def __init__(self, existing_doc=None) -> None:
        self.docs = [] if existing_doc is None else [dict(existing_doc)]

    async def find_one(self, query, projection=None):
        _ = projection
        for doc in self.docs:
            if doc.get("employee_id") == query.get("employee_id"):
                return dict(doc)
        return None

    async def update_one(self, query, update, upsert=False):
        for index, doc in enumerate(self.docs):
            if doc.get("employee_id") != query.get("employee_id"):
                continue
            next_doc = dict(doc)
            next_doc.update(update.get("$setOnInsert", {}))
            next_doc.update(update.get("$set", {}))
            self.docs[index] = next_doc
            return
        if not upsert:
            raise AssertionError("upsert disabled for missing row")
        next_doc = {}
        next_doc.update(update.get("$setOnInsert", {}))
        next_doc.update(update.get("$set", {}))
        self.docs.append(next_doc)


class _FakeDb:
    def __init__(self) -> None:
        self.employee_identities = _FakeEmployeeIdentitiesCollection()
        self.employee_profile_extensions = _FakeUpsertCollection()
        self.employee_profile_read_models = _FakeUpsertCollection()


@pytest.mark.asyncio
async def test_migration_moves_assignment_fields_to_profile_and_unsets_identity_fields() -> None:
    db = _FakeDb()

    await migration.run(db)

    extension = db.employee_profile_extensions.docs[0]
    assert extension["employee_id"] == "EMP-1"
    assert extension["employment_type"] == "REGULAR"
    assert extension["date_of_initial_engagement"] == "2020-01-01"
    assert extension["current_department_id"] == "FIN"

    read_model = db.employee_profile_read_models.docs[0]
    assert read_model["employment_type"] == "REGULAR"
    assert read_model["current_department_id"] == "FIN"

    identity = db.employee_identities.docs[0]
    assert "employment_type" not in identity
    assert "date_of_initial_engagement" not in identity
    assert "current_department_id" not in identity
    assert db.employee_identities.drop_index_calls == ["current_department_id_1", "employment_type_1"]