"""Employee domain enums."""

from __future__ import annotations

from enum import Enum


class EmploymentType(str, Enum):
    """Employment type classification"""
    REGULAR = "REGULAR"
    PROBATIONER = "PROBATIONER"
    TEMPORARY = "TEMPORARY"
    CONTRACTUAL = "CONTRACTUAL"
    DAILY_WAGE = "DAILY_WAGE"
    REEMPLOYED = "REEMPLOYED"
    OUTSOURCED = "OUTSOURCED"
    MUSTER_ROLL = "MUSTER_ROLL"
    CONTRACT = "CONTRACT"
    FIXED_PAY = "FIXED_PAY"
    WAGES = "WAGES"
    DAILY_RATED = "DAILY_RATED"
    CO_TERMINUS = "CO_TERMINUS"
    DEPUTATION = "DEPUTATION"
    CASUAL = "CASUAL"
    PART_TIME = "PART_TIME"


class EmployeeStatus(str, Enum):
    """Identity lifecycle status, not current service status."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DUPLICATE = "DUPLICATE"
    MERGED = "MERGED"
    ARCHIVED = "ARCHIVED"


class Gender(str, Enum):
    """Gender classification"""
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class WorkflowStatus(str, Enum):
    """Employee record workflow status"""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    VERIFIED = "VERIFIED"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    ATTESTED = "ATTESTED"
    LOCKED = "LOCKED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"
