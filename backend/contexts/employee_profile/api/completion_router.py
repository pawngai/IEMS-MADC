from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from contexts.employee_profile.application.queries.completion_queries import (
    build_bulk_completion_response,
    calculate_profile_completion,
)
from contexts.employee_profile.application.access_scope import (
    get_department_scope_for_user as _get_department_scope_for_user,
)
from contexts.employee_profile.application.dependencies import get_current_user, get_db
from contexts.employee_profile.application.factory import build_employee_workflow_service
from contexts.employee_profile.application.policy import DEPARTMENT_SCOPED_ROLES
from contexts.employee_profile.application.services.workflow_engine import EmployeeWorkflowApplicationService
from contexts.identity_access.contracts.user_role import get_user_role

completion_router = APIRouter()


def get_employee_workflow_service(
    request: Request, db=None
) -> EmployeeWorkflowApplicationService:
    if db is None:
        db = get_db()
    return build_employee_workflow_service(request=request, db=db)


async def get_department_scope_for_user(
    current_user: dict,
    user_role: str,
    workflow_service: EmployeeWorkflowApplicationService,
) -> Optional[str]:
    return await _get_department_scope_for_user(
        current_user,
        user_role,
        workflow_service,
        DEPARTMENT_SCOPED_ROLES,
    )


@completion_router.get("/completion/bulk")
async def get_bulk_completion(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
    workflow_service: EmployeeWorkflowApplicationService = Depends(
        get_employee_workflow_service
    ),
):
    user_role = get_user_role(current_user)
    dept_scope = await get_department_scope_for_user(
        current_user, user_role, workflow_service
    )

    query: dict = {}
    if dept_scope:
        query["current_department_id"] = dept_scope

    profiles = await workflow_service.list_profile_records_for_completion(
        query=query, limit=5000
    )
    return build_bulk_completion_response(profiles)


@completion_router.get("/{employee_id}/completion")
async def get_profile_completion(
    employee_id: str,
    current_user: dict = Depends(get_current_user),
    workflow_service: EmployeeWorkflowApplicationService = Depends(
        get_employee_workflow_service
    ),
):
    profile = await workflow_service.get_employee_record(employee_id=employee_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    completion = calculate_profile_completion(profile)
    completion["employee_id"] = employee_id
    completion["full_name"] = profile.get("full_name")
    return completion

