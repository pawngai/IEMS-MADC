from __future__ import annotations

import pytest

from contexts.ess.infrastructure import repo


class _FakeCollection:
    def __init__(self, find_one_result=None, count_result: int = 0) -> None:
        self._find_one_result = find_one_result
        self._count_result = count_result

    async def find_one(self, *_args, **_kwargs):
        return self._find_one_result

    async def count_documents(self, *_args, **_kwargs):
        return self._count_result


class _FakeDb:
    def __init__(self) -> None:
        self.service_book_part_projections = _FakeCollection()
        self.service_book_entries = _FakeCollection()
        self.leave_ledger_entries = _FakeCollection()

    def __getitem__(self, name: str):
        return getattr(self, name)


@pytest.mark.asyncio
async def test_get_service_book_part_reads_projection_collection() -> None:
    db = _FakeDb()
    db.service_book_part_projections = _FakeCollection(
        find_one_result={"employee_id": "EMP-1", "part_code": "VI", "earned_leave_balance": 11}
    )

    result = await repo.get_service_book_part(db, "EMP-1", "VI")

    assert result is not None
    assert result["earned_leave_balance"] == 11


@pytest.mark.asyncio
async def test_get_service_book_part_returns_none_when_projection_missing() -> None:
    db = _FakeDb()
    db.service_book_part_projections = _FakeCollection(find_one_result=None)

    result = await repo.get_service_book_part(db, "EMP-1", "VI")

    assert result is None


@pytest.mark.asyncio
async def test_count_service_book_parts_counts_projection_documents() -> None:
    db = _FakeDb()
    db.service_book_part_projections = _FakeCollection(count_result=3)

    total = await repo.count_service_book_parts(db, "EMP-1")

    assert total == 3


@pytest.mark.asyncio
async def test_count_service_book_parts_returns_zero_when_projection_empty() -> None:
    db = _FakeDb()
    db.service_book_part_projections = _FakeCollection(count_result=0)

    total = await repo.count_service_book_parts(db, "EMP-1")

    assert total == 0
