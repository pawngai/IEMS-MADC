from __future__ import annotations

from typing import Any, Callable, Awaitable

from contexts.department.repository import department_portal_repo as repo
from contexts.department.services.portal_common import (
    EMPLOYMENT_TYPES,
    WORKFLOW_STATUSES,
    _pending_leave_statuses,
)
from contexts.department.services.sanctioned_strength_service import build_sanctioned_strength_summary
from contexts.rbac.application.access_control import require_permissions
from contexts.rbac.domain.models import Permission

ResolveDepartment = Callable[[Any, dict], Awaitable[str]]
RequireAuthority = Callable[[dict], None]


async def get_dashboard(
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

    dept_info = await repository.get_department_info(db, department_code)
    department_name = (dept_info or {}).get("name") if dept_info else None

    employee_ids = await repository.get_employee_ids_for_department(db, department_code)
    total = len(employee_ids)

    active_count = await repository.count_employees_by_status(db, department_code, "ACTIVE")
    locked_count = await repository.count_employees_by_workflow(db, department_code, "LOCKED")

    workflow_breakdown = []
    for workflow_status in WORKFLOW_STATUSES:
        count = await repository.count_employees_by_workflow(db, department_code, workflow_status)
        if count > 0:
            workflow_breakdown.append({"status": workflow_status, "count": count})

    employment_type_breakdown = []
    for employment_type in EMPLOYMENT_TYPES:
        count = await repository.count_employees_by_employment_type(db, department_code, employment_type)
        if count > 0:
            employment_type_breakdown.append({"employment_type": employment_type, "count": count})

    regular_count = next(
        (
            item["count"]
            for item in employment_type_breakdown
            if item["employment_type"] == "REGULAR"
        ),
        0,
    )

    statuses = _pending_leave_statuses(current_user)
    pending_leave_count = await repository.count_pending_leaves(db, employee_ids, statuses)
    establishment = await build_sanctioned_strength_summary(
        db,
        department_code,
        repository=repository,
    )

    return {
        "department_code": department_code,
        "department_name": department_name,
        "total_employees": total,
        "active_employees": active_count,
        "locked_profiles": locked_count,
        "regular_employees": regular_count,
        "workflow_breakdown": workflow_breakdown,
        "employment_type_breakdown": employment_type_breakdown,
        "pending_leave_actions": pending_leave_count,
        "sanctioned_strength_configured": establishment["configured"],
        "sanctioned_strength_total": establishment["totals"]["sanctioned_strength_total"],
        "filled_strength_total": establishment["totals"]["filled_strength_total"],
        "vacancy_count": establishment["totals"]["vacancy_count"],
        "over_strength_count": establishment["totals"]["over_strength_count"],
    }


__all__ = ["get_dashboard"]