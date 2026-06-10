"""
Department Portal facade.

Routes and tests import this module as the stable service surface; feature-specific
implementation lives in smaller modules in this package.
"""

from __future__ import annotations

from typing import Any, Optional

from contexts.department.repository import department_portal_repo as repo
from contexts.department.services import dashboard_service, directory_service, sanctioned_strength_service, workload_service
from contexts.department.services.portal_common import (
    ALLOWED_DIRECTORY_SORT_FIELDS,
    EMPLOYMENT_TYPES,
    WORKFLOW_STATUSES,
    _actor_identity,
    _normalize,
    _pending_leave_statuses,
    _require_department_authority,
    _resolve_department,
)
from contexts.identity.contracts.user_directory import find_user_by_employee_id


async def _build_sanctioned_strength_summary(
    db,
    department_code: str,
) -> dict[str, Any]:
    return await sanctioned_strength_service.build_sanctioned_strength_summary(
        db,
        department_code,
        repository=repo,
    )


async def get_dashboard(db, *, current_user: dict) -> dict[str, Any]:
    return await dashboard_service.get_dashboard(
        db,
        current_user=current_user,
        resolve_department=_resolve_department,
        require_department_authority=_require_department_authority,
        repository=repo,
    )


async def get_sanctioned_strength(db, *, current_user: dict) -> dict[str, Any]:
    return await sanctioned_strength_service.get_sanctioned_strength(
        db,
        current_user=current_user,
        resolve_department=_resolve_department,
        require_department_authority=_require_department_authority,
        repository=repo,
    )


async def update_sanctioned_strength(
    db,
    *,
    current_user: dict,
    rows: list[dict[str, Any]],
    reason: str,
) -> dict[str, Any]:
    return await sanctioned_strength_service.update_sanctioned_strength(
        db,
        current_user=current_user,
        rows=rows,
        reason=reason,
        resolve_department=_resolve_department,
        require_department_authority=_require_department_authority,
        repository=repo,
    )


async def get_employees(
    db,
    *,
    current_user: dict,
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
    return await directory_service.get_employees(
        db,
        current_user=current_user,
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
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
        resolve_department=_resolve_department,
        require_department_authority=_require_department_authority,
        repository=repo,
        user_lookup=find_user_by_employee_id,
    )


async def get_employee_snapshot(
    db,
    employee_id: str,
    *,
    current_user: dict,
) -> dict[str, Any]:
    return await directory_service.get_employee_snapshot(
        db,
        employee_id,
        current_user=current_user,
        resolve_department=_resolve_department,
        require_department_authority=_require_department_authority,
    )


async def get_pending_leaves(
    db,
    *,
    current_user: dict,
) -> dict[str, Any]:
    return await workload_service.get_pending_leaves(
        db,
        current_user=current_user,
        resolve_department=_resolve_department,
        require_department_authority=_require_department_authority,
        repository=repo,
    )


async def get_workflow_overview(
    db,
    *,
    current_user: dict,
    workflow_status: Optional[str] = None,
) -> dict[str, Any]:
    return await workload_service.get_workflow_overview(
        db,
        current_user=current_user,
        workflow_status=workflow_status,
        resolve_department=_resolve_department,
        require_department_authority=_require_department_authority,
        repository=repo,
    )


async def get_activity(
    db,
    *,
    current_user: dict,
    limit: int = 50,
) -> dict[str, Any]:
    return await workload_service.get_activity(
        db,
        current_user=current_user,
        limit=limit,
        resolve_department=_resolve_department,
        require_department_authority=_require_department_authority,
        repository=repo,
    )


async def get_pending_work(db, *, current_user: dict) -> dict[str, Any]:
    return await workload_service.get_pending_work(
        db,
        current_user=current_user,
        resolve_department=_resolve_department,
        require_department_authority=_require_department_authority,
        repository=repo,
    )


__all__ = [
    "ALLOWED_DIRECTORY_SORT_FIELDS",
    "EMPLOYMENT_TYPES",
    "WORKFLOW_STATUSES",
    "_actor_identity",
    "_build_sanctioned_strength_summary",
    "_normalize",
    "_pending_leave_statuses",
    "_require_department_authority",
    "_resolve_department",
    "find_user_by_employee_id",
    "get_activity",
    "get_dashboard",
    "get_employee_snapshot",
    "get_employees",
    "get_pending_leaves",
    "get_pending_work",
    "get_sanctioned_strength",
    "get_workflow_overview",
    "repo",
    "update_sanctioned_strength",
]