from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from contexts.employee_master.identity.application.dependencies import get_current_user, get_db
from contexts.employee_master.identity.application.identity_interface import (
    count_employee_identities,
    get_employee_identity as get_employee_identity_record,
    get_identity_editor_bootstrap,
    list_employee_identities as list_identity_records,
    resolve_employee_department_code,
)
from contexts.employee_master.profile.contracts.profile_directory import list_profile_workflow_statuses
from contexts.identity_access.contracts.user_role import get_user_role
from contexts.identity_access.contracts.access_control import has_permission, is_owner
from contexts.identity_access.contracts.models import Permission


read_router = APIRouter()
DEPARTMENT_SCOPED_ROLES = {"DEPT_DATA_ENTRY", "HOD"}
VERIFIER_VISIBLE_WORKFLOW_STATUSES = ["SUBMITTED", "VERIFIED", "ACTIVE"]
APPROVER_VISIBLE_WORKFLOW_STATUSES = ["VERIFIED", "ACTIVE"]
NO_MATCH_WORKFLOW_STATUS = "__NO_MATCH__"
_ALLOWED_IDENTITY_DIRECTORY_SORT_FIELDS = frozenset({
    "full_name",
    "employee_code",
    "current_department_id",
    "current_designation_id",
    "current_office_id",
    "employment_type",
    "employee_status",
    "identity_workflow_status",
    "workflow_status",
    "date_of_initial_engagement",
    "date_of_birth",
    "gender",
    "category",
    "mode_of_recruitment",
    "pay_level",
    "mobile_primary",
    "email_official",
})


def _normalize_department_code(value: Optional[str]) -> str | None:
    normalized = str(value or "").strip().upper()
    return normalized or None


def _normalize_sort_value(value: Any) -> tuple[int, Any]:
    if value is None:
        return (3, "")
    if isinstance(value, bool):
        return (0, int(value))
    if isinstance(value, (int, float)):
        return (0, value)

    text = str(value).strip()
    if not text:
        return (3, "")

    try:
        return (1, datetime.fromisoformat(text.replace("Z", "+00:00")))
    except ValueError:
        return (2, text.casefold())


def _get_identity_sort_value(identity: dict[str, Any], sort_by: str) -> Any:
    if sort_by == "identity_workflow_status":
        return identity.get("identity_workflow_status") or identity.get("workflow_status")
    if sort_by == "workflow_status":
        return identity.get("profile_workflow_status") or identity.get("workflow_status")
    return identity.get(sort_by)


def _sort_identity_rows(
    identities: list[dict[str, Any]],
    *,
    sort_by: str,
    sort_dir: str,
) -> list[dict[str, Any]]:
    present: list[tuple[tuple[int, Any], dict[str, Any]]] = []
    missing: list[dict[str, Any]] = []

    for identity in identities:
        value = _get_identity_sort_value(identity, sort_by)
        normalized = _normalize_sort_value(value)
        if normalized[0] == 3:
            missing.append(identity)
            continue
        present.append((normalized, identity))

    present.sort(key=lambda item: item[0], reverse=sort_dir == "desc")
    return [identity for _, identity in present] + missing


def _identity_status_scope_for_role(user_role: str, status: Optional[str]) -> str | list[str] | None:
    normalized_status = str(status or "").strip().upper()
    if user_role == "VERIFIER":
        visible_statuses = VERIFIER_VISIBLE_WORKFLOW_STATUSES
    elif user_role == "APPROVING_AUTHORITY":
        visible_statuses = APPROVER_VISIBLE_WORKFLOW_STATUSES
    else:
        return normalized_status or None

    if normalized_status:
        if normalized_status in visible_statuses:
            return normalized_status
        return NO_MATCH_WORKFLOW_STATUS

    return visible_statuses


async def _get_scoped_department(db, *, current_user: dict, user_role: str) -> str | None:
    if user_role not in DEPARTMENT_SCOPED_ROLES:
        return None

    token_department = _normalize_department_code(current_user.get("department_code"))
    if token_department:
        return token_department

    employee_id = current_user.get("employee_id")
    if employee_id:
        identity_department = await resolve_employee_department_code(
            db,
            employee_id=employee_id,
        )
        if identity_department:
            return identity_department

    raise HTTPException(
        status_code=403,
        detail="Department access is restricted. Map this user to a department first.",
    )


