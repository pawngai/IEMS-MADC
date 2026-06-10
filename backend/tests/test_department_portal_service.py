from __future__ import annotations

import pytest
from fastapi import HTTPException
from types import SimpleNamespace

from contexts.department.services import department_portal_service
from contexts.identity_access.rbac.domain.models import Permission


def test_require_department_authority_rejects_global_scope() -> None:
    with pytest.raises(HTTPException) as exc:
        department_portal_service._require_department_authority(
            {
                "authorities": ["GLOBAL_DATA_ENTRY"],
                "permissions": [Permission.IDENTITY_READ_ALL.value],
            }
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "Department portal requires department-scoped access."


def test_require_department_authority_allows_department_scope() -> None:
    department_portal_service._require_department_authority(
        {
            "authorities": ["DEPT_DATA_ENTRY"],
            "permissions": [Permission.IDENTITY_READ_ALL.value],
        }
    )


@pytest.mark.asyncio
async def test_get_dashboard_rejects_global_scope_before_db_lookup() -> None:
    with pytest.raises(HTTPException) as exc:
        await department_portal_service.get_dashboard(
            None,
            current_user={
                "authorities": ["GLOBAL_DATA_ENTRY"],
                "permissions": [Permission.IDENTITY_READ_ALL.value],
            },
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "Department portal requires department-scoped access."


@pytest.mark.asyncio
async def test_get_employees_uses_true_page_total_and_forwards_filters(monkeypatch) -> None:
    captured = {}

    async def _fake_resolve_department(_db, current_user):
        assert current_user["authorities"] == ["DEPT_DATA_ENTRY"]
        return "FIN"

    async def _fake_list_employees(_db, department_code, **kwargs):
        captured["list"] = {"department_code": department_code, **kwargs}
        return [
            {
                "employee_id": "EMP-001",
                "employee_code": "E-001",
                "full_name": "Alice",
                "workflow_status": "APPROVED",
            }
        ]

    async def _fake_count_employees(_db, department_code, **kwargs):
        captured["count"] = {"department_code": department_code, **kwargs}
        return 47

    async def _fake_find_user_by_employee_id(_db, *, employee_id, projection=None):
        assert projection == {"_id": 0, "email": 1}
        return {"email": "alice@madc.gov.in"} if employee_id == "EMP-001" else None

    monkeypatch.setattr(department_portal_service, "_resolve_department", _fake_resolve_department)
    monkeypatch.setattr(department_portal_service.repo, "list_employees", _fake_list_employees)
    monkeypatch.setattr(department_portal_service.repo, "count_employees", _fake_count_employees)
    monkeypatch.setattr(department_portal_service, "find_user_by_employee_id", _fake_find_user_by_employee_id)

    result = await department_portal_service.get_employees(
        SimpleNamespace(),
        current_user={
            "authorities": ["DEPT_DATA_ENTRY"],
            "permissions": [Permission.IDENTITY_READ_ALL.value],
        },
        search="alice",
        workflow_status="APPROVED",
        employment_type="REGULAR",
        designation_id="SO",
        office_id="HQ",
        employee_status="ACTIVE",
        recruitment_mode="DIRECT",
        pay_level="LEVEL_7",
        service="MCS",
        service_group="GROUP_B",
        date_from="2020-01-01",
        date_to="2020-12-31",
        sort_by="employee_code",
        sort_dir="desc",
        page=3,
        page_size=10,
    )

    assert captured["list"] == {
        "department_code": "FIN",
        "search": "alice",
        "workflow_status": "APPROVED",
        "employment_type": "REGULAR",
        "designation_id": "SO",
        "office_id": "HQ",
        "employee_status": "ACTIVE",
        "recruitment_mode": "DIRECT",
        "pay_level": "LEVEL_7",
        "service": "MCS",
        "service_group": "GROUP_B",
        "date_from": "2020-01-01",
        "date_to": "2020-12-31",
        "limit": 10,
        "offset": 20,
        "sort_by": "employee_code",
        "sort_dir": "desc",
    }
    assert captured["count"] == {
        "department_code": "FIN",
        "search": "alice",
        "workflow_status": "APPROVED",
        "employment_type": "REGULAR",
        "designation_id": "SO",
        "office_id": "HQ",
        "employee_status": "ACTIVE",
        "recruitment_mode": "DIRECT",
        "pay_level": "LEVEL_7",
        "service": "MCS",
        "service_group": "GROUP_B",
        "date_from": "2020-01-01",
        "date_to": "2020-12-31",
    }
    assert result["total"] == 47
    assert result["total_pages"] == 5
    assert result["employees"][0]["has_login_account"] is True
    assert "can_reset_password" not in result["employees"][0]
    assert "can_provision_account" not in result["employees"][0]
    assert result["employees"][0]["account_email"] == "alice@madc.gov.in"


@pytest.mark.asyncio
async def test_get_employees_marks_missing_account_rows_as_not_resettable(monkeypatch) -> None:
    async def _fake_resolve_department(_db, _current_user):
        return "FIN"

    async def _fake_list_employees(_db, _department_code, **_kwargs):
        return [{"employee_id": "EMP-002", "workflow_status": "LOCKED"}]

    async def _fake_count_employees(_db, _department_code, **_kwargs):
        return 1

    async def _fake_find_user_by_employee_id(_db, *, employee_id, projection=None):
        assert employee_id == "EMP-002"
        assert projection == {"_id": 0, "email": 1}
        return None

    monkeypatch.setattr(department_portal_service, "_resolve_department", _fake_resolve_department)
    monkeypatch.setattr(department_portal_service.repo, "list_employees", _fake_list_employees)
    monkeypatch.setattr(department_portal_service.repo, "count_employees", _fake_count_employees)
    monkeypatch.setattr(department_portal_service, "find_user_by_employee_id", _fake_find_user_by_employee_id)

    result = await department_portal_service.get_employees(
        SimpleNamespace(),
        current_user={
            "authorities": ["DEPT_DATA_ENTRY"],
            "permissions": [Permission.IDENTITY_READ_ALL.value],
        },
    )

    assert result["employees"][0]["has_login_account"] is False
    assert "can_reset_password" not in result["employees"][0]
    assert "can_provision_account" not in result["employees"][0]


@pytest.mark.asyncio
async def test_get_sanctioned_strength_returns_derived_totals(monkeypatch) -> None:
    async def _fake_resolve_department(_db, _current_user):
        return "FIN"

    async def _fake_get_department_info(_db, department_code):
        assert department_code == "FIN"
        return {"code": "FIN", "name": "Finance"}

    async def _fake_get_department_establishment_rows(_db, department_code):
        assert department_code == "FIN"
        return [
            {
                "designation_code": "SO",
                "employment_type": "REGULAR",
                "sanctioned_count": 10,
            },
            {"designation_code": "ASO", "employment_type": None, "sanctioned_count": 2},
        ]

    async def _fake_count_active_employees_for_establishment_row(
        _db,
        department_code,
        *,
        designation_code,
        employment_type=None,
    ):
        assert department_code == "FIN"
        if designation_code == "SO":
            assert employment_type == "REGULAR"
            return 7
        if designation_code == "ASO":
            assert employment_type is None
            return 3
        return 0

    monkeypatch.setattr(department_portal_service, "_resolve_department", _fake_resolve_department)
    monkeypatch.setattr(department_portal_service.repo, "get_department_info", _fake_get_department_info)
    monkeypatch.setattr(
        department_portal_service.repo,
        "get_department_establishment_rows",
        _fake_get_department_establishment_rows,
    )
    monkeypatch.setattr(
        department_portal_service.repo,
        "count_active_employees_for_establishment_row",
        _fake_count_active_employees_for_establishment_row,
    )

    result = await department_portal_service.get_sanctioned_strength(
        SimpleNamespace(),
        current_user={
            "authorities": ["DEPT_DATA_ENTRY"],
            "permissions": [Permission.IDENTITY_READ_ALL.value],
        },
    )

    assert result["department_code"] == "FIN"
    assert result["department_name"] == "Finance"
    assert result["configured"] is True
    assert result["total_rows"] == 2
    assert result["totals"] == {
        "sanctioned_strength_total": 12,
        "filled_strength_total": 10,
        "vacancy_count": 3,
        "over_strength_count": 1,
    }
    by_designation = {
        item["designation_code"]: item
        for item in result["items"]
    }
    assert by_designation["ASO"]["over_strength_count"] == 1
    assert by_designation["SO"]["vacancy_count"] == 3


@pytest.mark.asyncio
async def test_update_sanctioned_strength_persists_department_owned_rows(monkeypatch) -> None:
    captured = {}

    async def _fake_resolve_department(_db, _current_user):
        return "FIN"

    async def _fake_upsert_department_establishment(
        _db,
        department_code,
        *,
        items,
        reason,
        actor_id,
        actor_email,
    ):
        captured["upsert"] = {
            "department_code": department_code,
            "items": items,
            "reason": reason,
            "actor_id": actor_id,
            "actor_email": actor_email,
        }
        return {"department_code": department_code, "items": items}

    async def _fake_get_department_establishment_rows(_db, department_code):
        assert department_code == "FIN"
        return captured["upsert"]["items"]

    async def _fake_count_active_employees_for_establishment_row(
        _db,
        department_code,
        *,
        designation_code,
        employment_type=None,
    ):
        assert department_code == "FIN"
        assert designation_code == "SO"
        assert employment_type is None
        return 2

    monkeypatch.setattr(department_portal_service, "_resolve_department", _fake_resolve_department)
    monkeypatch.setattr(
        department_portal_service.repo,
        "upsert_department_establishment",
        _fake_upsert_department_establishment,
    )
    monkeypatch.setattr(
        department_portal_service.repo,
        "get_department_establishment_rows",
        _fake_get_department_establishment_rows,
    )
    monkeypatch.setattr(
        department_portal_service.repo,
        "count_active_employees_for_establishment_row",
        _fake_count_active_employees_for_establishment_row,
    )

    result = await department_portal_service.update_sanctioned_strength(
        SimpleNamespace(),
        current_user={
            "sub": "user-1",
            "email": "hod@madc.gov.in",
            "authorities": ["HOD"],
            "permissions": [Permission.PROFILE_UPDATE_ALL.value],
        },
        rows=[
            {
                "designation_code": "so",
                "employment_type": None,
                "sanctioned_count": 5,
                "order_number": "12/2026",
                "order_date": "2026-04-04",
                "remarks": "Revised",
            }
        ],
        reason="Annual review",
    )

    assert captured["upsert"] == {
        "department_code": "FIN",
        "items": [
            {
                "designation_code": "SO",
                "employment_type": None,
                "sanctioned_count": 5,
                "order_number": "12/2026",
                "order_date": "2026-04-04",
                "remarks": "Revised",
            }
        ],
        "reason": "Annual review",
        "actor_id": "user-1",
        "actor_email": "hod@madc.gov.in",
    }
    assert result["success"] is True
    assert result["department_code"] == "FIN"
    assert result["totals"] == {
        "sanctioned_strength_total": 5,
        "filled_strength_total": 2,
        "vacancy_count": 3,
        "over_strength_count": 0,
    }


@pytest.mark.asyncio
async def test_system_admin_gets_sanctioned_strength_for_selected_department(monkeypatch) -> None:
    async def _fake_get_department_info(_db, department_code):
        assert department_code == "FIN"
        return {"code": "FIN", "name": "Finance"}

    async def _fake_get_department_establishment_rows(_db, department_code):
        assert department_code == "FIN"
        return [{"designation_code": "SO", "employment_type": None, "sanctioned_count": 4}]

    async def _fake_count_active_employees_for_establishment_row(
        _db,
        department_code,
        *,
        designation_code,
        employment_type=None,
    ):
        assert department_code == "FIN"
        assert designation_code == "SO"
        assert employment_type is None
        return 1

    monkeypatch.setattr(department_portal_service.repo, "get_department_info", _fake_get_department_info)
    monkeypatch.setattr(
        department_portal_service.repo,
        "get_department_establishment_rows",
        _fake_get_department_establishment_rows,
    )
    monkeypatch.setattr(
        department_portal_service.repo,
        "count_active_employees_for_establishment_row",
        _fake_count_active_employees_for_establishment_row,
    )

    result = await department_portal_service.sanctioned_strength_service.get_sanctioned_strength_for_department_admin(
        SimpleNamespace(),
        "fin",
        current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
    )

    assert result["department_code"] == "FIN"
    assert result["department_name"] == "Finance"
    assert result["totals"] == {
        "sanctioned_strength_total": 4,
        "filled_strength_total": 1,
        "vacancy_count": 3,
        "over_strength_count": 0,
    }


@pytest.mark.asyncio
async def test_system_admin_update_sanctioned_strength_uses_department_establishment_repo(monkeypatch) -> None:
    captured = {}

    async def _fake_get_department_info(_db, department_code):
        assert department_code == "FIN"
        return {"code": "FIN", "name": "Finance"}

    async def _fake_upsert_department_establishment(
        _db,
        department_code,
        *,
        items,
        reason,
        actor_id,
        actor_email,
    ):
        captured["upsert"] = {
            "department_code": department_code,
            "items": items,
            "reason": reason,
            "actor_id": actor_id,
            "actor_email": actor_email,
        }
        return {"department_code": department_code, "items": items}

    async def _fake_get_department_establishment_rows(_db, department_code):
        assert department_code == "FIN"
        return captured["upsert"]["items"]

    async def _fake_count_active_employees_for_establishment_row(
        _db,
        department_code,
        *,
        designation_code,
        employment_type=None,
    ):
        assert department_code == "FIN"
        assert designation_code == "SO"
        assert employment_type is None
        return 2

    monkeypatch.setattr(department_portal_service.repo, "get_department_info", _fake_get_department_info)
    monkeypatch.setattr(
        department_portal_service.repo,
        "upsert_department_establishment",
        _fake_upsert_department_establishment,
    )
    monkeypatch.setattr(
        department_portal_service.repo,
        "get_department_establishment_rows",
        _fake_get_department_establishment_rows,
    )
    monkeypatch.setattr(
        department_portal_service.repo,
        "count_active_employees_for_establishment_row",
        _fake_count_active_employees_for_establishment_row,
    )

    result = await department_portal_service.sanctioned_strength_service.update_sanctioned_strength_for_department_admin(
        SimpleNamespace(),
        "fin",
        current_user={
            "sub": "admin-1",
            "email": "admin@madc.gov.in",
            "authorities": ["SYSTEM_ADMIN"],
        },
        rows=[{"designation_code": "so", "sanctioned_count": 6}],
        reason="Correct sanctioned strength from order",
    )

    assert captured["upsert"] == {
        "department_code": "FIN",
        "items": [
            {
                "designation_code": "SO",
                "employment_type": None,
                "sanctioned_count": 6,
                "order_number": None,
                "order_date": None,
                "remarks": None,
            }
        ],
        "reason": "Correct sanctioned strength from order",
        "actor_id": "admin-1",
        "actor_email": "admin@madc.gov.in",
    }
    assert result["success"] is True
    assert result["department_code"] == "FIN"
    assert result["department_name"] == "Finance"


@pytest.mark.asyncio
async def test_get_pending_work_uses_workflow_remarks_for_rejected_items(monkeypatch) -> None:
    async def _fake_resolve_department(_db, _current_user):
        return "FIN"

    async def _fake_list_employees(_db, department_code, *, workflow_status=None, **_kwargs):
        assert department_code == "FIN"
        if workflow_status == "DRAFT":
            return [
                {
                    "employee_id": "EMP-001",
                    "employee_code": "E-001",
                    "full_name": "Draft User",
                    "employment_type": "REGULAR",
                    "updated_at": "2026-04-04T10:00:00+00:00",
                }
            ]
        if workflow_status == "REJECTED":
            return [
                {
                    "employee_id": "EMP-002",
                    "employee_code": "E-002",
                    "full_name": "Rejected User",
                    "employment_type": "REGULAR",
                    "updated_at": "2026-04-05T10:00:00+00:00",
                    "workflow_remarks": "Upload clearer supporting documents.",
                }
            ]
        return []

    monkeypatch.setattr(department_portal_service, "_resolve_department", _fake_resolve_department)
    monkeypatch.setattr(department_portal_service.repo, "list_employees", _fake_list_employees)

    result = await department_portal_service.get_pending_work(
        SimpleNamespace(),
        current_user={
            "authorities": ["DEPT_DATA_ENTRY"],
            "permissions": [Permission.IDENTITY_READ_ALL.value],
        },
    )

    assert result["total"] == 2
    assert result["draft_count"] == 1
    assert result["rejected_count"] == 1
    rejected_item = next(item for item in result["items"] if item["workflow_status"] == "REJECTED")
    assert rejected_item["rejection_reason"] == "Upload clearer supporting documents."
    assert rejected_item["action_needed"] == "Fix issues and re-submit profile"
