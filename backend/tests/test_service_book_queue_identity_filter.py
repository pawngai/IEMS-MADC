from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.service_book.api import query_router as query_router_module


class _FakeCursor:
    def __init__(self, items):
        self._items = items

    def sort(self, *_args, **_kwargs):
        return self

    async def to_list(self, length):
        return self._items[:length]


class _FakeAggregateCursor(_FakeCursor):
    pass


class _FakeCollection:
    def __init__(self, items):
        self.items = items
        self.query = None
        self.queries = []
        self.projection = None
        self.aggregate_pipeline = None

    def find(self, query, projection):
        self.query = query
        self.queries.append(query)
        self.projection = projection
        items = [
            item for item in self.items
            if item.get("is_active") == query.get("is_active")
            and (
                item.get("workflow_state") == query.get("workflow_state")
                or item.get("workflow_state") in (query.get("workflow_state", {}).get("$in") if isinstance(query.get("workflow_state"), dict) else [])
            )
        ]
        return _FakeCursor(items)

    def aggregate(self, pipeline):
        self.aggregate_pipeline = pipeline
        match_stage = pipeline[0].get("$match", {})
        requested_states = match_stage.get("workflow_state", {}).get("$in", [])
        facet_stage = pipeline[1].get("$facet", {})
        items = []
        for state in requested_states:
            limit_stage = next(
                (stage.get("$limit") for stage in facet_stage.get(state, []) if "$limit" in stage),
                len(self.items),
            )
            state_items = [
                item for item in self.items
                if item.get("is_active") == match_stage.get("is_active")
                and item.get("workflow_state") == state
            ]
            state_items = sorted(state_items, key=lambda item: item.get("updated_at") or "", reverse=True)
            items.extend([{key: value for key, value in item.items() if key != "_id"} for item in state_items[:limit_stage]])
        return _FakeAggregateCursor(sorted(items, key=lambda item: item.get("updated_at") or "", reverse=True))


class _FakeDb:
    def __init__(self, items):
        self.service_book_workflow_entries = _FakeCollection(items)


@pytest.mark.asyncio
async def test_service_book_queue_excludes_entries_without_identity(monkeypatch):
    db = _FakeDb(
        [
            {
                "id": "entry-1",
                "employee_id": "EMP-FOUND",
                "workflow_state": "DRAFT",
                "is_active": True,
            },
            {
                "id": "entry-2",
                "employee_id": "EMP-MISSING",
                "workflow_state": "DRAFT",
                "is_active": True,
            },
        ]
    )

    monkeypatch.setattr(query_router_module, "require_permissions", lambda *_args, **_kwargs: None)

    async def _fake_find_identities_by_ids(_db, *, employee_ids, projection):
        assert set(employee_ids) == {"EMP-FOUND", "EMP-MISSING"}
        assert projection == {"_id": 0, "employee_id": 1, "full_name": 1, "employee_code": 1}
        return [
            {
                "employee_id": "EMP-FOUND",
                "full_name": "Found Employee",
                "employee_code": "MADC-2024-0001",
            }
        ]

    monkeypatch.setattr(query_router_module, "find_identities_by_ids", _fake_find_identities_by_ids)

    result = await query_router_module.list_service_book_queue(
        workflow_state="DRAFT",
        page_size=200,
        db=db,
        current_user={"permissions": ["SERVICE_BOOK_READ_ALL"]},
    )

    assert result == {
        "entries": [
            {
                "id": "entry-1",
                "employee_id": "EMP-FOUND",
                "workflow_state": "DRAFT",
                "is_active": True,
                "full_name": "Found Employee",
                "employee_code": "MADC-2024-0001",
            }
        ]
    }
    assert db.service_book_workflow_entries.query == {"is_active": True, "workflow_state": "DRAFT"}
    assert db.service_book_workflow_entries.projection == {"_id": 0}


@pytest.mark.asyncio
async def test_service_book_queue_fetches_multiple_states_in_one_contract(monkeypatch):
    db = _FakeDb(
        [
            {
                "id": "entry-1",
                "employee_id": "EMP-DRAFT",
                "workflow_state": "DRAFT",
                "is_active": True,
                "updated_at": "2026-05-25T10:00:00Z",
            },
            {
                "id": "entry-2",
                "employee_id": "EMP-SUBMITTED",
                "workflow_state": "SUBMITTED",
                "is_active": True,
                "updated_at": "2026-05-25T11:00:00Z",
            },
            {
                "id": "entry-3",
                "employee_id": "EMP-VERIFIED",
                "workflow_state": "VERIFIED",
                "is_active": True,
                "updated_at": "2026-05-25T12:00:00Z",
            },
        ]
    )

    monkeypatch.setattr(query_router_module, "require_permissions", lambda *_args, **_kwargs: None)

    async def _fake_find_identities_by_ids(_db, *, employee_ids, projection):
        _ = (_db, projection)
        return [
            {
                "employee_id": employee_id,
                "full_name": f"Name {employee_id}",
                "employee_code": f"CODE-{employee_id}",
            }
            for employee_id in employee_ids
        ]

    monkeypatch.setattr(query_router_module, "find_identities_by_ids", _fake_find_identities_by_ids)

    result = await query_router_module.list_service_book_queue(
        workflow_states="DRAFT,SUBMITTED",
        page_size=200,
        db=db,
        current_user={"permissions": ["SERVICE_BOOK_READ_ALL"]},
    )

    assert [entry["id"] for entry in result["entries"]] == ["entry-2", "entry-1"]
    assert db.service_book_workflow_entries.queries == []
    assert db.service_book_workflow_entries.aggregate_pipeline == [
        {"$match": {"is_active": True, "workflow_state": {"$in": ["DRAFT", "SUBMITTED"]}}},
        {
            "$facet": {
                "DRAFT": [
                    {"$match": {"workflow_state": "DRAFT"}},
                    {"$sort": {"updated_at": -1}},
                    {"$limit": 200},
                    {"$project": {"_id": 0}},
                ],
                "SUBMITTED": [
                    {"$match": {"workflow_state": "SUBMITTED"}},
                    {"$sort": {"updated_at": -1}},
                    {"$limit": 200},
                    {"$project": {"_id": 0}},
                ],
            }
        },
        {"$project": {"entries": {"$concatArrays": ["$DRAFT", "$SUBMITTED"]}}},
        {"$unwind": "$entries"},
        {"$replaceRoot": {"newRoot": "$entries"}},
        {"$sort": {"updated_at": -1}},
    ]
