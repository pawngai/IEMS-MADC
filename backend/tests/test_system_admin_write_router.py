from __future__ import annotations

import pytest
from fastapi import HTTPException

from contexts.system_admin.api import router as system_admin_router


@pytest.mark.asyncio
async def test_delete_employee_is_forbidden_for_system_admin(monkeypatch) -> None:
    async def _should_not_run(*_args, **_kwargs):
        raise AssertionError("transactional delete contract should not run for SYSTEM_ADMIN")

    monkeypatch.setattr(system_admin_router, "find_profile_view", _should_not_run)
    monkeypatch.setattr(system_admin_router, "count_servicebook_entries", _should_not_run)

    payload = system_admin_router.EmployeeDeleteRequest(reason="Remove duplicate draft employee")

    with pytest.raises(HTTPException) as exc:
        await system_admin_router.delete_employee(
            employee_id="EMP-1",
            payload=payload,
            db=object(),
            current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
        )

    assert exc.value.status_code == 403
    assert exc.value.detail["error_code"] == "SYSTEM_ADMIN_FORBIDDEN"


@pytest.mark.asyncio
async def test_admin_cancel_leave_is_forbidden_for_system_admin(monkeypatch) -> None:
    async def _should_not_run(*_args, **_kwargs):
        raise AssertionError("transactional leave contract should not run for SYSTEM_ADMIN")

    monkeypatch.setattr(system_admin_router, "get_leave_application_by_id", _should_not_run)
    monkeypatch.setattr(system_admin_router, "admin_cancel_leave_application", _should_not_run)

    payload = system_admin_router.EmployeeDeleteRequest(reason="Cancel due to admin override")

    with pytest.raises(HTTPException) as exc:
        await system_admin_router.admin_cancel_leave(
            leave_id="L-1",
            payload=payload,
            db=object(),
            current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-3"},
        )

    assert exc.value.status_code == 403
    assert exc.value.detail["error_code"] == "SYSTEM_ADMIN_FORBIDDEN"


@pytest.mark.asyncio
async def test_unlock_workflow_is_forbidden_for_system_admin() -> None:
    payload = system_admin_router.WorkflowUnlockRequest(reason="Compatibility endpoint should stay blocked")

    with pytest.raises(HTTPException) as exc:
        await system_admin_router.unlock_workflow(
            entity_type="profile",
            entity_id="EMP-1",
            payload=payload,
            current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-4"},
        )

    assert exc.value.status_code == 403
    assert exc.value.detail["error_code"] == "SYSTEM_ADMIN_FORBIDDEN"
