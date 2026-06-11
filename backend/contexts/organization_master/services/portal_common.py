from __future__ import annotations

from typing import Optional

from fastapi import HTTPException

from contexts.employee_master.contracts.profile_directory import find_profile_view
from contexts.identity_access.contracts.user_directory import get_user_department_code
from contexts.identity_access.contracts.access_control import has_permission
from contexts.identity_access.contracts.authorization_service import DEPARTMENT, resolveScopeAccess
from contexts.identity_access.contracts.models import Permission

WORKFLOW_STATUSES = ["DRAFT", "SUBMITTED", "VERIFIED", "APPROVED", "LOCKED", "REJECTED"]
EMPLOYMENT_TYPES = ["REGULAR", "CONTRACTUAL", "DAILY_WAGE", "DEPUTATION", "REEMPLOYED", "OUTSOURCED"]
ALLOWED_DIRECTORY_SORT_FIELDS = frozenset(
    {
        "full_name",
        "employee_code",
        "current_department_id",
        "current_designation_id",
        "current_office_id",
        "employment_type",
        "employee_status",
        "workflow_status",
        "date_of_initial_engagement",
        "date_of_birth",
        "gender",
        "category",
        "mode_of_recruitment",
        "pay_level",
        "mobile_primary",
        "email_official",
    }
)


def _normalize(value: Optional[str]) -> str:
    return str(value or "").strip().upper()


async def _resolve_department(db, current_user: dict) -> str:
    token_dept = _normalize(current_user.get("department_code"))
    if token_dept:
        return token_dept

    user_id = current_user.get("sub") or current_user.get("user_id") or ""
    if user_id:
        dept_code = await get_user_department_code(db, user_id=user_id)
        if dept_code:
            return dept_code

    employee_id = current_user.get("employee_id") or ""
    if employee_id:
        profile = await find_profile_view(
            db,
            employee_id=employee_id,
            projection={"_id": 0, "current_department_id": 1},
        )
        profile_dept = _normalize((profile or {}).get("current_department_id"))
        if profile_dept:
            return profile_dept

    raise HTTPException(
        status_code=403,
        detail="Department access is restricted. Map this user to a department first.",
    )


def _require_department_authority(current_user: dict) -> None:
    scope = resolveScopeAccess(current_user).get("scope")
    if scope != DEPARTMENT:
        raise HTTPException(
            status_code=403,
            detail="Department portal requires department-scoped access.",
        )


def _pending_leave_statuses(current_user: dict) -> list[str]:
    statuses: list[str] = []
    if has_permission(current_user, Permission.LEAVE_RECOMMEND):
        statuses.append("SUBMITTED")
    if has_permission(current_user, Permission.LEAVE_SANCTION):
        statuses.append("RECOMMENDED")
    return statuses


def _actor_identity(current_user: dict) -> tuple[str, str]:
    actor_id = str(current_user.get("sub") or current_user.get("user_id") or "unknown")
    actor_email = str(current_user.get("email") or current_user.get("username") or "unknown")
    return actor_id, actor_email


__all__ = [
    "ALLOWED_DIRECTORY_SORT_FIELDS",
    "EMPLOYMENT_TYPES",
    "WORKFLOW_STATUSES",
    "_actor_identity",
    "_normalize",
    "_pending_leave_statuses",
    "_require_department_authority",
    "_resolve_department",
]