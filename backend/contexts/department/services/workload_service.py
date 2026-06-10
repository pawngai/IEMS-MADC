from __future__ import annotations

from typing import Any, Awaitable, Callable, Optional

from contexts.department.repository import department_portal_repo as repo
from contexts.department.services.portal_common import _pending_leave_statuses
from contexts.employee_profile.contracts.workflow_status_utils import normalize_workflow_status
from contexts.rbac.application.access_control import require_permissions
from contexts.rbac.domain.models import Permission

ResolveDepartment = Callable[[Any, dict], Awaitable[str]]
RequireAuthority = Callable[[dict], None]


async def get_pending_leaves(
    db,
    *,
    current_user: dict,
    resolve_department: ResolveDepartment,
    require_department_authority: RequireAuthority,
    repository=repo,
) -> dict[str, Any]:
    require_permissions(current_user, Permission.LEAVE_READ_ALL)
    require_department_authority(current_user)

    department_code = await resolve_department(db, current_user)
    employee_ids = await repository.get_employee_ids_for_department(db, department_code)

    statuses = _pending_leave_statuses(current_user)
    leaves = await repository.list_pending_leaves(db, employee_ids, statuses)

    name_map = await repository.get_employee_name_map(db, employee_ids) if employee_ids else {}
    for leave in leaves:
        leave["employee_name"] = name_map.get(
            leave.get("employee_id"), leave.get("employee_id")
        )

    return {
        "department_code": department_code,
        "leaves": leaves,
        "total": len(leaves),
    }


async def get_workflow_overview(
    db,
    *,
    current_user: dict,
    resolve_department: ResolveDepartment,
    require_department_authority: RequireAuthority,
    repository=repo,
    workflow_status: Optional[str] = None,
) -> dict[str, Any]:
    require_permissions(current_user, Permission.IDENTITY_READ_ALL)
    require_department_authority(current_user)

    department_code = await resolve_department(db, current_user)

    employees = await repository.list_employees(
        db,
        department_code,
        workflow_status=workflow_status,
    )

    items = [
        {
            "employee_id": employee.get("employee_id"),
            "employee_code": employee.get("employee_code"),
            "full_name": employee.get("full_name"),
            "workflow_status": normalize_workflow_status(employee.get("workflow_status", "DRAFT"))
            or "DRAFT",
            "employment_type": employee.get("employment_type"),
            "updated_at": employee.get("updated_at"),
        }
        for employee in employees
    ]

    return {
        "department_code": department_code,
        "items": items,
        "total": len(items),
    }


async def get_activity(
    db,
    *,
    current_user: dict,
    resolve_department: ResolveDepartment,
    require_department_authority: RequireAuthority,
    repository=repo,
    limit: int = 50,
) -> dict[str, Any]:
    require_permissions(current_user, Permission.IDENTITY_READ_ALL)
    require_department_authority(current_user)

    department_code = await resolve_department(db, current_user)
    employee_ids = await repository.get_employee_ids_for_department(db, department_code)

    entries = await repository.list_department_activity(db, employee_ids, limit=limit)

    activities = [
        {
            "id": entry.get("id", ""),
            "action": entry.get("action", ""),
            "resource_type": entry.get("resource_type"),
            "resource_id": entry.get("resource_id"),
            "user_name": entry.get("user_name"),
            "timestamp": entry.get("timestamp", ""),
            "details": entry.get("details"),
        }
        for entry in entries
    ]

    return {
        "department_code": department_code,
        "activities": activities,
        "total": len(activities),
    }


async def get_pending_work(
    db,
    *,
    current_user: dict,
    resolve_department: ResolveDepartment,
    require_department_authority: RequireAuthority,
    repository=repo,
) -> dict[str, Any]:
    require_permissions(current_user, Permission.IDENTITY_READ_ALL)
    require_department_authority(current_user)

    department_code = await resolve_department(db, current_user)

    draft_profiles = await repository.list_employees(
        db,
        department_code,
        workflow_status="DRAFT",
    )
    rejected_profiles = await repository.list_employees(
        db,
        department_code,
        workflow_status="REJECTED",
    )

    items = []
    for profile in draft_profiles:
        items.append(
            {
                "employee_id": profile.get("employee_id"),
                "employee_code": profile.get("employee_code"),
                "full_name": profile.get("full_name"),
                "workflow_status": "DRAFT",
                "employment_type": profile.get("employment_type"),
                "updated_at": profile.get("updated_at"),
                "action_needed": "Complete and submit profile",
            }
        )
    for profile in rejected_profiles:
        items.append(
            {
                "employee_id": profile.get("employee_id"),
                "employee_code": profile.get("employee_code"),
                "full_name": profile.get("full_name"),
                "workflow_status": "REJECTED",
                "employment_type": profile.get("employment_type"),
                "updated_at": profile.get("updated_at"),
                "rejection_reason": profile.get("workflow_remarks", ""),
                "action_needed": "Fix issues and re-submit profile",
            }
        )

    return {
        "department_code": department_code,
        "items": items,
        "total": len(items),
        "draft_count": len(draft_profiles),
        "rejected_count": len(rejected_profiles),
    }


__all__ = [
    "get_activity",
    "get_pending_leaves",
    "get_pending_work",
    "get_workflow_overview",
]