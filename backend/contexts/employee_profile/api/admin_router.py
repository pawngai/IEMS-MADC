from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Request

from contexts.employee_profile.application.commands.profile_commands import (
    delete_profile_response,
    get_audit_trail_response,
)
from contexts.employee_profile.application.access_scope import (
    enforce_department_scope_or_raise as _enforce_department_scope_or_raise,
    enforce_profile_write_scope_or_raise as _enforce_profile_write_scope_or_raise,
)
from contexts.employee_profile.application.dependencies import get_current_user, get_db
from contexts.employee_profile.application.factory import build_employee_workflow_service
from contexts.employee_profile.application.policy import (
    DATA_ENTRY_ROLES,
    DEPARTMENT_SCOPED_ROLES,
    enforce_system_admin_readonly as _enforce_system_admin_readonly,
)
from contexts.employee_profile.application.router_support import (
    get_user_id,
    normalize_department_code as _normalize_department_code,
)
from contexts.employee_profile.application.services.workflow_engine import EmployeeWorkflowApplicationService
from contexts.employee_profile.contracts.workflow import WorkflowStatus
from contexts.identity.contracts.user_role import get_user_role

admin_router = APIRouter()


def get_employee_workflow_service(
    request: Request, db=None
) -> EmployeeWorkflowApplicationService:
    if db is None:
        db = get_db()
    return build_employee_workflow_service(request=request, db=db)


def enforce_system_admin_readonly(user: dict, action: str):
    return _enforce_system_admin_readonly(user, action)


async def enforce_department_scope_or_raise(
    current_user: dict,
    user_role: str,
    workflow_service: EmployeeWorkflowApplicationService,
    requested_department: Optional[str] = None,
) -> Optional[str]:
    return await _enforce_department_scope_or_raise(
        current_user,
        user_role,
        workflow_service,
        DEPARTMENT_SCOPED_ROLES,
        requested_department=requested_department,
    )


async def enforce_profile_write_scope_or_raise(
    current_user: dict,
    user_role: str,
    workflow_service: EmployeeWorkflowApplicationService,
    profile: Optional[dict] = None,
    target_department: Optional[str] = None,
) -> Optional[str]:
    return await _enforce_profile_write_scope_or_raise(
        current_user,
        user_role,
        workflow_service,
        DEPARTMENT_SCOPED_ROLES,
        profile=profile,
        target_department=target_department,
    )


@admin_router.get("/{employee_id}/audit-trail", response_model=dict)
async def get_audit_trail(
    employee_id: str,
    current_user: dict = Depends(get_current_user),
    workflow_service: EmployeeWorkflowApplicationService = Depends(
        get_employee_workflow_service
    ),
):
    user_role = get_user_role(current_user)
    return await get_audit_trail_response(
        employee_id=employee_id,
        current_user=current_user,
        user_role=user_role,
        workflow_service=workflow_service,
        enforce_department_scope_or_raise_fn=enforce_department_scope_or_raise,
        normalize_department_code_fn=_normalize_department_code,
    )


@admin_router.delete("/{employee_id}", response_model=dict)
async def delete_profile(
    employee_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    workflow_service: EmployeeWorkflowApplicationService = Depends(
        get_employee_workflow_service
    ),
):
    enforce_system_admin_readonly(current_user, "DELETE")
    user_role = get_user_role(current_user)
    user_id = get_user_id(current_user)
    return await delete_profile_response(
        employee_id=employee_id,
        request=request,
        current_user=current_user,
        user_role=user_role,
        user_id=user_id,
        workflow_service=workflow_service,
        enforce_profile_write_scope_or_raise_fn=enforce_profile_write_scope_or_raise,
        data_entry_roles=set(DATA_ENTRY_ROLES),
        draft_status_value=WorkflowStatus.DRAFT.value,
    )

