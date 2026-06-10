from __future__ import annotations

from fastapi import HTTPException

from contexts.employee_master.contracts.identity_directory import get_employee_department_code
from contexts.identity.infrastructure import repo
from contexts.rbac.contracts.models import Authority

DEPARTMENT_SCOPED_AUTHORITIES = {"DEPT_DATA_ENTRY", "HOD"}
ACCOUNT_PROVISIONING_READY_STAGE = "ACTIVE"

# Authorities exempt from the one-holder-per-role constraint
NON_EXCLUSIVE_AUTHORITIES = {"EMPLOYEE"}


async def _validate_exclusive_role_assignment(
    db,
    new_authorities: list[str],
    *,
    exclude_user_id: str | None = None,
) -> None:
    """Ensure each authority (except EMPLOYEE) is held by at most one active user.

    Raises HTTPException(409) listing the conflicting role(s) and current holder(s).
    """
    conflicts: list[str] = []
    for auth in new_authorities:
        if auth in NON_EXCLUSIVE_AUTHORITIES:
            continue
        holders = await repo.find_users_with_authority(
            db, auth, exclude_user_id=exclude_user_id
        )
        if holders:
            holder = holders[0]
            conflicts.append(
                f"{auth} (held by {holder.get('name', 'unknown')} — {holder.get('email', '')})"
            )
    if conflicts:
        raise HTTPException(
            status_code=409,
            detail=(
                "Role(s) already assigned to another employee: "
                + "; ".join(conflicts)
            ),
        )


async def _validate_department_scoped_roles(
    db,
    target_user: dict,
    new_authorities: list[str],
    department_code: str | None = None,
) -> None:
    """Ensure that department-scoped roles are only assigned to employees
    belonging to the specified department.

    Raises HTTPException(400/403) if the employee's profile department
    does not match the department_code being assigned.
    """
    dept_roles = set(new_authorities) & DEPARTMENT_SCOPED_AUTHORITIES
    if not dept_roles:
        return  # No department-scoped roles being assigned; nothing to check

    # Resolve department: explicit param -> user record -> fail
    target_dept = (department_code or "").strip().upper() or (
        target_user.get("department_code") or ""
    ).strip().upper()

    # Look up the employee's profile to get their actual department
    employee_id = target_user.get("employee_id") or ""
    if not employee_id:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot assign department-scoped role(s) {', '.join(sorted(dept_roles))} "
                f"- user has no linked employee_id."
            ),
        )

    profile_dept = await get_employee_department_code(
        db,
        employee_id=employee_id,
    ) or ""

    if not profile_dept:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot assign department-scoped role(s) {', '.join(sorted(dept_roles))} "
                f"- employee {employee_id} has no department in their profile."
            ),
        )

    if not target_dept:
        # No department specified; auto-use profile department (will be set by caller)
        return

    if target_dept != profile_dept:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Employee {employee_id} belongs to department {profile_dept}, "
                f"cannot assign role(s) {', '.join(sorted(dept_roles))} to department {target_dept}."
            ),
        )


def _valid_authorities() -> list[str]:
    """Derive valid authorities from the Authority enum to avoid desync."""
    return [a.value for a in Authority]


def _require_employee_account_ready(identity_workflow_status: str | None) -> str:
    normalized_status = str(identity_workflow_status or "").strip().upper() or "DRAFT"
    if normalized_status != ACCOUNT_PROVISIONING_READY_STAGE:
        raise HTTPException(
            status_code=409,
            detail=(
                "Employee account can be provisioned only after the employee identity is "
                f"ACTIVE. Current identity workflow status: {normalized_status}."
            ),
        )
    return normalized_status
