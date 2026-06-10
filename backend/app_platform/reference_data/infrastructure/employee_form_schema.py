from __future__ import annotations

from app_platform.reference_data.infrastructure.employee_form_catalog import (
    COMMON_FIELDS,
    EMPLOYEE_FORM_SCHEMA,
    EMPLOYMENT_TYPE_FIELDS,
    REJECTED_FIELDS,
    WIZARD_STEPS,
    EMPLOYMENT_TYPE_CODE_MAP,
    EmploymentType,
    get_allowed_field_ids,
    get_fields_for_employment_type,
    validate_submission,
)

__all__ = [
    "COMMON_FIELDS",
    "EMPLOYEE_FORM_SCHEMA",
    "EMPLOYMENT_TYPE_CODE_MAP",
    "EMPLOYMENT_TYPE_FIELDS",
    "EmploymentType",
    "REJECTED_FIELDS",
    "WIZARD_STEPS",
    "get_allowed_field_ids",
    "get_fields_for_employment_type",
    "validate_submission",
]
