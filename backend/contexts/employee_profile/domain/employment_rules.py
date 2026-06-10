from __future__ import annotations

from typing import Any


REGULAR_EMPLOYMENT_TYPE = "REGULAR"

EMPLOYMENT_TYPE_ALIASES = {
    "REG": REGULAR_EMPLOYMENT_TYPE,
    "REGULAR": REGULAR_EMPLOYMENT_TYPE,
    "CONTRACT": "CONTRACTUAL",
    "CONTRACTUAL": "CONTRACTUAL",
    "DAILY_WAGE": "DAILY_WAGE",
    "DAILYWAGE": "DAILY_WAGE",
    "DEPUTATION": "DEPUTATION",
    "REEMPLOYED": "REEMPLOYED",
    "REEMPLOYMENT": "REEMPLOYED",
    "OUTSOURCED": "OUTSOURCED",
}


def determine_employment_type(employee_or_type: Any) -> str | None:
    if isinstance(employee_or_type, dict):
        raw = employee_or_type.get("employment_type") or employee_or_type.get(
            "employment_type_code"
        )
    else:
        raw = employee_or_type

    if raw is None:
        return None

    normalized = str(raw).strip().upper()
    if not normalized:
        return None

    return EMPLOYMENT_TYPE_ALIASES.get(normalized, normalized)


def is_regular_employee(employee_or_type: Any) -> bool:
    return determine_employment_type(employee_or_type) == REGULAR_EMPLOYMENT_TYPE
