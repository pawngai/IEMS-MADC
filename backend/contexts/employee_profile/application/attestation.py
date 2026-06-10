from __future__ import annotations

from contexts.employee_profile.application.services.workflow_engine import EmployeeWorkflowApplicationService
from contexts.employee_profile.domain.constants import EMPLOYMENT_TYPE_REGULAR


async def get_attesting_officer_info(
    current_user: dict,
    workflow_service: EmployeeWorkflowApplicationService,
) -> dict:
    officer_employee_id = current_user.get("employee_id")
    fallback_name = current_user.get("name")

    if not officer_employee_id:
        return {"attesting_officer_name": fallback_name, "attesting_officer_designation": None}

    officer_profile = await workflow_service.get_officer_profile_for_attestation(employee_id=officer_employee_id)
    if not officer_profile:
        return {"attesting_officer_name": fallback_name, "attesting_officer_designation": None}

    if (officer_profile.get("employment_type") or "").upper() != EMPLOYMENT_TYPE_REGULAR:
        return {"attesting_officer_name": fallback_name, "attesting_officer_designation": None}

    designation_value = officer_profile.get("current_designation_id")
    designation_name = None
    if designation_value:
        designation_name = await workflow_service.get_designation_name(code=designation_value)

    return {
        "attesting_officer_name": officer_profile.get("full_name") or fallback_name,
        "attesting_officer_designation": designation_name or designation_value,
    }

