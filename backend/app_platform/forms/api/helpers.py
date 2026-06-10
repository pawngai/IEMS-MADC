from __future__ import annotations

from fastapi import HTTPException

from app_platform.forms.infrastructure.service import EmploymentType, WorkflowStage
from contexts.rbac.domain.models import Permission
from contexts.rbac.application.access_control import require_permissions


EMPLOYMENT_TYPE_LABELS: dict[str, str] = {
    "REGULAR": "Regular (Permanent)",
    "CONTRACTUAL": "Contractual",
    "DAILY_WAGE": "Daily Wage / Casual",
    "DEPUTATION": "Deputation",
    "REEMPLOYED": "Re-employed",
    "OUTSOURCED": "Outsourced",
}


TYPE_SPECIFIC_FIELDS: dict[str, list[str]] = {
    "REGULAR": [
        "service_group",
        "cadre",
        "pay_level",
        "basic_pay",
        "pension_scheme",
        "retirement_date",
    ],
    "CONTRACTUAL": [
        "contract_start_date",
        "contract_end_date",
        "contract_renewal_count",
        "consolidated_pay",
    ],
    "DAILY_WAGE": ["daily_rate", "muster_roll_number"],
    "DEPUTATION": [
        "parent_department_code",
        "deputation_start_date",
        "deputation_end_date",
        "deputation_tenure_years",
        "lien_position",
    ],
    "REEMPLOYED": [
        "previous_retirement_date",
        "reemployment_start_date",
        "reemployment_end_date",
        "pension_details",
    ],
    "OUTSOURCED": ["outsourcing_agency", "agency_contract_number"],
}


def require_forms_access(current_user: dict) -> None:
    require_permissions(
        current_user,
        Permission.IDENTITY_READ_OWN,
        Permission.IDENTITY_READ_ALL,
        Permission.IDENTITY_CREATE,
        Permission.PROFILE_UPDATE_OWN_LIMITED,
        Permission.PROFILE_UPDATE_ALL,
    )


def parse_employment_type(employment_type: str | None) -> EmploymentType | None:
    if not employment_type:
        return None
    try:
        return EmploymentType(employment_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid employment_type '{employment_type}'",
        ) from exc


def parse_workflow_stage(workflow_stage: str) -> WorkflowStage:
    try:
        return WorkflowStage(workflow_stage)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid workflow_stage '{workflow_stage}'",
        ) from exc
