from __future__ import annotations

import pytest

from contexts.service_book.contracts import service_book_directory
from contexts.service_book.repository.read_repository import ServiceBookReadRepository


def _deep_get(document, dotted_key: str):
    value = document
    for part in dotted_key.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _matches(document: dict, query: dict) -> bool:
    for key, expected in (query or {}).items():
        actual = _deep_get(document, key)
        if isinstance(expected, dict):
            if "$in" in expected and actual not in expected["$in"]:
                return False
            if "$gte" in expected and (actual is None or actual < expected["$gte"]):
                return False
            if "$lte" in expected and (actual is None or actual > expected["$lte"]):
                return False
            continue
        if actual != expected:
            return False
    return True


class _FakeCursor:
    def __init__(self, docs: list[dict]) -> None:
        self._docs = list(docs)

    def sort(self, key: str, direction: int):
        reverse = direction == -1
        self._docs.sort(key=lambda item: item.get(key) or "", reverse=reverse)
        return self

    async def to_list(self, length: int):
        return self._docs[:length]


class _FakeCollection:
    def __init__(self, docs: list[dict] | None = None) -> None:
        self.docs = list(docs or [])

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if _matches(doc, query):
                return {k: v for k, v in doc.items() if projection is None or k != "_id"}
        return None

    def find(self, query, projection=None):
        matched = [
            {k: v for k, v in doc.items() if projection is None or k != "_id"}
            for doc in self.docs
            if _matches(doc, query)
        ]
        return _FakeCursor(matched)

    async def count_documents(self, query):
        return len([doc for doc in self.docs if _matches(doc, query)])


class _FakeDb:
    def __init__(self) -> None:
        self.service_book_entries = _FakeCollection(
            [
                {
                    "entry_id": "legacy-part-iv",
                    "employee_id": "EMP-1",
                    "part_code": "SB_PART_IV",
                    "schema_key": "SB_IV_SERVICE_HISTORY_ROW",
                    "created_at": "2026-03-16T00:00:00+00:00",
                    "payload": {"status": "LOCKED", "post_held": "ASO"},
                },
                {
                    "entry_id": "legacy-part-vi-opening",
                    "employee_id": "EMP-1",
                    "part_code": "SB_PART_VI",
                    "schema_key": "SB_VI_LEAVE_OPENING_BALANCE",
                    "created_at": "2026-03-10T00:00:00+00:00",
                    "payload": {"earned_leave_balance": 99},
                },
            ]
        )
        self.service_book_part_projections = _FakeCollection(
            [
                {
                    "employee_id": "EMP-1",
                    "part_code": "SB_PART_VI",
                    "earned_leave_balance": 99,
                    "half_pay_leave_balance": 50,
                }
            ]
        )
        self.leave_ledger_entries = _FakeCollection(
            [
                {
                    "employee_id": "EMP-1",
                    "id": "ledger-1",
                    "earned_leave_balance": 210.0,
                    "half_pay_leave_balance": 140.0,
                    "commuted_leave_balance": 18.0,
                    "leave_not_due_balance": 7.0,
                    "casual_leave_balance": 6.0,
                    "created_at": "2026-03-01T00:00:00+00:00",
                    "last_updated_at": "2026-03-16T01:19:11+00:00",
                    "transactions": [
                        {
                            "id": "txn-credit",
                            "transaction_date": "2025-07-01",
                            "transaction_type": "CREDIT",
                            "leave_type": "EL",
                            "credit_days": 15,
                            "closing_balance": 210,
                            "remarks": "Half-yearly EL credit",
                        },
                        {
                            "id": "txn-cml",
                            "transaction_date": "2026-03-16",
                            "transaction_type": "DEBIT",
                            "leave_type": "CML",
                            "days_availed": 2,
                            "closing_balance": 16,
                            "remarks": "Sanctioned commuted leave",
                        },
                        {
                            "id": "txn-cl",
                            "transaction_date": "2026-03-18",
                            "transaction_type": "DEBIT",
                            "leave_type": "CL",
                            "days_availed": 1,
                            "closing_balance": 5,
                            "remarks": "Operational leave only",
                        },
                    ],
                }
            ]
        )


@pytest.mark.asyncio
async def test_directory_list_projected_entries_uses_canonical_leave_ledger_for_part_vi() -> None:
    db = _FakeDb()

    result = await service_book_directory.list_projected_service_book_entries(
        db,
        employee_id="EMP-1",
    )

    assert any(entry.get("part_code") == "SB_PART_IV" for entry in result)
    assert len([entry for entry in result if entry.get("part_code") == "SB_PART_VI"]) == 3
    assert {entry.get("schema_key") for entry in result if entry.get("part_code") == "SB_PART_VI"} == {
        "SB_VI_LEAVE_OPENING_BALANCE",
        "SB_VI_LEAVE_TRANSACTION_ROW",
    }
    projected_ids = {entry.get("id") for entry in result if entry.get("part_code") == "SB_PART_VI"}
    assert "txn-cl" not in projected_ids
    latest_txn = next(entry for entry in result if entry.get("id") == "txn-cml")
    assert latest_txn["payload"]["leave_type"] == "CML"
    assert latest_txn["payload"]["closing_balance"] == 16
    assert latest_txn["workflow_state"] == "LOCKED"


@pytest.mark.asyncio
async def test_directory_get_projected_part_vi_prefers_canonical_leave_ledger() -> None:
    db = _FakeDb()

    result = await service_book_directory.get_projected_service_book_part(
        db,
        employee_id="EMP-1",
        part_code="SB_PART_VI",
    )

    assert result is not None
    assert result["earned_leave_balance"] == 210.0
    assert result["half_pay_leave_balance"] == 140.0
    assert result["commuted_leave_balance"] == 18.0
    assert result["leave_not_due_balance"] == 7.0
    assert "casual_leave_balance" not in result
    assert result["source"] == "LEAVE_LEDGER"


@pytest.mark.asyncio
async def test_read_repository_list_entries_replaces_legacy_part_vi_rows() -> None:
    db = _FakeDb()
    repo = ServiceBookReadRepository(db=db)

    result = await repo.list_entries(employee_id="EMP-1", filters={})

    assert len([entry for entry in result if entry.get("part_code") == "SB_PART_VI"]) == 3
    assert all(entry.get("entry_id") != "legacy-part-vi-opening" for entry in result)
    assert all(entry.get("id") != "txn-cl" for entry in result)
    latest_part_vi_entry = next(entry for entry in result if entry.get("id") == "txn-cml")
    assert latest_part_vi_entry["payload"]["closing_balance"] == 16


@pytest.mark.asyncio
async def test_read_repository_get_part_vi_returns_canonical_projection() -> None:
    db = _FakeDb()
    repo = ServiceBookReadRepository(db=db)

    result = await repo.get_part(employee_id="EMP-1", part_code="SB_PART_VI")

    assert result is not None
    assert result["earned_leave_balance"] == 210.0
    assert result["commuted_leave_balance"] == 18.0
    assert result["leave_not_due_balance"] == 7.0
    assert "casual_leave_balance" not in result