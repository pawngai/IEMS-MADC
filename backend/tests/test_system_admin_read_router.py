from __future__ import annotations

from copy import deepcopy
from datetime import datetime

import pytest
from fastapi import HTTPException

from contexts.system_admin.api import router as system_admin_router


class _FakeCursor:
    def __init__(self, documents: list[dict]) -> None:
        self._documents = [deepcopy(document) for document in documents]
        self._skip = 0
        self._limit: int | None = None
        self._iter_index = 0

    def _active_documents(self) -> list[dict]:
        end_index = None if self._limit is None else self._skip + self._limit
        return self._documents[self._skip:end_index]

    def sort(self, field: str, direction: int):
        reverse = direction == -1
        self._documents.sort(key=lambda item: item.get(field) or "", reverse=reverse)
        return self

    def skip(self, count: int):
        self._skip = count
        return self

    def limit(self, count: int):
        self._limit = count
        return self

    async def to_list(self, count: int):
        effective_limit = self._limit if self._limit is not None else count
        return deepcopy(self._active_documents()[:effective_limit])

    def __aiter__(self):
        self._iter_index = 0
        return self

    async def __anext__(self):
        active_documents = self._active_documents()
        if self._iter_index >= len(active_documents):
            raise StopAsyncIteration
        document = deepcopy(active_documents[self._iter_index])
        self._iter_index += 1
        return document


class _FakeCollection:
    def __init__(self, documents: list[dict]) -> None:
        self._documents = [deepcopy(document) for document in documents]

    async def count_documents(self, query: dict):
        return len([document for document in self._documents if _matches_query(document, query)])

    def find(self, query: dict, projection: dict | None = None):
        documents = []
        for document in self._documents:
            if _matches_query(document, query):
                documents.append(_apply_projection(document, projection))
        return _FakeCursor(documents)

    def aggregate(self, pipeline: list[dict]):
        _ = pipeline
        grouped: dict[str, int] = {}
        for document in self._documents:
            key = str(document.get("action") or "UNKNOWN")
            grouped[key] = grouped.get(key, 0) + 1
        rows = [
            {"_id": key, "count": count}
            for key, count in sorted(grouped.items(), key=lambda item: (-item[1], item[0]))
        ]
        return _FakeCursor(rows)


class _FakeSystemAdminDB:
    def __init__(self) -> None:
        self.employee_profile_read_models = _FakeCollection(
            [
                {
                    "employee_id": "EMP-1",
                    "full_name": "Alpha",
                    "workflow_status": "SUBMITTED",
                    "updated_at": "2026-03-20T08:00:00+00:00",
                },
                {
                    "employee_id": "EMP-2",
                    "full_name": "Beta",
                    "workflow_status": "LOCKED",
                    "updated_at": "2026-04-12T08:00:00+00:00",
                },
            ]
        )
        self.service_book_entries = _FakeCollection(
            [
                {
                    "entry_id": "SB-1",
                    "employee_id": "EMP-1",
                    "part_code": "I",
                    "workflow_state": "VERIFIED",
                    "updated_at": "2026-03-15T08:00:00+00:00",
                },
                {
                    "entry_id": "SB-2",
                    "employee_id": "EMP-2",
                    "part_code": "II",
                    "workflow_state": "ATTESTED",
                    "updated_at": "2026-04-12T08:00:00+00:00",
                },
            ]
        )
        self.leave_applications = _FakeCollection(
            [
                {
                    "id": "LV-1",
                    "employee_id": "EMP-1",
                    "leave_type_code": "EL",
                    "status": "RECOMMENDED",
                    "from_date": "2026-04-01",
                    "to_date": "2026-04-03",
                    "applied_at": "2026-03-10T08:00:00+00:00",
                },
                {
                    "id": "LV-2",
                    "employee_id": "EMP-2",
                    "leave_type_code": "CL",
                    "status": "SANCTIONED",
                    "from_date": "2026-04-10",
                    "to_date": "2026-04-10",
                    "applied_at": "2026-04-09T08:00:00+00:00",
                },
            ]
        )
        self.audit_logs = _FakeCollection(
            [
                {
                    "timestamp": "2026-04-12T09:15:00+00:00",
                    "action": "CREATE",
                    "resource_type": "employee_profile",
                    "resource_id": "EMP-1",
                    "user_name": "Admin One",
                    "user_id": "admin-1",
                },
                {
                    "timestamp": "2026-04-11T09:15:00+00:00",
                    "action": "VERIFY",
                    "resource_type": "servicebook_entry",
                    "resource_id": "SB-1",
                    "user_name": "Verifier One",
                    "user_id": "verifier-1",
                },
            ]
        )


def _apply_projection(document: dict, projection: dict | None) -> dict:
    if not projection:
        return deepcopy(document)
    included_fields = [field for field, value in projection.items() if field != "_id" and value]
    if not included_fields:
        return deepcopy(document)
    return {field: deepcopy(document.get(field)) for field in included_fields if field in document}


