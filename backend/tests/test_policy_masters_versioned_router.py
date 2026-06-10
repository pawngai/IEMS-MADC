from __future__ import annotations

import pytest
from fastapi import HTTPException

from app_platform.reference_data.api import versioned_router
from app_platform.db.runtime import mongo_state


@pytest.mark.asyncio
async def test_list_master_records_requires_system_admin(monkeypatch) -> None:
    def _should_not_hit_db():
        raise AssertionError("get_db should not be called for unauthorized requests")

    monkeypatch.setattr(versioned_router, "get_db", _should_not_hit_db)

    with pytest.raises(HTTPException) as exc:
        await versioned_router.list_master_records(
            master_type=versioned_router.MasterType.EMPLOYMENT_TYPE,
            include_inactive=False,
            current_user={"authorities": ["DEPARTMENT_ADMIN"], "sub": "u-1"},
        )

    assert exc.value.status_code == 403
    assert exc.value.detail["error_code"] == "SYSTEM_ADMIN_REQUIRED"


@pytest.mark.asyncio
async def test_get_master_record_requires_system_admin(monkeypatch) -> None:
    def _should_not_hit_db():
        raise AssertionError("get_db should not be called for unauthorized requests")

    monkeypatch.setattr(versioned_router, "get_db", _should_not_hit_db)

    with pytest.raises(HTTPException) as exc:
        await versioned_router.get_master_record(
            master_type=versioned_router.MasterType.EMPLOYMENT_TYPE,
            code="REGULAR",
            current_user={"authorities": ["DEPARTMENT_ADMIN"], "sub": "u-2"},
        )

    assert exc.value.status_code == 403
    assert exc.value.detail["error_code"] == "SYSTEM_ADMIN_REQUIRED"


@pytest.mark.asyncio
async def test_list_master_records_returns_503_when_database_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(mongo_state, "db", None)

    with pytest.raises(HTTPException) as exc:
        await versioned_router.list_master_records(
            master_type=versioned_router.MasterType.EMPLOYMENT_TYPE,
            include_inactive=False,
            current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
        )

    assert exc.value.status_code == 503
    assert exc.value.detail == "Database not available"


class _FakeCollection:
    def __init__(self, find_one_result: dict | None = None):
        self.find_one_result = find_one_result
        self.inserted: list[dict] = []
        self.updated: list[tuple[tuple, dict]] = []

    async def find_one(self, *_args, **_kwargs):
        return self.find_one_result

    async def insert_one(self, _doc: dict):
        self.inserted.append(_doc)
        return None

    async def update_one(self, *args, **kwargs):
        self.updated.append((args, kwargs))
        return None


class _FakeDb:
    def __init__(self, collection: _FakeCollection | None = None):
        self.collection = collection or _FakeCollection()

    def __getitem__(self, _name: str):
        return self.collection


@pytest.mark.asyncio
async def test_update_master_record_response_message_uses_ascii_arrow(monkeypatch) -> None:
    monkeypatch.setattr(versioned_router, "get_db", lambda: _FakeDb())

    async def _fake_get_required_active_record(_collection, _code: str):
        current = {
            "id": "rec-1",
            "code": "REGULAR",
            "name": "Regular",
            "description": "Regular employee",
            "metadata": {},
            "version": 1,
            "is_active": True,
            "created_at": "2026-01-01T00:00:00+00:00",
            "created_by": "seed",
        }
        return dict(current), dict(current)

    monkeypatch.setattr(
        versioned_router,
        "get_required_active_record",
        _fake_get_required_active_record,
    )
    monkeypatch.setattr(versioned_router, "actor_identity", lambda _user: ("admin-1", "admin@example.com"))

    def _fake_build_updated_version_record(*, code, current_record, updated_name, updated_description, updated_metadata, created_by):
        next_record = dict(current_record)
        next_record.update(
            {
                "id": "rec-2",
                "code": code,
                "name": updated_name or current_record["name"],
                "description": updated_description,
                "metadata": updated_metadata or current_record.get("metadata") or {},
                "version": 2,
                "created_by": created_by,
            }
        )
        return next_record, 2, "2026-01-02T00:00:00+00:00"

    monkeypatch.setattr(
        versioned_router,
        "build_updated_version_record",
        _fake_build_updated_version_record,
    )

    async def _fake_supersede_active_record(**_kwargs):
        return None

    async def _fake_log_master_change(**_kwargs):
        return "audit-1"

    monkeypatch.setattr(versioned_router, "supersede_active_record", _fake_supersede_active_record)
    monkeypatch.setattr(versioned_router, "log_master_change", _fake_log_master_change)

    result = await versioned_router.update_master_record(
        master_type=versioned_router.MasterType.EMPLOYMENT_TYPE,
        code="REGULAR",
        data=versioned_router.MasterRecordUpdate(
            name="Regular Staff",
            description="Updated",
            reason="Update label for consistency",
        ),
        current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
    )

    assert "->" in result["message"]
    assert "Ã" not in result["message"]


