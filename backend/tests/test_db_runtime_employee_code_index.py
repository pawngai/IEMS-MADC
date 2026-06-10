from __future__ import annotations

import pytest

from app_platform.db import runtime


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


class _FakeEmployeeIdentitiesCollection:
    def __init__(self, *, duplicates=None, index_info=None):
        self.duplicates = list(duplicates or [])
        self._index_info = dict(index_info or {})
        self.dropped_indexes: list[str] = []
        self.created_indexes: list[dict] = []

    def aggregate(self, _pipeline):
        return _FakeAsyncCursor(self.duplicates)

    async def index_information(self):
        return dict(self._index_info)

    async def drop_index(self, name: str):
        self.dropped_indexes.append(name)
        self._index_info.pop(name, None)

    async def create_index(self, keys, **kwargs):
        self.created_indexes.append({"keys": keys, **kwargs})
        index_name = "_".join(f"{field}_{direction}" for field, direction in keys)
        self._index_info[index_name] = {"key": keys, **kwargs}
        return index_name


class _FakeDb:
    def __init__(self, employee_identities):
        self.employee_identities = employee_identities


@pytest.mark.asyncio
async def test_promotes_legacy_employee_code_index_to_unique() -> None:
    collection = _FakeEmployeeIdentitiesCollection(
        index_info={
            "employee_id_1": {"key": [("employee_id", 1)], "unique": True},
            "employee_code_1": {"key": [("employee_code", 1)]},
        }
    )

    await runtime._ensure_employee_code_unique_index(_FakeDb(collection), ascending=1)

    assert collection.dropped_indexes == ["employee_code_1"]
    assert collection.created_indexes == [
        {
            "keys": [("employee_code", 1)],
            "unique": True,
            "background": True,
        }
    ]


@pytest.mark.asyncio
async def test_keeps_existing_unique_employee_code_index() -> None:
    collection = _FakeEmployeeIdentitiesCollection(
        index_info={
            "employee_code_1": {
                "key": [("employee_code", 1)],
                "unique": True,
                "background": True,
            }
        }
    )

    await runtime._ensure_employee_code_unique_index(_FakeDb(collection), ascending=1)

    assert collection.dropped_indexes == []
    assert collection.created_indexes == []


@pytest.mark.asyncio
async def test_rejects_duplicate_employee_codes_before_index_promotion() -> None:
    collection = _FakeEmployeeIdentitiesCollection(
        duplicates=[
            {
                "_id": "MADC-2024-0001",
                "count": 2,
                "employee_ids": ["EMP-1", "EMP-2"],
            }
        ],
        index_info={
            "employee_code_1": {"key": [("employee_code", 1)]},
        },
    )

    with pytest.raises(RuntimeError) as exc:
        await runtime._ensure_employee_code_unique_index(_FakeDb(collection), ascending=1)

    assert "MADC-2024-0001" in str(exc.value)
    assert collection.dropped_indexes == []
    assert collection.created_indexes == []