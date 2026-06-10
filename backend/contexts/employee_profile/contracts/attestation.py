from __future__ import annotations

from typing import Any

from contexts.employee_identity.contracts.designation_directory import get_designation_name
from contexts.employee_profile.contracts.profile_directory import find_profile_view
from contexts.employee_profile.domain.constants import EMPLOYMENT_TYPE_REGULAR


async def get_attesting_officer_info(db, *, current_user: dict[str, Any]) -> dict[str, Any]:
    officer_employee_id = current_user.get("employee_id")
    fallback_name = current_user.get("name")

    if not officer_employee_id:
        return {
            "attesting_officer_name": fallback_name,
            "attesting_officer_designation": None,
        }

    officer_profile = await find_profile_view(
        db,
        employee_id=officer_employee_id,
        projection={
            "_id": 0,
            "employee_id": 1,
            "employment_type": 1,
            "full_name": 1,
            "current_designation_id": 1,
        },
    )
    if not officer_profile:
        return {
            "attesting_officer_name": fallback_name,
            "attesting_officer_designation": None,
        }

    if (officer_profile.get("employment_type") or "").upper() != EMPLOYMENT_TYPE_REGULAR:
        return {
            "attesting_officer_name": fallback_name,
            "attesting_officer_designation": None,
        }

    designation_value = officer_profile.get("current_designation_id")
    designation_name = await get_designation_name(db, code=designation_value)

    return {
        "attesting_officer_name": officer_profile.get("full_name") or fallback_name,
        "attesting_officer_designation": designation_name or designation_value,
    }