@pytest.mark.asyncio
async def test_workflow_stage_master_create_is_read_only(monkeypatch) -> None:
    def _should_not_hit_db():
        raise AssertionError("get_db should not be called for read-only workflow stage writes")

    monkeypatch.setattr(versioned_router, "get_db", _should_not_hit_db)

    with pytest.raises(HTTPException) as exc:
        await versioned_router.create_master_record(
            master_type=versioned_router.MasterType.WORKFLOW_STAGE,
            data=versioned_router.MasterRecordCreate(
                code="TEST",
                name="Test",
                metadata={},
            ),
            current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
        )

    assert exc.value.status_code == 403
    assert exc.value.detail["error_code"] == "READ_ONLY_MASTER_TYPE"


@pytest.mark.asyncio
async def test_workflow_stage_master_update_is_read_only(monkeypatch) -> None:
    def _should_not_hit_db():
        raise AssertionError("get_db should not be called for read-only workflow stage writes")

    monkeypatch.setattr(versioned_router, "get_db", _should_not_hit_db)

    with pytest.raises(HTTPException) as exc:
        await versioned_router.update_master_record(
            master_type=versioned_router.MasterType.WORKFLOW_STAGE,
            code="APPROVED",
            data=versioned_router.MasterRecordUpdate(
                name="Approved",
                reason="Attempting prohibited derived-master update",
            ),
            current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
        )

    assert exc.value.status_code == 403
    assert exc.value.detail["error_code"] == "READ_ONLY_MASTER_TYPE"


@pytest.mark.asyncio
async def test_workflow_stage_master_deprecate_is_read_only(monkeypatch) -> None:
    def _should_not_hit_db():
        raise AssertionError("get_db should not be called for read-only workflow stage writes")

    monkeypatch.setattr(versioned_router, "get_db", _should_not_hit_db)

    with pytest.raises(HTTPException) as exc:
        await versioned_router.deprecate_master_record(
            master_type=versioned_router.MasterType.WORKFLOW_STAGE,
            code="APPROVED",
            reason="Attempting prohibited derived-master deprecation",
            current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
        )

    assert exc.value.status_code == 403
    assert exc.value.detail["error_code"] == "READ_ONLY_MASTER_TYPE"


@pytest.mark.asyncio
async def test_create_master_record_rejects_invalid_pay_level_metadata(monkeypatch) -> None:
    collection = _FakeCollection(find_one_result=None)
    monkeypatch.setattr(versioned_router, "get_db", lambda: _FakeDb(collection))

    with pytest.raises(HTTPException) as exc:
        await versioned_router.create_master_record(
            master_type=versioned_router.MasterType.PAY_LEVEL,
            data=versioned_router.MasterRecordCreate(
                code="l15",
                name="Level 15",
                metadata={
                    "pay_band": "PB-2",
                    "basic_min": 50000,
                    "basic_max": 40000,
                },
            ),
            current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Basic Max must be greater than or equal to Basic Min"
    assert collection.inserted == []


@pytest.mark.asyncio
async def test_create_master_record_normalizes_leave_metadata_and_code(monkeypatch) -> None:
    collection = _FakeCollection(find_one_result=None)
    monkeypatch.setattr(versioned_router, "get_db", lambda: _FakeDb(collection))
    monkeypatch.setattr(versioned_router, "actor_identity", lambda _user: ("admin-1", "admin@example.com"))

    async def _fake_log_master_change(**_kwargs):
        return "audit-1"

    monkeypatch.setattr(versioned_router, "log_master_change", _fake_log_master_change)

    result = await versioned_router.create_master_record(
        master_type=versioned_router.MasterType.LEAVE_TYPE,
        data=versioned_router.MasterRecordCreate(
            code="ml",
            name=" Maternity Leave ",
            description=" Leave policy ",
            metadata={
                "leave_code": "WRONG",
                "max_days_per_year": "180",
                "max_days_per_spell": "180",
                "is_encashable": False,
                "is_accumulative": False,
                "applicable_employment_types": ["reg", "dep", "reg"],
            },
        ),
        current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1", "email": "admin@example.com"},
    )

    assert result["record"]["code"] == "ML"
    assert result["record"]["name"] == "Maternity Leave"
    assert result["record"]["description"] == "Leave policy"
    assert result["record"]["metadata"]["leave_code"] == "ML"
    assert result["record"]["metadata"]["max_days_per_spell"] == 180
    assert result["record"]["metadata"]["applicable_employment_types"] == ["REG", "DEP"]


@pytest.mark.asyncio
async def test_update_master_record_rejects_self_parent_department(monkeypatch) -> None:
    collection = _FakeCollection()
    monkeypatch.setattr(versioned_router, "get_db", lambda: _FakeDb(collection))

    async def _fake_get_required_active_record(_collection, _code: str):
        current = {
            "id": "rec-1",
            "code": "HR",
            "name": "Human Resources",
            "description": "Department",
            "metadata": {
                "parent_department_code": "ADMIN",
            },
            "version": 1,
            "is_active": True,
            "created_at": "2026-01-01T00:00:00+00:00",
            "created_by": "seed",
        }
        return dict(current), dict(current)

    monkeypatch.setattr(
        versioned_router,
        "get_required_active_record",
        _fake_get_required_active_record,
    )

    with pytest.raises(HTTPException) as exc:
        await versioned_router.update_master_record(
            master_type=versioned_router.MasterType.DEPARTMENT,
            code="hr",
            data=versioned_router.MasterRecordUpdate(
                metadata={"parent_department_code": "HR"},
                reason="Prevent invalid self parent",
            ),
            current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Parent Department cannot be the same as the record code"
    assert collection.inserted == []