def _field_value(document: dict, dotted_field: str):
    value = document
    for key in dotted_field.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _matches_condition(value, condition) -> bool:
    if isinstance(condition, dict):
        for operator, expected in condition.items():
            if operator == "$in":
                if value not in expected:
                    return False
            elif operator == "$lt":
                if value is None or value >= expected:
                    return False
            elif operator == "$lte":
                if value is None or value > expected:
                    return False
            elif operator == "$gte":
                if value is None or value < expected:
                    return False
            elif operator == "$ne":
                if value == expected:
                    return False
            else:
                raise AssertionError(f"Unsupported operator in fake collection: {operator}")
        return True
    return value == condition


def _matches_query(document: dict, query: dict) -> bool:
    for field, condition in query.items():
        value = _field_value(document, field)
        if not _matches_condition(value, condition):
            return False
    return True


@pytest.mark.asyncio
async def test_list_employees_uses_profile_contracts(monkeypatch) -> None:
    async def _fake_list_profiles(_db, **_kwargs):
        return [{"employee_id": "EMP-1", "full_name": "A"}]

    async def _fake_count_profiles(_db, **_kwargs):
        return 1

    monkeypatch.setattr(system_admin_router, "list_profiles", _fake_list_profiles)
    monkeypatch.setattr(system_admin_router, "count_employee_profiles", _fake_count_profiles)

    result = await system_admin_router.list_employees(
        limit=50,
        offset=0,
        db=object(),
        current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
        search=None,
        department=None,
        employment_type=None,
        workflow_status=None,
    )

    assert result["total"] == 1
    assert result["employees"][0]["employee_id"] == "EMP-1"


@pytest.mark.asyncio
async def test_get_employee_returns_profile_and_servicebook_count(monkeypatch) -> None:
    async def _fake_find_profile_view(_db, **_kwargs):
        return {"employee_id": "EMP-9", "full_name": "Employee 9"}

    async def _fake_count_servicebook_entries(_db, **_kwargs):
        return 3

    monkeypatch.setattr(system_admin_router, "find_profile_view", _fake_find_profile_view)
    monkeypatch.setattr(system_admin_router, "count_servicebook_entries", _fake_count_servicebook_entries)

    result = await system_admin_router.get_employee(
        employee_id="EMP-9",
        db=object(),
        current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
    )

    assert result["employee"]["employee_id"] == "EMP-9"
    assert result["service_book_entries_count"] == 3


@pytest.mark.asyncio
async def test_get_leave_applications_filters_by_department(monkeypatch) -> None:
    async def _fake_get_employee_ids_for_department(_db, **_kwargs):
        return ["EMP-1", "EMP-2"]

    async def _fake_list_leave_applications(_db, **kwargs):
        assert kwargs.get("employee_ids") == ["EMP-1", "EMP-2"]
        return [{"id": "L-1", "employee_id": "EMP-1"}]

    async def _fake_count_leave_applications(_db, **kwargs):
        assert kwargs.get("employee_ids") == ["EMP-1", "EMP-2"]
        return 1

    monkeypatch.setattr(system_admin_router, "get_employee_ids_for_department", _fake_get_employee_ids_for_department)
    monkeypatch.setattr(system_admin_router, "list_leave_applications", _fake_list_leave_applications)
    monkeypatch.setattr(system_admin_router, "count_leave_applications", _fake_count_leave_applications)

    result = await system_admin_router.get_leave_applications(
        limit=50,
        offset=0,
        db=object(),
        current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
        status="SUBMITTED",
        leave_type=None,
        department="FIN",
    )

    assert result["total"] == 1
    assert result["items"][0]["id"] == "L-1"


@pytest.mark.asyncio
async def test_get_dashboard_stats_returns_live_aggregate_counts(monkeypatch) -> None:
    captured_queries: list[dict] = []

    async def _fake_count_users(_db, *, query=None):
        captured_queries.append(query or {})
        if query == {"is_active": {"$ne": False}}:
            return 4
        return 6

    async def _fake_count_profiles(_db, **_kwargs):
        return 19

    async def _fake_count_stuck_workflows(_db, *, days_threshold=7):
        assert days_threshold == 7
        return 3

    async def _fake_count_audit_logs(_db, *, query=None):
        assert isinstance(query, dict)
        assert "timestamp" in query
        assert "$gte" in query["timestamp"]
        return 8

    monkeypatch.setattr(system_admin_router, "count_users", _fake_count_users)
    monkeypatch.setattr(system_admin_router, "count_employee_profiles", _fake_count_profiles)
    monkeypatch.setattr(system_admin_router, "_build_stuck_workflow_payload", lambda _db, days_threshold=7, limit=50: _fake_stuck_payload(days_threshold=days_threshold))
    monkeypatch.setattr(system_admin_router, "count_audit_logs", _fake_count_audit_logs)

    async def _fake_stuck_payload(*, days_threshold=7, limit=50):
        assert days_threshold == 7
        _ = limit
        return {"total": 3, "stuck_profiles": [], "stuck_entries": [], "stuck_leaves": [], "days_threshold": 7}

    result = await system_admin_router.get_dashboard_stats(
        db=object(),
        current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
    )

    assert captured_queries == [{}, {"is_active": {"$ne": False}}]
    assert result == {
        "users": {"total": 6, "active": 4},
        "employees": {"total": 19},
        "workflows": {"stuck": 3},
        "audit": {"today": 8},
    }


