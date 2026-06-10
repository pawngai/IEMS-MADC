"""Employee identity, profile extension, and composed employee view models."""

from __future__ import annotations

import uuid
import re
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class EmploymentType(str, Enum):
    """Employment type values projected from EmployeeIdentity."""

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
    """Identity lifecycle values projected from EmployeeIdentity."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DUPLICATE = "DUPLICATE"
    MERGED = "MERGED"
    ARCHIVED = "ARCHIVED"


class Gender(str, Enum):
    """Gender values projected from EmployeeIdentity."""

    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class WorkflowStatus(str, Enum):
    """Employee profile workflow status values."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    VERIFIED = "VERIFIED"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    ATTESTED = "ATTESTED"
    LOCKED = "LOCKED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


class ContactDetails(BaseModel):
    mobile_primary: Optional[str] = None
    mobile_alternate: Optional[str] = None
    email_personal: Optional[str] = None
    email_official: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    present_address: Optional[str] = None
    present_city: Optional[str] = None
    present_district: Optional[str] = None
    present_state: Optional[str] = None
    present_pincode: Optional[str] = None
    emergency_name: Optional[str] = None
    emergency_phone: Optional[str] = None
    emergency_relation: Optional[str] = None

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
    aadhaar_number: Optional[str] = None
    pan_number: Optional[str] = None

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


class EmployeeIdentity(BaseModel):
    """Profile-owned identity snapshot used for composed read views."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Snapshot document ID")
    employee_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_code: Optional[str] = None
    full_name: str = Field(..., min_length=2, max_length=100)
    gender: Gender
    date_of_birth: str
    aadhaar_number: Optional[str] = None
    employment_type: EmploymentType
    date_of_initial_engagement: str
    current_department_id: str
    current_designation_id: Optional[str] = None
    current_office_id: Optional[str] = None
    reporting_officer_id: Optional[str] = None
    employee_status: EmployeeStatus = Field(default=EmployeeStatus.ACTIVE)
    status_effective_date: Optional[str] = None
    status_remarks: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by: Optional[str] = None
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_by: Optional[str] = None
    version: int = Field(default=1)

    @field_validator("date_of_birth", "date_of_initial_engagement")
    @classmethod
    def validate_date_format(cls, value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("Date must be in YYYY-MM-DD format") from exc
        return value


class EmployeeProfileExtension(BaseModel):
    """Employee-owned profile enrichment built on top of identity."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Extension document ID")
    employee_id: str

    father_name: Optional[str] = Field(None, max_length=100)
    mother_name: Optional[str] = Field(None, max_length=100)
    nationality: str = Field(default="Indian", max_length=50)
    category: Optional[str] = Field(None, description="Reservation category code")
    sub_caste: Optional[str] = None
    religion: Optional[str] = None
    date_of_birth_saka: Optional[str] = None
    place_of_birth: Optional[str] = None
    blood_group: Optional[str] = None
    height_cm: Optional[float] = None
    identification_marks: List[str] = Field(default_factory=list)
    marital_status: Optional[str] = None
    spouse_name: Optional[str] = None

    educational_qualifications_initial: List[dict] = Field(default_factory=list)
    educational_qualifications_acquired: List[dict] = Field(default_factory=list)
    professional_qualifications: List[dict] = Field(default_factory=list)

    contact: ContactDetails = Field(default_factory=ContactDetails)
    identifiers: Optional[IdentityDocuments] = None

    photo_url: Optional[str] = None
    photo_updated_at: Optional[str] = None
    signature_url: Optional[str] = None
    thumb_impression_url: Optional[str] = None

    workflow_status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT)
    workflow_remarks: Optional[str] = None

    employee_section_completed: bool = Field(default=False, description="Employee self-service section completed")
    data_entry_section_completed: bool = Field(default=False, description="Data Entry section completed")

    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by: Optional[str] = None
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_by: Optional[str] = None
    verified_at: Optional[str] = None
    verified_by: Optional[str] = None
    approved_at: Optional[str] = None
    approved_by: Optional[str] = None
    locked_at: Optional[str] = None
    locked_by: Optional[str] = None
    version: int = Field(default=1)


class EmployeeCompositeProfileView(EmployeeIdentity):
    """Composed employee-owned view combining identity and extension."""

    father_name: Optional[str] = Field(None, max_length=100)
    mother_name: Optional[str] = Field(None, max_length=100)
    nationality: str = Field(default="Indian", max_length=50)
    category: Optional[str] = Field(None, description="Reservation category code")
    sub_caste: Optional[str] = None
    religion: Optional[str] = None
    date_of_birth_saka: Optional[str] = None
    place_of_birth: Optional[str] = None
    blood_group: Optional[str] = None
    height_cm: Optional[float] = None
    identification_marks: List[str] = Field(default_factory=list)
    marital_status: Optional[str] = None
    spouse_name: Optional[str] = None
    educational_qualifications_initial: List[dict] = Field(default_factory=list)
    educational_qualifications_acquired: List[dict] = Field(default_factory=list)
    professional_qualifications: List[dict] = Field(default_factory=list)
    contact: ContactDetails = Field(default_factory=ContactDetails)
    identifiers: Optional[IdentityDocuments] = None
    photo_url: Optional[str] = None
    photo_updated_at: Optional[str] = None
    signature_url: Optional[str] = None
    thumb_impression_url: Optional[str] = None
    workflow_status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT)
    workflow_remarks: Optional[str] = None
    employee_section_completed: bool = Field(default=False)
    data_entry_section_completed: bool = Field(default=False)
    verified_at: Optional[str] = None
    verified_by: Optional[str] = None
    approved_at: Optional[str] = None
    approved_by: Optional[str] = None
    locked_at: Optional[str] = None
    locked_by: Optional[str] = None
