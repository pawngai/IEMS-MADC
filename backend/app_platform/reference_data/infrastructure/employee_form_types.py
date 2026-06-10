from __future__ import annotations

from enum import Enum


class EmploymentType(str, Enum):
    REGULAR = "REGULAR"
    CONTRACTUAL = "CONTRACTUAL"
    DAILY_WAGE = "DAILY_WAGE"
    DEPUTATION = "DEPUTATION"
    REEMPLOYED = "REEMPLOYED"
    OUTSOURCED = "OUTSOURCED"


EMPLOYMENT_TYPE_CODE_MAP = {
    "REG": EmploymentType.REGULAR,
    "CON": EmploymentType.CONTRACTUAL,
    "CAS": EmploymentType.DAILY_WAGE,
    "DEP": EmploymentType.DEPUTATION,
    "REE": EmploymentType.REEMPLOYED,
    "OUT": EmploymentType.OUTSOURCED,
    "ADH": EmploymentType.CONTRACTUAL,
}


__all__ = ["EMPLOYMENT_TYPE_CODE_MAP", "EmploymentType"]