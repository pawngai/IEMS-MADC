from __future__ import annotations

from typing import Optional

from fastapi import HTTPException

from contexts.employee_profile.application.router_support import get_user_id, normalize_department_code
from contexts.employee_profile.application.services.workflow_engine import EmployeeWorkflowApplicationService


async def get_department_scope_for_user(
    current_user: dict,
    user_role: str,
    workflow_service: EmployeeWorkflowApplicationService,
    department_scoped_roles: set[str],
) -> Optional[str]:
    if user_role not in department_scoped_roles:
        return None

    token_department = normalize_department_code(current_user.get("department_code"))
    if token_department:
        return token_department

    user_id = get_user_id(current_user)
    if user_id:
        user_department = normalize_department_code(
            await workflow_service.get_user_department_code(user_id=user_id)
        )
        if user_department:
            return user_department

    employee_id = current_user.get("employee_id")
    if employee_id:
        profile_department = normalize_department_code(
            await workflow_service.get_profile_department_code(employee_id=employee_id)
        )
        if profile_department:
            return profile_department

    return None


async def enforce_department_scope_or_raise(
    current_user: dict,
    user_role: str,
    workflow_service: EmployeeWorkflowApplicationService,
    department_scoped_roles: set[str],
    requested_department: Optional[str] = None,
) -> Optional[str]:
    scope_department = await get_department_scope_for_user(
        current_user,
        user_role,
        workflow_service,
        department_scoped_roles,
    )
    if user_role in department_scoped_roles and not scope_department:
        raise HTTPException(
            status_code=403,
            detail="Department access is restricted. Map this user to a department first.",
        )

    if not scope_department:
        return None

    requested = normalize_department_code(requested_department)
    if requested and requested != scope_department:
        raise HTTPException(
            status_code=403,
            detail="Department-scoped access only allows your own department records.",
        )
    return scope_department


async def enforce_profile_write_scope_or_raise(
    current_user: dict,
    user_role: str,
    workflow_service: EmployeeWorkflowApplicationService,
    department_scoped_roles: set[str],
    profile: Optional[dict] = None,
    target_department: Optional[str] = None,
) -> Optional[str]:
    if user_role == "EMPLOYEE":
        target_employee_id = str((profile or {}).get("employee_id") or current_user.get("employee_id") or "").strip()
        caller_employee_id = str(current_user.get("employee_id") or "").strip()
        if not caller_employee_id or not target_employee_id or caller_employee_id != target_employee_id:
            raise HTTPException(
                status_code=403,
                detail="Employee self-service access only allows your own profile.",
            )
        return None

    scoped_department = await enforce_department_scope_or_raise(
        current_user,
        user_role,
        workflow_service,
        department_scoped_roles,
        requested_department=target_department,
    )
    if not scoped_department:
        return None

    if profile is not None:
        profile_department = normalize_department_code(profile.get("current_department_id"))
        if profile_department != scoped_department:
            raise HTTPException(
                status_code=403,
                detail="Department-scoped access only allows your own department records.",
            )
    return scoped_department

