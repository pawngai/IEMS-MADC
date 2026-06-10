from __future__ import annotations

from typing import Optional

from app_platform.reference_data.contracts.employment_type_master import (
    get_employment_type_master,
    normalize_employment_type_code as normalize_final_employment_type_code,
)
from app_platform.reference_data.contracts.schemas import EMPLOYMENT_TYPE_RULES, EmploymentTypeCode


EMPLOYMENT_TYPE_MAP: dict[str, str] = {
    "REG": "REGULAR",
    "REGULAR": "REGULAR",
    "CONTRACTUAL": "CONTRACT",
    "CONTRACT": "CONTRACT",
    "DAILY_WAGE": "DAILY_RATED",
    "DAILY_RATED": "DAILY_RATED",
    "DEPUTATION": "DEPUTATION",
    "REEMPLOYED": "TEMPORARY",
    "OUTSOURCED": "CONTRACT",
    "ADHOC": "TEMPORARY",
}


def normalize_employment_type_code(employment_type: str) -> Optional[EmploymentTypeCode]:
    if not employment_type:
        return None
    normalized = normalize_final_employment_type_code(
        EMPLOYMENT_TYPE_MAP.get(employment_type, employment_type)
    )
    try:
        return EmploymentTypeCode(normalized)
    except ValueError:
        return None


def get_employment_type_rules(employment_type: str) -> dict[str, object] | None:
    master = get_employment_type_master(employment_type)
    if master:
        return {
            "has_service_book": master["eligible_for_service_book"],
            "has_pension": master["eligible_for_pension"],
            "has_gpf": master["eligible_for_gpf"],
            "has_leave_account": master["eligible_for_leave_account"],
            "has_increment": master["eligible_for_macp"],
            "can_be_promoted": master["eligible_for_seniority"],
            "can_be_transferred": master["employment_class"] == "REGULAR",
            "service_book_parts": ["I", "II-A", "II-B", "III", "IV", "V", "VI", "VII", "VIII"]
            if master["eligible_for_service_book"]
            else [],
        }
    emp_type = normalize_employment_type_code(employment_type)
    rules = EMPLOYMENT_TYPE_RULES.get(emp_type) if emp_type else None
    return rules.model_dump() if rules else None


def check_employment_type_allows_service_book(employment_type: str) -> bool:
    rules = get_employment_type_rules(employment_type)
    return bool(rules.get("has_service_book")) if rules else False


def get_available_service_book_parts(employment_type: str) -> list[str]:
    rules = get_employment_type_rules(employment_type)
    return list(rules.get("service_book_parts") or []) if rules else []
