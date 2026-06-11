"""Employee identity models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from contexts.employee_master.identity.domain.employee_code import format_employee_code
from contexts.employee_master.identity.schemas.enums import EmployeeStatus, Gender


class EmployeeIdentity(BaseModel):
    """Canonical first-layer employee identity."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="MongoDB document ID")
    employee_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="System-generated unique ID")
    employee_code: Optional[str] = None

    full_name: str = Field(..., min_length=2, max_length=100, description="Full name as per official records")
    gender: Gender = Field(..., description="Gender")
    date_of_birth: str = Field(..., description="Date of birth (YYYY-MM-DD)")
    mobile_primary: Optional[str] = None
    email_official: Optional[str] = None

    employee_status: EmployeeStatus = Field(default=EmployeeStatus.ACTIVE)
    status_effective_date: Optional[str] = None
    status_remarks: Optional[str] = None

    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by: Optional[str] = None
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_by: Optional[str] = None
    version: int = Field(default=1)

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("Date must be in YYYY-MM-DD format") from exc
        return v

    def generate_employee_code(self, sequence: int) -> str:
        year = datetime.now(timezone.utc).year
        return format_employee_code(
            year=year,
            employment_type="IDENTITY",
            sequence=sequence,
        )