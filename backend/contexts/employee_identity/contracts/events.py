"""Published event contracts owned by the employee_identity context.

These are the canonical event payload schemas for employee identity lifecycle
events. Other contexts subscribe to them via the platform event bus and may
import them from here as a Published Language. They must never be defined in
``app_platform`` — the platform only hosts the bus mechanism, not the business
event schemas of any specific context.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class EmployeeEventBase(BaseModel):
    event_version: Literal[1] = 1


class EmployeeCreatedEvent(EmployeeEventBase):
    employee_id: str
    employee_code: str | None = None
    dept_id: str | None = None
    current_department_id: str | None = None
    name: str
    full_name: str | None = None
    gender: str | None = None
    dob: date | None = None
    date_of_birth: date | None = None
    doj: date | None = None
    date_of_initial_engagement: date | None = None
    employment_type: str | None = None
    designation_id: str | None = None
    current_designation_id: str | None = None
    current_office_id: str | None = None
    reporting_officer_id: str | None = None
    employee_status: str | None = None
    mobile_primary: str | None = None
    email_official: str | None = None
    identity_workflow_status: str | None = None
    workflow_status: str | None = None
    status_effective_date: str | None = None
    status_remarks: str | None = None
    created_at: str
    updated_at: str | None = None
    created_by: str | None = None
    updated_by: str | None = None
    version: int = Field(default=1, ge=1)


class EmployeeIdentityCreatedEvent(EmployeeEventBase):
    employee_id: str
    employee_code: str | None = None
    dept_id: str | None = None
    current_department_id: str | None = None
    name: str
    full_name: str | None = None
    gender: str | None = None
    dob: date | None = None
    date_of_birth: date | None = None
    doj: date | None = None
    date_of_initial_engagement: date | None = None
    employment_type: str | None = None
    designation_id: str | None = None
    current_designation_id: str | None = None
    current_office_id: str | None = None
    reporting_officer_id: str | None = None
    employee_status: str | None = None
    mobile_primary: str | None = None
    email_official: str | None = None
    identity_workflow_status: str = "DRAFT"
    workflow_status: str = "DRAFT"
    status_effective_date: str | None = None
    status_remarks: str | None = None
    created_at: str
    updated_at: str | None = None
    created_by: str | None = None
    updated_by: str | None = None
    version: int = Field(default=1, ge=1)


class EmployeeUpdatedEvent(EmployeeEventBase):
    employee_id: str
    patch: dict
    updated_at: str
    version: int = Field(default=1, ge=1)


class EmployeeStatusChangedEvent(EmployeeEventBase):
    employee_id: str
    old_status: str | None = None
    new_status: str
    effective_date: str | None = None
    updated_at: str
    version: int = Field(default=1, ge=1)


class EmployeePromotedEvent(EmployeeEventBase):
    employee_id: str
    promotion_order_id: str
    effective_date: str
    from_post: str | None = None
    to_post: str
    updated_at: str
    version: int = Field(default=1, ge=1)


__all__ = [
    "EmployeeEventBase",
    "EmployeeCreatedEvent",
    "EmployeeIdentityCreatedEvent",
    "EmployeeUpdatedEvent",
    "EmployeeStatusChangedEvent",
    "EmployeePromotedEvent",
]
