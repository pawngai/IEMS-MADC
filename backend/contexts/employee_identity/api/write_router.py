from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request

from contexts.employee_identity.application.dependencies import get_current_user, get_db
from contexts.employee_identity.application.identity_interface import resolve_employee_department_code
from contexts.employee_identity.domain.identity_workflow_rules import (
    build_identity_workflow_response,
    validate_identity_activate_transition,
    validate_identity_reject_transition,
    validate_identity_submit_transition,
    validate_identity_verify_transition,
)
from contexts.employee_identity.repository import EmployeeIdentityRepository
from contexts.employee_identity.schemas.commands import (
    EmployeeIdentityCreate,
    EmployeeIdentityUpdate,
)
from contexts.identity.contracts.user_role import get_user_role
from contexts.rbac.contracts.access_control import require_permissions
from contexts.rbac.contracts.models import Permission


write_router = APIRouter()
DEPARTMENT_SCOPED_ROLES = {"DEPT_DATA_ENTRY", "HOD"}
DATA_ENTRY_ROLES = {"DEPT_DATA_ENTRY", "GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT"}


def _normalize_department_code(value: Optional[str]) -> str | None:
    normalized = str(value or "").strip().upper()
    return normalized or None


def _get_user_id(current_user: dict) -> str:
    return current_user.get("sub") or current_user.get("user_id") or ""


def _raise_department_scope_error() -> None:
    raise HTTPException(
        status_code=403,
        detail="Department-scoped access only allows your own department records.",
    )


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


def _repo_from_request(request: Request, db) -> EmployeeIdentityRepository:
    container = getattr(request.app.state, "container", None)
    outbox_repo = container.outbox_repo if container is not None else None
    return EmployeeIdentityRepository(db=db, outbox_repo=outbox_repo)


@write_router.post("/", response_model=dict)
async def create_employee_identity(
    payload: EmployeeIdentityCreate,
    request: Request,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_permissions(current_user, Permission.IDENTITY_CREATE)

    user_role = get_user_role(current_user)
    if user_role not in DATA_ENTRY_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Core employee identity creation is limited to data entry staff.",
        )

    scoped_department = await _get_scoped_department(
        db,
        current_user=current_user,
        user_role=user_role,
    )
    if scoped_department:
        _raise_department_scope_error()
    repo = _repo_from_request(request, db)
    identity = await repo.create_identity(
        payload=payload.model_dump(mode="json", exclude_none=True),
        actor_user_id=_get_user_id(current_user),
    )
    return {
        "success": True,
        "message": "Employee identity created successfully",
        "employee_id": identity["employee_id"],
        "employee_code": identity["employee_code"],
    }


@write_router.put("/{employee_id}", response_model=dict)
async def update_employee_identity(
    employee_id: str,
    payload: EmployeeIdentityUpdate,
    request: Request,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_permissions(current_user, Permission.IDENTITY_UPDATE_ALL)

    user_role = get_user_role(current_user)
    if user_role not in DATA_ENTRY_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Core employee identity updates are limited to data entry staff.",
        )

    repo = _repo_from_request(request, db)
    current = await repo.get_identity(employee_id=employee_id)
    if not current:
        raise HTTPException(status_code=404, detail="Employee identity not found")

    scoped_department = await _get_scoped_department(
        db,
        current_user=current_user,
        user_role=user_role,
    )
    if scoped_department:
        target_department = await resolve_employee_department_code(
            db,
            employee_id=employee_id,
        )
        if target_department != scoped_department:
            _raise_department_scope_error()
    patch = {
        key: value
        for key, value in payload.model_dump(mode="json").items()
        if value is not None
    }
    if not patch:
        raise HTTPException(status_code=400, detail="No updates provided")

    updated = await repo.update_identity(
        employee_id=employee_id,
        patch=patch,
        actor_user_id=_get_user_id(current_user),
    )
    return {
        "success": True,
        "message": "Employee identity updated successfully",
        "employee_id": employee_id,
        "updated_fields": sorted(patch.keys()),
        "version": updated.get("version"),
    }


# ---------------------------------------------------------------------------
# Identity workflow transitions
# ---------------------------------------------------------------------------

