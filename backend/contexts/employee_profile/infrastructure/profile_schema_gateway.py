from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import re
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EmployeeStatus(str, Enum):
    ACTIVE = "ACTIVE"


class WorkflowStatus(str, Enum):
    DRAFT = "DRAFT"


class ContactDetails(BaseModel):
    mobile_primary: str | None = None
    mobile_alternate: str | None = None
    email_personal: str | None = None
    email_official: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    district: str | None = None
    state: str | None = None
    pincode: str | None = None
    present_address_line1: str | None = None
    present_address_line2: str | None = None
    present_city: str | None = None
    present_district: str | None = None
    present_state: str | None = None
    present_pincode: str | None = None
    emergency_name: str | None = None
    emergency_phone: str | None = None
    emergency_relation: str | None = None

    @field_validator("mobile_primary", "mobile_alternate")
    @classmethod
    def validate_mobile(cls, value):
        if value and not re.match(r"^[6-9]\d{9}$", value):
            raise ValueError("Invalid Indian mobile number")
        return value

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, value):
        if value and not re.match(r"^\d{6}$", value):
            raise ValueError("Invalid pincode")
        return value


class IdentityDocuments(BaseModel):
    aadhaar_number: str | None = None
    pan_number: str | None = None

    @field_validator("aadhaar_number")
    @classmethod
    def validate_aadhaar(cls, value):
        if value and not re.match(r"^\d{12}$", value):
            raise ValueError("Aadhaar must be 12 digits")
        return value

    @field_validator("pan_number")
    @classmethod
    def validate_pan(cls, value):
        if value and not re.match(r"^[A-Z]{5}\d{4}[A-Z]$", value.upper()):
            raise ValueError("Invalid PAN format")
        return value.upper() if value else value


class EmployeeProfileDocument(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    employee_code: str | None = None
    full_name: str
    gender: str
    date_of_birth: str
    employment_type: str
    date_of_initial_engagement: str
    current_department_id: str
    contact: ContactDetails
    identifiers: IdentityDocuments | None = None
    employee_status: str = Field(default=EmployeeStatus.ACTIVE.value)
    workflow_status: str = Field(default=WorkflowStatus.DRAFT.value)
    employee_section_completed: bool = Field(default=False)
    data_entry_section_completed: bool = Field(default=False)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: int = Field(default=1)

    @field_validator("date_of_birth", "date_of_initial_engagement")
    @classmethod
    def validate_date_format(cls, value):
        datetime.strptime(value, "%Y-%m-%d")
        return value

    @field_validator("employment_type", mode="before")
    @classmethod
    def normalize_employment_type(cls, value):
        if value is None:
            return value
        return str(getattr(value, "value", value))

    @field_validator("gender", mode="before")
    @classmethod
    def normalize_gender(cls, value):
        if value is None:
            return value
        return str(getattr(value, "value", value))


def validate_contact_details(payload: dict) -> dict:
    return ContactDetails(**payload).model_dump()


def validate_identity_documents(payload: dict) -> dict:
    return IdentityDocuments(**payload).model_dump()


def build_employee_profile_document(payload: dict) -> dict:
    return EmployeeProfileDocument(**payload).model_dump()
