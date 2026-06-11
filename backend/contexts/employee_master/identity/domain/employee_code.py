from __future__ import annotations

import re
from typing import Any

from contexts.employee_master.identity.schemas.enums import EmploymentType


_CURRENT_EMPLOYEE_CODE_PATTERN = re.compile(r"MADC-(\d{4})")
_LEGACY_CANONICAL_EMPLOYEE_CODE_PATTERN = re.compile(r"MADC-(\d{4})-([A-Z])(\d{4})")
_IDENTITY_EMPLOYEE_CODE_INITIAL = "I"


def employment_type_initial(value: Any) -> str:
    normalized = str(value or "").strip().upper().replace("-", "_").replace(" ", "_")
    if normalized == "IDENTITY":
        return _IDENTITY_EMPLOYEE_CODE_INITIAL
    if normalized == "EMPLOYEE":
        return _IDENTITY_EMPLOYEE_CODE_INITIAL
    if not normalized:
        raise ValueError("INVALID_EMPLOYMENT_TYPE")

    for employment_type in EmploymentType:
        if normalized in {employment_type.name, employment_type.value}:
            return employment_type.value[0]

    for char in normalized:
        if char.isalpha():
            return char

    raise ValueError("INVALID_EMPLOYMENT_TYPE")


def format_employee_code(*, year: int, employment_type: Any, sequence: int) -> str:
    _ = (year, employment_type)
    return f"MADC-{sequence:04d}"


def parse_employee_code(value: Any) -> tuple[int | None, str | None, int] | None:
    normalized = str(value or "").strip()
    match = _CURRENT_EMPLOYEE_CODE_PATTERN.fullmatch(normalized)
    if match:
        return None, None, int(match.group(1))

    legacy_match = _LEGACY_CANONICAL_EMPLOYEE_CODE_PATTERN.fullmatch(normalized)
    if not legacy_match:
        return None
    return int(legacy_match.group(1)), legacy_match.group(2), int(legacy_match.group(3))