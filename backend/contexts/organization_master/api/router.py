"""
Department Portal API Router.

All endpoints are scoped to the authenticated user's department.
Prefix: /department
"""

from __future__ import annotations

from typing import Any, Optional

from app_platform.auth.current_user import get_current_user
from app_platform.db.runtime import get_db
from contexts.organization_master.services import department_portal_service as department_service
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

department_portal_router = APIRouter(prefix="/department", tags=["Department Portal"])


class SanctionedStrengthUpdateRequest(BaseModel):
    sanctioned_strength: list[dict[str, Any]] = Field(default_factory=list)
    reason: str = Field(..., min_length=3)


@department_portal_router.get("/dashboard")
async def get_dashboard(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await department_service.get_dashboard(db, current_user=current_user)


@department_portal_router.get("/employees")
async def get_employees(
    q: Optional[str] = Query(default=None, description="Search by name/code"),
    search: Optional[str] = Query(default=None, description="Search by name/code"),
    workflow_status: Optional[str] = Query(
        default=None,
        description="Filter by profile workflow status. Use LOCKED as terminal status.",
    ),
    employment_type: Optional[str] = Query(
        default=None, description="Filter by employment type"
    ),
    designation_id: Optional[str] = Query(default=None, description="Filter by designation"),
    office_id: Optional[str] = Query(default=None, description="Filter by office"),
    employee_status: Optional[str] = Query(default=None, description="Filter by employee status"),
    recruitment_mode: Optional[str] = Query(default=None, description="Filter by recruitment mode"),
    pay_level: Optional[str] = Query(default=None, description="Filter by pay level"),
    service: Optional[str] = Query(default=None, description="Filter by service"),
    service_group: Optional[str] = Query(default=None, description="Filter by service group"),
    date_from: Optional[str] = Query(default=None, description="Filter by appointment date from (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(default=None, description="Filter by appointment date to (YYYY-MM-DD)"),
    sort_by: Optional[str] = Query(default=None, description="Field name to sort by."),
    sort_dir: str = Query(default="asc", description="Sort direction: asc or desc."),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await department_service.get_employees(
        db,
        current_user=current_user,
        search=q or search,
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
    )


@department_portal_router.get("/employees/{employee_id}")
async def get_employee_snapshot(
    employee_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await department_service.get_employee_snapshot(
        db, employee_id, current_user=current_user
    )


@department_portal_router.get("/pending-leaves")
async def get_pending_leaves(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await department_service.get_pending_leaves(db, current_user=current_user)


@department_portal_router.get("/workflow")
async def get_workflow_overview(
    workflow_status: Optional[str] = Query(
        default=None,
        description="Filter by profile workflow status. Use LOCKED as terminal status.",
    ),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await department_service.get_workflow_overview(
        db,
        current_user=current_user,
        workflow_status=workflow_status,
    )


@department_portal_router.get("/activity")
async def get_activity(
    limit: int = Query(default=50, ge=1, le=200),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await department_service.get_activity(db, current_user=current_user, limit=limit)


@department_portal_router.get("/pending-work")
async def get_pending_work(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await department_service.get_pending_work(db, current_user=current_user)


@department_portal_router.get("/sanctioned-strength")
async def get_sanctioned_strength(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await department_service.get_sanctioned_strength(db, current_user=current_user)


@department_portal_router.put("/sanctioned-strength")
async def update_sanctioned_strength(
    payload: SanctionedStrengthUpdateRequest,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await department_service.update_sanctioned_strength(
        db,
        current_user=current_user,
        rows=payload.sanctioned_strength,
        reason=payload.reason,
    )