async def _attach_profile_workflow_statuses(db, identities: list[dict]) -> list[dict]:
    if not identities:
        return identities

    statuses = await list_profile_workflow_statuses(
        db,
        employee_ids=[str(identity.get("employee_id") or "") for identity in identities],
    )
    enriched: list[dict] = []
    for identity in identities:
        employee_id = str(identity.get("employee_id") or "").strip()
        enriched.append(
            {
                **identity,
                "identity_workflow_status": identity.get("identity_workflow_status")
                or identity.get("workflow_status")
                or "DRAFT",
                "profile_workflow_status": statuses.get(employee_id)
                or identity.get("profile_workflow_status")
                or "DRAFT",
            }
        )
    return enriched


@read_router.get("/bootstrap", response_model=dict)
async def get_employee_identity_bootstrap(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not (
        has_permission(current_user, Permission.IDENTITY_READ_ALL)
        or has_permission(current_user, Permission.IDENTITY_CREATE)
        or has_permission(current_user, Permission.IDENTITY_UPDATE_ALL)
    ):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permission to load employee identity bootstrap data",
        )
    return await get_identity_editor_bootstrap(db)


@read_router.get("/", response_model=dict)
async def list_employee_identities(
    search: Optional[str] = None,
    status: Optional[str] = None,
    department_id: Optional[str] = None,
    employment_type: Optional[str] = None,
    sort_by: Optional[str] = Query(default=None),
    sort_dir: Optional[str] = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if has_permission(current_user, Permission.IDENTITY_READ_ALL):
        pass
    elif has_permission(current_user, Permission.IDENTITY_READ_OWN):
        employee_id = current_user.get("employee_id")
        if not employee_id:
            raise HTTPException(status_code=403, detail="No employee identity linked to user")
        identity = await get_employee_identity_record(
            db,
            employee_id=employee_id,
        )
        return {
            "identities": [identity] if identity else [],
            "total": 1 if identity else 0,
            "page": 1,
            "page_size": 1,
            "total_pages": 1 if identity else 0,
        }
    else:
        raise HTTPException(status_code=403, detail="Insufficient permission to view identities")

    user_role = get_user_role(current_user)
    scoped_department = await _get_scoped_department(
        db,
        current_user=current_user,
        user_role=user_role,
    )
    if scoped_department:
        department_id = scoped_department

    workflow_status_scope = _identity_status_scope_for_role(user_role, status)
    safe_sort_by = sort_by if sort_by in _ALLOWED_IDENTITY_DIRECTORY_SORT_FIELDS else None
    safe_sort_dir = sort_dir if sort_dir in ("asc", "desc") else "asc"

    total = await count_employee_identities(
        db,
        search=search,
        employment_type=employment_type,
        department_code=department_id,
        status=workflow_status_scope,
    )

    if safe_sort_by:
        identities = await list_identity_records(
            db,
            search=search,
            employment_type=employment_type,
            department_code=department_id,
            status=workflow_status_scope,
            skip=0,
            limit=max(total, 1),
        )
    else:
        identities = await list_identity_records(
            db,
            search=search,
            employment_type=employment_type,
            department_code=department_id,
            status=workflow_status_scope,
            skip=(page - 1) * page_size,
            limit=page_size,
        )

    identities = await _attach_profile_workflow_statuses(db, identities)
    if safe_sort_by:
        identities = _sort_identity_rows(
            identities,
            sort_by=safe_sort_by,
            sort_dir=safe_sort_dir,
        )
        start = (page - 1) * page_size
        identities = identities[start:start + page_size]

    return {
        "identities": identities,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@read_router.get("/{employee_id}", response_model=dict)
async def get_employee_identity(
    employee_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if has_permission(current_user, Permission.IDENTITY_READ_ALL):
        pass
    elif has_permission(current_user, Permission.IDENTITY_READ_OWN) and is_owner(
        current_user, employee_id
    ):
        pass
    else:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permission to view this employee identity",
        )

    identity = await get_employee_identity_record(
        db,
        employee_id=employee_id,
    )
    if not identity:
        raise HTTPException(status_code=404, detail="Employee identity not found")

    user_role = get_user_role(current_user)
    scoped_department = await _get_scoped_department(
        db,
        current_user=current_user,
        user_role=user_role,
    )
    identity_department = await resolve_employee_department_code(
        db,
        employee_id=str(identity.get("employee_id") or employee_id),
    )
    if scoped_department and scoped_department != identity_department:
        raise HTTPException(
            status_code=403,
            detail="Department-scoped access only allows your own department records.",
        )

    return identity
