"""Employee identity command models."""

from __future__ import annotations

from datetime import datetime
import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from contexts.employee_identity.schemas.enums import (
    EmployeeStatus,
    Gender,
)


def _validate_date_string(value: str | None) -> str | None:
    if value is None:
        return None

    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("Date must be in YYYY-MM-DD format") from exc
    return value


def _normalize_email(value: str | None) -> str | None:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return None
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", normalized):
        raise ValueError("Invalid email address")
    return normalized


def _normalize_mobile(value: str | None) -> str | None:
    normalized = re.sub(r"\D", "", str(value or ""))
    if not normalized:
        return None
    if not re.match(r"^[6-9]\d{9}$", normalized):
        raise ValueError("Invalid Indian mobile number")
    return normalized


def _format_field_list(fields: list[str], *, limit: int = 8) -> str:
    if len(fields) <= limit:
        return ", ".join(fields)
    visible = ", ".join(fields[:limit])
    return f"{visible}, and {len(fields) - limit} more"


def _reject_non_identity_fields(
    data,
    *,
    allowed_fields: set[str],
    action: str,
) -> dict:
    if not isinstance(data, dict):
        return data

    extra_fields = sorted(str(key) for key in data.keys() if key not in allowed_fields)
    if not extra_fields:
        return data

    message_parts = [
        f"Employee identity {action} accepts only core identity fields.",
    ]
    message_parts.append(
        "Move non-identity fields to their owning context after the identity exists: "
        f"{_format_field_list(extra_fields)}."
    )
    message_parts.append("See /api/docs for the identity-first 2-step contract.")
    raise ValueError(" ".join(message_parts))


class EmployeeIdentityCreate(BaseModel):
    """Model for creating core employee identity."""

    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(..., min_length=2, max_length=100)
    gender: Gender
    date_of_birth: str
    current_designation_id: Optional[str] = None
    current_office_id: Optional[str] = None
    reporting_officer_id: Optional[str] = None
    mobile_primary: Optional[str] = None
    email_official: Optional[str] = None
    employee_status: Optional[EmployeeStatus] = None
    status_effective_date: Optional[str] = None
    status_remarks: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def reject_non_identity_fields(cls, data):
        return _reject_non_identity_fields(
            data,
            allowed_fields=set(cls.model_fields.keys()),
            action="create",
        )

    @field_validator("date_of_birth", "status_effective_date")
    @classmethod
    def validate_date_fields(cls, value: str | None) -> str | None:
        return _validate_date_string(value)

    @field_validator("mobile_primary")
    @classmethod
    def validate_mobile_primary(cls, value: str | None) -> str | None:
        return _normalize_mobile(value)

    @field_validator("email_official")
    @classmethod
    def validate_email_official(cls, value: str | None) -> str | None:
        return _normalize_email(value)


class EmployeeIdentityUpdate(BaseModel):
    """Model for updating core employee identity."""

    model_config = ConfigDict(extra="forbid")

    full_name: Optional[str] = None
    gender: Optional[Gender] = None
    date_of_birth: Optional[str] = None
    current_designation_id: Optional[str] = None
    current_office_id: Optional[str] = None
    reporting_officer_id: Optional[str] = None
    mobile_primary: Optional[str] = None
    email_official: Optional[str] = None
    employee_status: Optional[EmployeeStatus] = None
    status_effective_date: Optional[str] = None
    status_remarks: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def reject_non_identity_fields(cls, data):
        return _reject_non_identity_fields(
            data,
            allowed_fields=set(cls.model_fields.keys()),
            action="update",
        )

    @field_validator("date_of_birth", "status_effective_date")
    @classmethod
    def validate_date_fields(cls, value: str | None) -> str | None:
        return _validate_date_string(value)

    @field_validator("mobile_primary")
    @classmethod
    def validate_mobile_primary(cls, value: str | None) -> str | None:
        return _normalize_mobile(value)

    @field_validator("email_official")
    @classmethod
    def validate_email_official(cls, value: str | None) -> str | None:
        return _normalize_email(value)
