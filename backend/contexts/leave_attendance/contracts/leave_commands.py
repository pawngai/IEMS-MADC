from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from contexts.leave_attendance.contracts.leave_directory import get_leave_application_by_id
from contexts.leave_attendance.domain.leave_rules import (
    EMPLOYMENT_TYPES_WITH_LEAVE_ACCOUNT,
    normalize_employment_type_code,
)
from contexts.leave_attendance.infrastructure.gateway_helpers import (
    _ensure_initial_leave_account,
    _find_employee_profile,
    _resolve_service_start_date,
)
from contexts.leave_attendance.repository.leave_repository import LeaveRuntimeRepository


async def admin_cancel_leave_application(
    db,
    *,
    leave_id: str,
    reason: str,
    cancelled_by: str,
) -> dict[str, Any] | None:
    record = await get_leave_application_by_id(db, leave_id=leave_id)
    if not record:
        return None

    if record.get("status") not in {"SUBMITTED", "RECOMMENDED"}:
        raise HTTPException(status_code=400, detail="Only pending leaves can be cancelled")

    update = {
        "status": "CANCELLED",
        "remarks": reason,
        "cancelled_at": datetime.now(timezone.utc).isoformat(),
        "cancelled_by": cancelled_by,
        "cancelled_by_role": "SYSTEM_ADMIN",
    }
    await db.leave_applications.update_one({"id": leave_id}, {"$set": update})
    record.update(update)
    return record


async def ensure_initial_leave_account(
    db,
    *,
    employee_id: str,
    user_id: str | None,
) -> dict[str, Any] | None:
    repository = LeaveRuntimeRepository(db=db)
    profile = await _find_employee_profile(repository, employee_id)
    if not profile:
        return None

    employment_type_code = normalize_employment_type_code(
        profile.get("employment_type") or profile.get("employment_type_code")
    )
    if not employment_type_code or employment_type_code not in EMPLOYMENT_TYPES_WITH_LEAVE_ACCOUNT:
        return None

    service_start_date = await _resolve_service_start_date(
        repository,
        employee_id=employee_id,
        profile=profile,
    )
    return await _ensure_initial_leave_account(
        repository,
        employee_id=employee_id,
        user_id=user_id,
        employment_type_code=employment_type_code,
        service_start_date=service_start_date,
    )


__all__ = ["admin_cancel_leave_application", "ensure_initial_leave_account"]