from __future__ import annotations

from typing import Optional

from contexts.employee_profile.application.access_scope import enforce_department_scope_or_raise
from contexts.employee_profile.application.dependencies import get_current_user, get_db
from contexts.employee_profile.application.factory import build_employee_workflow_service
from contexts.employee_profile.application.policy import (
    DATA_ENTRY_ROLES,
    DEPARTMENT_SCOPED_ROLES,
    ROLE_APPROVER,
    ROLE_VERIFIER,
)
from contexts.employee_profile.application.queries.profile_queries import (
    get_profile_response,
    list_profiles_response,
)
from contexts.employee_profile.application.router_support import (
    normalize_department_code as _normalize_department_code,
)
from contexts.employee_profile.application.services.workflow_engine import EmployeeWorkflowApplicationService
from contexts.identity_access.contracts.user_directory import find_user_by_employee_id
from fastapi import APIRouter, Depends, Query, Request
from contexts.identity_access.contracts.user_role import get_user_role

read_router = APIRouter()


def get_employee_workflow_service(
    request: Request, db=None
) -> EmployeeWorkflowApplicationService:
    if db is None:
        db = get_db()
    return build_employee_workflow_service(request=request, db=db)


async def _enforce_department_scope_or_raise(
    current_user: dict,
    user_role: str,
    workflow_service: EmployeeWorkflowApplicationService,
    requested_department: Optional[str] = None,
) -> Optional[str]:
    return await enforce_department_scope_or_raise(
        current_user,
        user_role,
        workflow_service,
        DEPARTMENT_SCOPED_ROLES,
        requested_department=requested_department,
    )


_ALLOWED_SORT_FIELDS = frozenset({
    "full_name", "employee_code", "current_department_id",
    "current_designation_id", "current_office_id", "employment_type",
    "employee_status", "identity_workflow_status", "workflow_status", "date_of_initial_engagement",
    "date_of_birth", "gender", "category", "mode_of_recruitment",
    "pay_level", "mobile_primary", "email_official",
})


@read_router.get("/", response_model=dict)
async def list_profiles(
    q: Optional[str] = Query(default=None, description="Search by employee id, code, or name."),
    status: Optional[str] = None,
    workflow_status: Optional[str] = Query(
        default=None,
        description="Filter by profile workflow status. Use LOCKED as terminal status.",
    ),
    profile_workflow_status: Optional[str] = Query(
        default=None,
        description="Explicit alias for filtering by profile workflow status.",
    ),
    department_id: Optional[str] = None,
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
    force_all: Optional[bool] = False,
    profile_workflow_only: bool = Query(
        default=False,
        description="When true, DRAFT profile queues include only records whose identity workflow is complete.",
    ),
    sort_by: Optional[str] = Query(default=None, description="Field name to sort by."),
    sort_dir: Optional[str] = Query(default="asc", description="Sort direction: asc or desc."),
    page: int = 1,
    page_size: int = 20,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
    workflow_service: EmployeeWorkflowApplicationService = Depends(
        get_employee_workflow_service
    ),
):
    user_role = get_user_role(current_user)
    safe_sort_by = sort_by if sort_by in _ALLOWED_SORT_FIELDS else None
    safe_sort_dir = sort_dir if sort_dir in ("asc", "desc") else "asc"
    effective_profile_workflow_status = profile_workflow_status or workflow_status
    return await list_profiles_response(
        db=db,
        search=q,
        status=status,
        workflow_status=effective_profile_workflow_status,
        department_id=department_id,
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
        force_all=force_all,
        sort_by=safe_sort_by,
        sort_dir=safe_sort_dir,
        page=page,
        page_size=page_size,
        current_user=current_user,
        user_role=user_role,
        workflow_service=workflow_service,
        enforce_department_scope_or_raise_fn=_enforce_department_scope_or_raise,
        data_entry_roles=set(DATA_ENTRY_ROLES),
        role_verifier=ROLE_VERIFIER,
        role_approver=ROLE_APPROVER,
        find_employee_account_by_employee_id_fn=find_user_by_employee_id,
        profile_workflow_only=profile_workflow_only,
    )


@read_router.get("/{employee_id}", response_model=dict)
async def get_profile(
    employee_id: str,
    current_user: dict = Depends(get_current_user),
    workflow_service: EmployeeWorkflowApplicationService = Depends(
        get_employee_workflow_service
    ),
):
    user_role = get_user_role(current_user)
    profile = await get_profile_response(
        employee_id=employee_id,
        current_user=current_user,
        user_role=user_role,
        workflow_service=workflow_service,
        enforce_department_scope_or_raise_fn=_enforce_department_scope_or_raise,
        normalize_department_code_fn=_normalize_department_code,
    )
    profile["workflow"] = {
        "status": profile.get("workflow_status"),
        "updated_at": profile.get("updated_at"),
    }
    return profile

