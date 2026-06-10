from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.service_book.api import query_router as api_router
from contexts.service_book.repository.mongo_entry_repository import MongoServiceBookEntryRepository


class _CaptureService:
    def __init__(self) -> None:
        self.filters = None

    async def list_service_book_entries(self, *, employee_id: str, filters: dict):
        self.filters = {"employee_id": employee_id, **filters}
        return []

    def normalize_part_code(self, part_value: str | None) -> str | None:
        if not part_value:
            return None
        return part_value.upper()


@pytest.mark.asyncio
async def test_api_query_router_parses_csv_statuses(monkeypatch):
    service = _CaptureService()
    monkeypatch.setattr(api_router, "_require_service_book_read_access", lambda *_args, **_kwargs: None)

    async def fake_resolve_employee(_db, employee_ref: str):
        return employee_ref, {"employee_id": employee_ref, "employment_type": "REGULAR"}

    monkeypatch.setattr(api_router, "_resolve_employee", fake_resolve_employee)

    await api_router.list_service_book_entries(
        employee_id="EMP-1",
        statuses="approved, locked",
        service=service,
        current_user={"employee_id": "EMP-1"},
    )

    assert service.filters == {
        "employee_id": "EMP-1",
        "statuses": ["APPROVED", "LOCKED"],
    }


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
    def __init__(self, docs: list[dict]) -> None:
        self.docs = list(docs)

    def find(self, query, projection=None):
        matched = [
            {k: v for k, v in doc.items() if projection is None or k != "_id"}
            for doc in self.docs
            if _matches(doc, query)
        ]
        return _FakeCursor(matched)


class _FakeDb:
    def __init__(self, docs: list[dict]) -> None:
        self.service_book_entries = _FakeCollection(docs)


@pytest.mark.asyncio
async def test_repository_list_entries_matches_canonical_top_level_status_and_part_key():
    repo = MongoServiceBookEntryRepository(db=_FakeDb([
        {
            "id": "entry-1",
            "employee_id": "EMP-1",
            "part_key": "SB_PART_I",
            "schema_key": "SB_I_BIODATA",
            "status": "LOCKED",
            "workflow_state": "LOCKED",
            "created_at": "2026-06-05T10:00:00+00:00",
            "payload": {"name_in_block_letters": "Workflow Regular Beacon"},
        },
        {
            "entry_id": "legacy-1",
            "employee_id": "EMP-1",
            "part_code": "SB_PART_IV",
            "created_at": "2026-06-04T10:00:00+00:00",
            "payload": {"status": "APPROVED"},
        },
    ]))

    locked = await repo.list_entries(
        employee_id="EMP-1",
        filters={"statuses": ["LOCKED"], "part_code": "SB_PART_I"},
    )
    approved = await repo.list_entries(
        employee_id="EMP-1",
        filters={"status": "APPROVED", "part_code": "SB_PART_IV"},
    )

    assert [entry.get("schema_key") for entry in locked] == ["SB_I_BIODATA"]
    assert [entry.get("entry_id") for entry in approved] == ["legacy-1"]

