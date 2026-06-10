from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app_platform.db.runtime import get_db
from app_platform.auth.current_user import get_current_user

from contexts.identity_access.identity.infrastructure import service as identity_service
from contexts.identity_access.identity.contracts.schemas import (
    ActivityLogResponse,
    EmployeeAccountProvisionRequest,
    EmployeeAccountProvisionResponse,
    AuthorityPatch,
    UserCreate,
    UserPasswordUpdate,
    UserResponse,
    UserUpdate,
)


users_router = APIRouter(prefix="/users", tags=["User Management"])


_ALLOWED_EMPLOYEE_DIRECTORY_SORT_FIELDS = frozenset({
    "full_name", "employee_code", "current_department_id",
    "current_designation_id", "current_office_id", "employment_type",
    "employee_status", "identity_workflow_status", "workflow_status", "date_of_initial_engagement",
    "date_of_birth", "gender", "category", "mode_of_recruitment",
    "pay_level", "mobile_primary", "email_official",
})


@users_router.get("/", response_model=list[UserResponse])
async def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    search: str | None = None,
    authority: str | None = None,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await identity_service.list_users(db, skip=skip, limit=limit, search=search, authority=authority, current_user=current_user)


@users_router.get("/count")
async def get_user_count(
    authority: str | None = None,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await identity_service.get_user_count(db, authority=authority, current_user=current_user)


@users_router.get("/authorities/list")
async def list_authorities(current_user: dict = Depends(get_current_user)):
    return await identity_service.list_authorities(current_user=current_user)


@users_router.get("/activity/logs", response_model=list[ActivityLogResponse])
async def get_activity_logs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    action: str | None = None,
    user_id: str | None = None,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await identity_service.list_activity_logs(
        db,
        skip=skip,
        limit=limit,
        action=action,
        user_id=user_id,
        current_user=current_user,
    )


@users_router.get("/activity/stats")
async def get_activity_stats(
    days: int = Query(default=30, ge=1, le=365),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await identity_service.get_activity_stats(db, days=days, current_user=current_user)


@users_router.get("/role-changes/history")
async def get_role_change_history(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    user_id: str | None = None,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await identity_service.get_role_change_history(db, skip=skip, limit=limit, user_id=user_id, current_user=current_user)


@users_router.get("/role-changes/stats")
async def get_role_change_stats(
    days: int = Query(default=30, ge=1, le=365),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await identity_service.get_role_change_stats(db, days=days, current_user=current_user)


@users_router.get("/authorities/holders")
async def get_authority_holders(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return a mapping of authority -> current holder (name, email, user_id).

    Only roles held by an active user are included.  The EMPLOYEE role is
    excluded because it is not subject to the one-holder constraint.
    """
    return await identity_service.get_authority_holders(db, current_user=current_user)


@users_router.get("/employees")
async def list_employee_directory(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    search: str | None = None,
    department: str | None = None,
    employment_type: str | None = None,
    workflow_status: str | None = None,
    profile_workflow_status: str | None = Query(
        default=None,
        description="Explicit alias for filtering by profile workflow status.",
    ),
    designation_id: str | None = None,
    office_id: str | None = None,
    employee_status: str | None = None,
    recruitment_mode: str | None = None,
    pay_level: str | None = None,
    service: str | None = None,
    service_group: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort_by: str | None = Query(default=None, description="Field name to sort by."),
    sort_dir: str | None = Query(default="asc", description="Sort direction: asc or desc."),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    safe_sort_by = sort_by if sort_by in _ALLOWED_EMPLOYEE_DIRECTORY_SORT_FIELDS else None
    safe_sort_dir = sort_dir if sort_dir in ("asc", "desc") else "asc"
    effective_profile_workflow_status = profile_workflow_status or workflow_status
    employees = await identity_service.list_employee_directory(
        db,
        skip=skip,
        limit=limit,
        search=search,
        department=department,
        employment_type=employment_type,
        workflow_status=effective_profile_workflow_status,
        designation_id=designation_id,
        office_id=office_id,
        employee_status=employee_status,
        recruitment_mode=recruitment_mode,
        pay_level=pay_level,
        service=service,
        service_group=service_group,
        date_from=date_from,
        date_to=date_to,
        sort_by=safe_sort_by,
        sort_dir=safe_sort_dir,
        current_user=current_user,
    )
    total = await identity_service.get_employee_directory_count(
        db,
        search=search,
        department=department,
        employment_type=employment_type,
        workflow_status=effective_profile_workflow_status,
        designation_id=designation_id,
        office_id=office_id,
        employee_status=employee_status,
        recruitment_mode=recruitment_mode,
        pay_level=pay_level,
        service=service,
        service_group=service_group,
        date_from=date_from,
        date_to=date_to,
        current_user=current_user,
    )
    return {
        "employees": employees,
        "total": total["count"],
        "limit": limit,
        "offset": skip,
    }


@users_router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await identity_service.get_user(db, user_id, current_user=current_user)


@users_router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await identity_service.create_user(db, user_data, current_user=current_user)


@users_router.post("/employee-accounts", response_model=EmployeeAccountProvisionResponse)
async def provision_employee_account(
    payload: EmployeeAccountProvisionRequest,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await identity_service.provision_employee_account_for_employee(
        db,
        employee_id=payload.employee_id,
        email=str(payload.email),
        current_user=current_user,
    )
    return EmployeeAccountProvisionResponse(**result)


@users_router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await identity_service.update_user(db, user_id, user_data, current_user=current_user)


@users_router.patch("/{user_id}/authorities", response_model=UserResponse)
async def patch_user_authorities(
    user_id: str,
    patch: AuthorityPatch,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Atomically add/remove specific authorities without replacing the full list."""
    return await identity_service.patch_user_authorities(db, user_id, patch, current_user=current_user)


@users_router.put("/{user_id}/password")
async def update_user_password(
    user_id: str,
    password_data: UserPasswordUpdate,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await identity_service.update_user_password(db, user_id, password_data, current_user=current_user)


@users_router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await identity_service.delete_user(db, user_id, current_user=current_user)
