from __future__ import annotations

import asyncio
import pytest
from fastapi import HTTPException

from contexts.service_book.application.service import (
    createServiceBookIfEligible,
    validateServiceBookEligibility,
)


class _FakePartProjectionCollection:
    def __init__(self) -> None:
        self.calls: list[tuple[dict, dict, bool]] = []

    async def update_one(self, query, update, upsert=False):
        self.calls.append((query, update, upsert))

    def find(self, *_args, **_kwargs):
        class _Cursor:
            async def to_list(self, length=None):
                _ = length
                return []

        return _Cursor()


class _FakeEntryCollection:
    def find(self, *_args, **_kwargs):
        class _Cursor:
            def sort(self, *_sort_args, **_sort_kwargs):
                return self

            async def to_list(self, length=None):
                _ = length
                return []

        return _Cursor()


class _FakeLeaveLedgerCollection:
    async def find_one(self, *_args, **_kwargs):
        return None


class _FakeDb:
    def __init__(self) -> None:
        self.service_book_part_projections = _FakePartProjectionCollection()
        self.service_book_entries = _FakeEntryCollection()
        self.leave_ledger_entries = _FakeLeaveLedgerCollection()


def test_create_service_book_if_eligible_blocks_non_regular() -> None:
    db = _FakeDb()

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            createServiceBookIfEligible(
                db=db,
                employee_id="EMP-2001",
                employee_or_type={"employment_type": "CONTRACTUAL"},
            )
        )

    assert exc.value.status_code == 403
    assert "Service Book" in str(exc.value.detail)


def test_create_service_book_if_eligible_allows_regular() -> None:
    db = _FakeDb()

    result = asyncio.run(
        createServiceBookIfEligible(
            db=db,
            employee_id="EMP-2002",
            employee_or_type={"employment_type": "REGULAR"},
        )
    )

    assert result["projection_ready"] is True
    assert db.service_book_part_projections.calls == []


def test_validate_service_book_eligibility_only_regular() -> None:
    assert validateServiceBookEligibility({"employment_type": "REGULAR"}) is True

    with pytest.raises(HTTPException):
        validateServiceBookEligibility({"employment_type": "DAILY_WAGE"})
