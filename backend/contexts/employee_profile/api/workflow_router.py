from __future__ import annotations

from typing import Optional

from contexts.employee_profile.application.dependencies import get_current_user, get_db
from contexts.employee_profile.application.factory import build_employee_workflow_service
from contexts.employee_profile.application.workflow_actions import (
    approve_profile_action,
    lock_profile_action,
    reject_profile_action,
    submit_profile_action,
    verify_profile_action,
)
from contexts.employee_profile.application.access_scope import enforce_profile_write_scope_or_raise
from contexts.employee_profile.application.policy import DEPARTMENT_SCOPED_ROLES, enforce_system_admin_readonly
from contexts.employee_profile.application.router_support import get_user_id
from contexts.employee_profile.application.services.workflow_engine import EmployeeWorkflowApplicationService
from contexts.employee_profile.contracts.workflow import WorkflowAction, WorkflowActionResponse
from fastapi import APIRouter, Depends, Request
from contexts.identity_access.contracts.user_role import get_user_role

workflow_router = APIRouter()


def get_employee_workflow_service(
    request: Request, db=None
) -> EmployeeWorkflowApplicationService:
    if db is None:
        db = get_db()
    return build_employee_workflow_service(request=request, db=db)


async def _enforce_profile_write_scope(
    current_user: dict,
    user_role: str,
    workflow_service: EmployeeWorkflowApplicationService,
    profile: Optional[dict] = None,
    target_department: Optional[str] = None,
) -> Optional[str]:
    return await enforce_profile_write_scope_or_raise(
        current_user,
        user_role,
        workflow_service,
        DEPARTMENT_SCOPED_ROLES,
        profile=profile,
        target_department=target_department,
    )


@workflow_router.post("/{employee_id}/submit", response_model=WorkflowActionResponse)
async def submit_profile(
    employee_id: str,
    action: WorkflowAction,
    request: Request,
    current_user: dict = Depends(get_current_user),
    workflow_service: EmployeeWorkflowApplicationService = Depends(
        get_employee_workflow_service
    ),
):
    enforce_system_admin_readonly(current_user, "SUBMIT")
    user_role = get_user_role(current_user)
    user_id = get_user_id(current_user)
    payload = await submit_profile_action(
        employee_id=employee_id,
        remarks=action.remarks,
        request=request,
        current_user=current_user,
        user_role=user_role,
        user_id=user_id,
        workflow_service=workflow_service,
        enforce_profile_write_scope_or_raise_fn=_enforce_profile_write_scope,
    )
    return WorkflowActionResponse(**payload)


@workflow_router.post("/{employee_id}/verify", response_model=WorkflowActionResponse)
async def verify_profile(
    employee_id: str,
    action: WorkflowAction,
    request: Request,
    current_user: dict = Depends(get_current_user),
    workflow_service: EmployeeWorkflowApplicationService = Depends(
        get_employee_workflow_service
    ),
):
    enforce_system_admin_readonly(current_user, "VERIFY")
    user_role = get_user_role(current_user)
    user_id = get_user_id(current_user)
    payload = await verify_profile_action(
        employee_id=employee_id,
        remarks=action.remarks,
        request=request,
        current_user=current_user,
        user_role=user_role,
        user_id=user_id,
        workflow_service=workflow_service,
        enforce_profile_write_scope_or_raise_fn=_enforce_profile_write_scope,
    )
    return WorkflowActionResponse(**payload)


@workflow_router.post("/{employee_id}/approve", response_model=WorkflowActionResponse)
async def approve_profile(
    employee_id: str,
    action: WorkflowAction,
    request: Request,
    current_user: dict = Depends(get_current_user),
    workflow_service: EmployeeWorkflowApplicationService = Depends(
        get_employee_workflow_service
    ),
):
    enforce_system_admin_readonly(current_user, "APPROVE")
    user_role = get_user_role(current_user)
    user_id = get_user_id(current_user)
    payload = await approve_profile_action(
        employee_id=employee_id,
        remarks=action.remarks,
        request=request,
        current_user=current_user,
        user_role=user_role,
        user_id=user_id,
        workflow_service=workflow_service,
        enforce_profile_write_scope_or_raise_fn=_enforce_profile_write_scope,
    )
    return WorkflowActionResponse(**payload)


@workflow_router.post("/{employee_id}/lock", response_model=WorkflowActionResponse)
async def lock_profile(
    employee_id: str,
    action: WorkflowAction,
    request: Request,
    current_user: dict = Depends(get_current_user),
    workflow_service: EmployeeWorkflowApplicationService = Depends(
        get_employee_workflow_service
    ),
):
    enforce_system_admin_readonly(current_user, "LOCK")
    user_role = get_user_role(current_user)
    user_id = get_user_id(current_user)
    payload = await lock_profile_action(
        employee_id=employee_id,
        remarks=action.remarks,
        request=request,
        db=get_db(),
        current_user=current_user,
        user_role=user_role,
        user_id=user_id,
        workflow_service=workflow_service,
        enforce_profile_write_scope_or_raise_fn=_enforce_profile_write_scope,
    )
    return WorkflowActionResponse(**payload)


@workflow_router.post("/{employee_id}/reject", response_model=WorkflowActionResponse)
async def reject_profile(
    employee_id: str,
    action: WorkflowAction,
    request: Request,
    current_user: dict = Depends(get_current_user),
    workflow_service: EmployeeWorkflowApplicationService = Depends(
        get_employee_workflow_service
    ),
):
    enforce_system_admin_readonly(current_user, "REJECT")
    user_role = get_user_role(current_user)
    user_id = get_user_id(current_user)
    payload = await reject_profile_action(
        employee_id=employee_id,
        remarks=action.remarks,
        request=request,
        current_user=current_user,
        user_role=user_role,
        user_id=user_id,
        workflow_service=workflow_service,
        enforce_profile_write_scope_or_raise_fn=_enforce_profile_write_scope,
    )
    return WorkflowActionResponse(**payload)


__all__ = ["workflow_router", "get_employee_workflow_service"]

