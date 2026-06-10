from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Optional

from contexts.employee_profile.application.profile_interface import get_employee_identity
from contexts.employee_profile.application.services.workflow_engine import EmployeeWorkflowApplicationService
from fastapi import HTTPException
from contexts.rbac.contracts.models import Permission
from contexts.rbac.contracts.access_control import has_permission, is_owner
from contexts.employee_profile.contracts.workflow_status_utils import (
    normalize_employee_workflow_status,
    normalize_workflow_status,
    workflow_status_filter_values,
)

EnforceDepartmentScopeFn = Callable[
    [dict, str, EmployeeWorkflowApplicationService, Optional[str]],
    Awaitable[Optional[str]],
]
NormalizeDepartmentCodeFn = Callable[[Optional[str]], Optional[str]]
FindEmployeeAccountFn = Callable[..., Awaitable[dict | None]]


async def list_profiles_response(
    *,
    db: Any,
    search: Optional[str],
    status: Optional[str],
    workflow_status: Optional[str],
    department_id: Optional[str],
    employment_type: Optional[str],
    designation_id: Optional[str] = None,
    office_id: Optional[str] = None,
    employee_status: Optional[str] = None,
    recruitment_mode: Optional[str] = None,
    pay_level: Optional[str] = None,
    service: Optional[str] = None,
    service_group: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    force_all: Optional[bool],
    sort_by: Optional[str] = None,
    sort_dir: str = "asc",
    page: int,
    page_size: int,
    current_user: dict,
    user_role: str,
    workflow_service: EmployeeWorkflowApplicationService,
    enforce_department_scope_or_raise_fn: EnforceDepartmentScopeFn,
    data_entry_roles: set[str],
    role_verifier: str,
    role_approver: str,
    find_employee_account_by_employee_id_fn: FindEmployeeAccountFn | None = None,
    profile_workflow_only: bool = False,
) -> dict[str, Any]:
    if has_permission(current_user, Permission.PROFILE_READ_ALL):
        pass
    elif has_permission(current_user, Permission.PROFILE_READ_OWN):
        if not current_user.get("employee_id"):
            raise HTTPException(
                status_code=403, detail="No employee profile linked to user"
            )
    else:
        raise HTTPException(
            status_code=403, detail="Insufficient permission to view profiles"
        )

    scoped_department = await enforce_department_scope_or_raise_fn(
        current_user,
        user_role,
        workflow_service,
        requested_department=department_id,
    )
    if scoped_department:
        department_id = scoped_department
        force_all = False

    query: dict[str, Any] = {}
    if not status and workflow_status:
        status = workflow_status
    if status:
        status = normalize_workflow_status(status) or status

    normalized_search = str(search or "").strip()
    if normalized_search:
        query["$or"] = [
            {"full_name": {"$regex": normalized_search, "$options": "i"}},
            {"employee_id": {"$regex": normalized_search, "$options": "i"}},
            {"employee_code": {"$regex": normalized_search, "$options": "i"}},
            {"current_department_id": {"$regex": normalized_search, "$options": "i"}},
            {"current_designation_id": {"$regex": normalized_search, "$options": "i"}},
        ]

    if not force_all:
        if status:
            status_values = workflow_status_filter_values(status)
            query["workflow_status"] = (
                status_values[0] if len(status_values) == 1 else {"$in": status_values}
            )
            if profile_workflow_only and "DRAFT" in status_values:
                query["identity_workflow_status"] = "ACTIVE"
        if department_id:
            query["current_department_id"] = department_id
        if employment_type:
            query["employment_type"] = employment_type
        if designation_id:
            query["current_designation_id"] = designation_id
        if office_id:
            query["current_office_id"] = office_id
        if employee_status:
            query["employee_status"] = employee_status
        if recruitment_mode:
            query["mode_of_recruitment"] = recruitment_mode
        if pay_level:
            query["pay_level"] = pay_level
        if service:
            query["service"] = service
        if service_group:
            query["group"] = service_group
        if date_from or date_to:
            date_cond: dict[str, str] = {}
            if date_from:
                date_cond["$gte"] = date_from
            if date_to:
                date_cond["$lte"] = date_to
            query["date_of_initial_engagement"] = date_cond

        if user_role in data_entry_roles:
            pass
        elif user_role == role_verifier:
            if not status:
                query["workflow_status"] = {
                    "$in": ["SUBMITTED", "VERIFIED", "APPROVED", "LOCKED"]
                }
        elif user_role == role_approver:
            if not status:
                query["workflow_status"] = {"$in": ["VERIFIED", "APPROVED", "LOCKED"]}
        elif has_permission(current_user, Permission.PROFILE_READ_ALL):
            pass
        elif has_permission(current_user, Permission.PROFILE_READ_OWN):
            query["employee_id"] = current_user.get("employee_id")
    else:
        if not has_permission(current_user, Permission.PROFILE_READ_ALL):
            raise HTTPException(
                status_code=403, detail="Insufficient permission to view profiles"
            )

    if hasattr(workflow_service, "count_profile_views"):
        total = await workflow_service.count_profile_views(query=query)
    else:
        total = await workflow_service.count_profile_records(query=query)
    skip = (page - 1) * page_size
    mongo_sort = None
    if sort_by:
        direction = 1 if sort_dir == "asc" else -1
        mongo_sort = [(sort_by, direction)]

    if hasattr(workflow_service, "list_profile_views"):
        profiles = await workflow_service.list_profile_views(
            query=query, skip=skip, limit=page_size, sort=mongo_sort
        )
    else:
        profiles = await workflow_service.list_profile_records(
            query=query, skip=skip, limit=page_size, sort=mongo_sort
        )
    normalized_profiles = [
        normalize_employee_workflow_status(profile) for profile in profiles
    ]
    if find_employee_account_by_employee_id_fn is not None:
        account_rows = await asyncio.gather(
            *[
                find_employee_account_by_employee_id_fn(
                    db,
                    employee_id=profile.get("employee_id", ""),
                    projection={"_id": 0, "email": 1},
                )
                for profile in normalized_profiles
            ]
        )
        for profile, account in zip(normalized_profiles, account_rows):
            profile["has_login_account"] = bool(account)
            if account and account.get("email"):
                profile["account_email"] = account["email"]

    return {
        "profiles": normalized_profiles,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


async def get_profile_response(
    *,
    employee_id: str,
    current_user: dict,
    user_role: str,
    workflow_service: EmployeeWorkflowApplicationService,
    enforce_department_scope_or_raise_fn: EnforceDepartmentScopeFn,
    normalize_department_code_fn: NormalizeDepartmentCodeFn,
) -> dict[str, Any]:
    if has_permission(current_user, Permission.PROFILE_READ_ALL):
        pass
    elif has_permission(current_user, Permission.PROFILE_READ_OWN) and is_owner(
        current_user, employee_id
    ):
        pass
    else:
        raise HTTPException(
            status_code=403, detail="Insufficient permission to view this profile"
        )

    if hasattr(workflow_service, "get_profile_view"):
        profile = await workflow_service.get_profile_view(employee_id=employee_id)
    else:
        profile = await workflow_service.get_employee_record(employee_id=employee_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    scoped_department = await enforce_department_scope_or_raise_fn(
        current_user,
        user_role,
        workflow_service,
    )
    if scoped_department:
        profile_department = normalize_department_code_fn(
            profile.get("current_department_id")
        )
        if profile_department != scoped_department:
            raise HTTPException(
                status_code=403,
                detail="Department-scoped access only allows your own department records.",
            )

    return normalize_employee_workflow_status(profile)


async def get_identity_response(
    *,
    employee_id: str,
    db: Any,
    current_user: dict,
    user_role: str,
    workflow_service: EmployeeWorkflowApplicationService,
    enforce_department_scope_or_raise_fn: EnforceDepartmentScopeFn,
    normalize_department_code_fn: NormalizeDepartmentCodeFn,
) -> dict[str, Any]:
    if has_permission(current_user, Permission.PROFILE_READ_ALL):
        pass
    elif has_permission(current_user, Permission.PROFILE_READ_OWN) and is_owner(
        current_user, employee_id
    ):
        pass
    else:
        raise HTTPException(
            status_code=403, detail="Insufficient permission to view this employee"
        )

    identity = await get_employee_identity(
        db,
        employee_id=employee_id,
        projection={"_id": 0},
    )
    if not identity:
        raise HTTPException(status_code=404, detail="Employee not found")

    scoped_department = await enforce_department_scope_or_raise_fn(
        current_user,
        user_role,
        workflow_service,
    )
    if scoped_department:
        identity_department = normalize_department_code_fn(
            identity.get("current_department_id")
        )
        if identity_department != scoped_department:
            raise HTTPException(
                status_code=403,
                detail="Department-scoped access only allows your own department records.",
            )

    return identity