@write_router.post("/{employee_id}/submit", response_model=dict)
async def submit_identity(
    employee_id: str,
    request: Request,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Submit a DRAFT identity for verification (Data Entry only)."""
    require_permissions(current_user, Permission.IDENTITY_SUBMIT)
    user_role = get_user_role(current_user)
    actor_id = _get_user_id(current_user)

    repo = _repo_from_request(request, db)
    identity = await repo.get_identity(employee_id=employee_id)
    if not identity:
        raise HTTPException(status_code=404, detail="Employee identity not found")

    previous = identity.get("workflow_status") or "DRAFT"
    new_status = validate_identity_submit_transition(
        current_status=previous,
        user_role=user_role,
    )
    await repo.transition_workflow(
        employee_id=employee_id,
        new_status=new_status,
        actor_user_id=actor_id,
    )
    return build_identity_workflow_response(
        action="SUBMIT",
        employee_id=employee_id,
        previous_status=previous,
        new_status=new_status,
        performed_by=actor_id,
    )


@write_router.post("/{employee_id}/verify", response_model=dict)
async def verify_identity(
    employee_id: str,
    request: Request,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Verify a SUBMITTED identity (Verifier only)."""
    require_permissions(current_user, Permission.IDENTITY_VERIFY)
    user_role = get_user_role(current_user)
    actor_id = _get_user_id(current_user)

    repo = _repo_from_request(request, db)
    identity = await repo.get_identity(employee_id=employee_id)
    if not identity:
        raise HTTPException(status_code=404, detail="Employee identity not found")

    previous = identity.get("workflow_status") or "DRAFT"
    new_status = validate_identity_verify_transition(
        current_status=previous,
        user_role=user_role,
        identity_created_by=identity.get("created_by"),
        actor_user_id=actor_id,
    )
    await repo.transition_workflow(
        employee_id=employee_id,
        new_status=new_status,
        actor_user_id=actor_id,
    )
    return build_identity_workflow_response(
        action="VERIFY",
        employee_id=employee_id,
        previous_status=previous,
        new_status=new_status,
        performed_by=actor_id,
    )


@write_router.post("/{employee_id}/activate", response_model=dict)
async def activate_identity(
    employee_id: str,
    request: Request,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Activate a VERIFIED identity (Approving Authority only).

    This publishes EmployeeCreated, initialising the EmployeeProfile projection
    and ServiceBook stream for regular employees.
    """
    require_permissions(current_user, Permission.IDENTITY_ACTIVATE)
    user_role = get_user_role(current_user)
    actor_id = _get_user_id(current_user)

    repo = _repo_from_request(request, db)
    identity = await repo.get_identity(employee_id=employee_id)
    if not identity:
        raise HTTPException(status_code=404, detail="Employee identity not found")

    previous = identity.get("workflow_status") or "DRAFT"
    new_status = validate_identity_activate_transition(
        current_status=previous,
        user_role=user_role,
        identity_created_by=identity.get("created_by"),
        identity_verified_by=identity.get("verified_by"),
        actor_user_id=actor_id,
    )
    await repo.transition_workflow(
        employee_id=employee_id,
        new_status=new_status,
        actor_user_id=actor_id,
    )
    return build_identity_workflow_response(
        action="ACTIVATE",
        employee_id=employee_id,
        previous_status=previous,
        new_status=new_status,
        performed_by=actor_id,
    )


@write_router.post("/{employee_id}/reject", response_model=dict)
async def reject_identity(
    employee_id: str,
    request: Request,
    remarks: str = Body(..., embed=True),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Reject a SUBMITTED or VERIFIED identity back to DRAFT."""
    require_permissions(current_user, Permission.IDENTITY_REJECT)
    user_role = get_user_role(current_user)
    actor_id = _get_user_id(current_user)

    repo = _repo_from_request(request, db)
    identity = await repo.get_identity(employee_id=employee_id)
    if not identity:
        raise HTTPException(status_code=404, detail="Employee identity not found")

    previous = identity.get("workflow_status") or "DRAFT"
    new_status = validate_identity_reject_transition(
        current_status=previous,
        user_role=user_role,
        remarks=remarks,
    )
    await repo.transition_workflow(
        employee_id=employee_id,
        new_status=new_status,
        actor_user_id=actor_id,
        remarks=remarks,
    )
    return build_identity_workflow_response(
        action="REJECT",
        employee_id=employee_id,
        previous_status=previous,
        new_status=new_status,
        performed_by=actor_id,
        remarks=remarks,
    )
