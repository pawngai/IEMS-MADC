from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Optional

from fastapi import HTTPException

from contexts.department.repository import department_portal_repo as repo
from contexts.department.services.portal_common import ALLOWED_DIRECTORY_SORT_FIELDS, _normalize
from contexts.employee_profile.contracts.profile_directory import find_profile_view
from contexts.employee_profile.contracts.workflow_status_utils import normalize_employee_workflow_status
from contexts.identity.contracts.user_directory import find_user_by_employee_id
from contexts.rbac.application.access_control import require_permissions
from contexts.rbac.domain.models import Permission

ResolveDepartment = Callable[[Any, dict], Awaitable[str]]
RequireAuthority = Callable[[dict], None]
FindUserByEmployeeId = Callable[..., Awaitable[dict | None]]


async def get_employees(
    db,
    *,
    current_user: dict,
    resolve_department: ResolveDepartment,
    require_department_authority: RequireAuthority,
    repository=repo,
    user_lookup: FindUserByEmployeeId = find_user_by_employee_id,
    search: Optional[str] = None,
    workflow_status: Optional[str] = None,
    employment_type: Optional[str] = None,
    designation_id: Optional[str] = None,
    office_id: Optional[str] = None,
    employee_status: Optional[str] = None,
    recruitment_mode: Optional[str] = None,
    pay_level: Optional[str] = None,
    service: Optional[str] = None,
    service_group: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: str = "asc",
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    require_permissions(current_user, Permission.IDENTITY_READ_ALL)
    require_department_authority(current_user)

    department_code = await resolve_department(db, current_user)
    safe_sort_by = sort_by if sort_by in ALLOWED_DIRECTORY_SORT_FIELDS else "full_name"
    safe_sort_dir = sort_dir if sort_dir in {"asc", "desc"} else "asc"
    offset = (page - 1) * page_size

    employees = await repository.list_employees(
        db,
        department_code,
        search=search,
        workflow_status=workflow_status,
        employment_type=employment_type,
        designation_id=designation_id,
        office_id=office_id,
        employee_status=employee_status,
        recruitment_mode=recruitment_mode,
        pay_level=pay_level,
        service=service,
        service_group=service_group,
        date_from=date_from,
        date_to=date_to,
        limit=page_size,
        offset=offset,
        sort_by=safe_sort_by,
        sort_dir=safe_sort_dir,
    )
    total = await repository.count_employees(
        db,
        department_code,
        search=search,
        workflow_status=workflow_status,
        employment_type=employment_type,
        designation_id=designation_id,
        office_id=office_id,
        employee_status=employee_status,
        recruitment_mode=recruitment_mode,
        pay_level=pay_level,
        service=service,
        service_group=service_group,
        date_from=date_from,
        date_to=date_to,
    )

    normalized_items = [normalize_employee_workflow_status(item) for item in employees]
    account_rows = await asyncio.gather(
        *[
            user_lookup(
                db,
                employee_id=item.get("employee_id", ""),
                projection={"_id": 0, "email": 1},
            )
            for item in normalized_items
        ]
    )
    for item, account in zip(normalized_items, account_rows):
        has_login_account = bool(account)
        item["has_login_account"] = has_login_account
        if account and account.get("email"):
            item["account_email"] = account["email"]

    return {
        "department_code": department_code,
        "employees": normalized_items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
        "sort_by": safe_sort_by,
        "sort_dir": safe_sort_dir,
    }


async def get_employee_snapshot(
    db,
    employee_id: str,
    *,
    current_user: dict,
    resolve_department: ResolveDepartment,
    require_department_authority: RequireAuthority,
) -> dict[str, Any]:
    require_permissions(current_user, Permission.IDENTITY_READ_ALL)
    require_department_authority(current_user)

    department_code = await resolve_department(db, current_user)

    profile = await find_profile_view(
        db,
        employee_id=employee_id,
        projection={"_id": 0},
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    profile_dept = _normalize(profile.get("current_department_id"))
    if profile_dept != department_code:
        raise HTTPException(
            status_code=403,
            detail="Employee does not belong to your department.",
        )

    return normalize_employee_workflow_status(profile)


__all__ = ["get_employee_snapshot", "get_employees"]