@pytest.mark.asyncio
async def test_build_workflow_summary_returns_real_status_counts(monkeypatch) -> None:
    db = _FakeSystemAdminDB()

    async def _fake_count_profiles(_db, *, workflow_status=None, **_kwargs):
        values = {"SUBMITTED": 1, "LOCKED": 1}
        return values.get(workflow_status, 0)

    async def _fake_count_leave_applications(_db, *, status=None, **_kwargs):
        values = {"RECOMMENDED": 1, "SANCTIONED": 1}
        return values.get(status, 0)

    monkeypatch.setattr(system_admin_router, "count_employee_profiles", _fake_count_profiles)
    monkeypatch.setattr(system_admin_router, "count_leave_applications", _fake_count_leave_applications)

    result = await system_admin_router._build_workflow_summary(db)

    assert result["profile_workflows"]["SUBMITTED"] == 1
    assert result["profile_workflows"]["LOCKED"] == 1
    assert result["service_book_workflows"]["VERIFIED"] == 1
    assert result["service_book_workflows"]["ATTESTED"] == 1
    assert result["leave_workflows"]["RECOMMENDED"] == 1
    assert result["leave_workflows"]["SANCTIONED"] == 1


@pytest.mark.asyncio
async def test_build_stuck_workflow_payload_returns_aged_records() -> None:
    db = _FakeSystemAdminDB()

    result = await system_admin_router._build_stuck_workflow_payload(db, days_threshold=7, limit=10)

    assert result["total"] == 3
    assert result["stuck_profiles"][0]["employee_id"] == "EMP-1"
    assert result["stuck_entries"][0]["entry_id"] == "SB-1"
    assert result["stuck_leaves"][0]["id"] == "LV-1"


@pytest.mark.asyncio
async def test_audit_routes_return_live_logs_and_stats(monkeypatch) -> None:
    class _FrozenDateTime:
        @classmethod
        def now(cls, tz=None):
            return datetime.fromisoformat("2026-04-12T12:00:00+00:00")

        @classmethod
        def fromisoformat(cls, value: str):
            return datetime.fromisoformat(value)

    monkeypatch.setattr(system_admin_router, "datetime", _FrozenDateTime)
    db = _FakeSystemAdminDB()

    logs_payload = await system_admin_router.get_audit_logs(
        limit=10,
        offset=0,
        action_filter=None,
        entity_type_filter="employee_profile",
        from_timestamp="2026-04-12T00:00:00+00:00",
        to_timestamp="2026-04-12T23:59:59+00:00",
        db=db,
        current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
    )
    stats_payload = await system_admin_router.get_audit_stats(
        db=db,
        current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
    )

    assert logs_payload["total"] == 1
    assert logs_payload["logs"][0]["resource_type"] == "employee_profile"
    assert stats_payload["total_logs"] == 2
    assert stats_payload["today_count"] == 1
    assert stats_payload["by_action"] == [
        {"action": "CREATE", "count": 1},
        {"action": "VERIFY", "count": 1},
    ]


@pytest.mark.asyncio
async def test_export_audit_logs_streams_csv_rows() -> None:
    db = _FakeSystemAdminDB()

    response = await system_admin_router.export_audit_logs(
		limit=10,
		action_filter=None,
		entity_type_filter=None,
		from_timestamp=None,
		to_timestamp=None,
        db=db,
        current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
    )

    chunks: list[str] = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)

    body = "".join(chunks)
    assert "timestamp,action,entity_type,entity_id,actor" in body
    assert "2026-04-12T09:15:00+00:00,CREATE,employee_profile,EMP-1,Admin One" in body
    assert "2026-04-11T09:15:00+00:00,VERIFY,servicebook_entry,SB-1,Verifier One" in body


@pytest.mark.asyncio
async def test_export_audit_logs_applies_filters_and_limit() -> None:
    db = _FakeSystemAdminDB()

    response = await system_admin_router.export_audit_logs(
        limit=1,
        action_filter="CREATE",
        entity_type_filter="employee_profile",
        from_timestamp="2026-04-12T00:00:00+00:00",
        to_timestamp="2026-04-12T23:59:59+00:00",
        db=db,
        current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
    )

    chunks: list[str] = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)

    body = "".join(chunks)
    assert "CREATE,employee_profile,EMP-1,Admin One" in body
    assert "VERIFY,servicebook_entry,SB-1,Verifier One" not in body


@pytest.mark.asyncio
async def test_audit_routes_reject_reversed_timestamp_range() -> None:
    db = _FakeSystemAdminDB()

    with pytest.raises(HTTPException) as exc:
        await system_admin_router.get_audit_logs(
            limit=10,
            offset=0,
            action_filter=None,
            entity_type_filter=None,
            from_timestamp="2026-04-13T00:00:00+00:00",
            to_timestamp="2026-04-12T00:00:00+00:00",
            db=db,
            current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "from_timestamp must be less than or equal to to_timestamp."
