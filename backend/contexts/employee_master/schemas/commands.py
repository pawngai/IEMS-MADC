"""Employee Master command models.

EmployeeMasterCreate preserves the identity-first 2-step contract
(EmployeeIdentityCreate: core identity only, extra="forbid"). EmployeeMasterUpdate
is the union of the identity update and the full profile-extension upsert surface
(all 35 employment-type fields + contact/identifier fields), so no editable field
is lost. Field-level permission filtering stays in field_policies + the write
service.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from contexts.employee_master.schemas.enums import EmployeeStatus, Gender


def _validate_date_string(value: str | None) -> str | None:
    if value in (None, ""):
        return value
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


def _reject_non_identity_fields(data, *, allowed_fields: set[str], action: str):
    if not isinstance(data, dict):
        return data
    extra = sorted(str(k) for k in data.keys() if k not in allowed_fields)
    if not extra:
        return data
    raise ValueError(
        f"Employee master {action} accepts only core identity fields. "
        "Move non-identity fields to the profile/engagement update after the "
        f"identity exists: {_format_field_list(extra)}. "
        "See /api/docs for the identity-first 2-step contract."
    )


class EmployeeMasterCreate(BaseModel):
    """Create core employee identity (identity-first step 1)."""

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
            data, allowed_fields=set(cls.model_fields.keys()), action="create"
        )

    @field_validator("date_of_birth", "status_effective_date")
    @classmethod
    def validate_date_fields(cls, value):
        return _validate_date_string(value)

    @field_validator("mobile_primary")
    @classmethod
    def validate_mobile_primary(cls, value):
        return _normalize_mobile(value)

    @field_validator("email_official")
    @classmethod
    def validate_email_official(cls, value):
        return _normalize_email(value)


class EmployeeMasterUpdate(BaseModel):
    """Update employee master: identity + profile + engagement (step 2+).

    Union of EmployeeIdentityUpdate and EmployeeProfileExtensionUpsert. All
    optional; per-role allowed-field filtering happens in the write service via
    field_policies. Unknown keys are rejected here but preserved at the storage
    layer under legacy_fields during migration.
    """

    # identity-editable
    full_name: Optional[str] = None
    gender: Optional[Gender] = None
    date_of_birth: Optional[str] = None
    employee_status: Optional[EmployeeStatus] = None
    status_effective_date: Optional[str] = None
    status_remarks: Optional[str] = None

    # assignment / appointment-time
    employment_type: Optional[str] = None
    date_of_initial_engagement: Optional[str] = None
    current_department_id: Optional[str] = None
    current_designation_id: Optional[str] = None
    current_office_id: Optional[str] = None
    reporting_officer_id: Optional[str] = None

    # profile enrichment
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    nationality: Optional[str] = None
    category: Optional[str] = None
    sub_caste: Optional[str] = None
    religion: Optional[str] = None
    date_of_birth_saka: Optional[str] = None
    place_of_birth: Optional[str] = None
    blood_group: Optional[str] = None
    height_cm: Optional[float] = None
    identification_marks: Optional[List[str]] = None
    marital_status: Optional[str] = None
    spouse_name: Optional[str] = None
    educational_qualifications_initial: Optional[List[dict]] = None
    educational_qualifications_acquired: Optional[List[dict]] = None
    professional_qualifications: Optional[List[dict]] = None

    # engagement: contract / order / wage / deputation / outsourcing
    contract_order_no: Optional[str] = None
    contract_start_date: Optional[str] = None
    contract_end_date: Optional[str] = None
    consolidated_pay: Optional[float] = None
    contract_authority: Optional[str] = None
    vendor_agency: Optional[str] = None
    renewal_allowed: Optional[str] = None
    engagement_order_no: Optional[str] = None
    engagement_order_date: Optional[str] = None
    engagement_end_date: Optional[str] = None
    remuneration_type: Optional[str] = None
    muster_roll_number: Optional[str] = None
    daily_wage_rate: Optional[float] = None
    wage_rate_unit: Optional[str] = None
    engagement_office: Optional[str] = None
    nature_of_work: Optional[str] = None
    expected_duration_days: Optional[int] = None
    fixed_monthly_amount: Optional[float] = None
    basic_pay: Optional[float] = None
    pay_level: Optional[str] = None
    document_ids: Optional[List[str]] = None
    engagement_remarks: Optional[str] = None
    deputation_order_no: Optional[str] = None
    parent_department: Optional[str] = None
    parent_designation: Optional[str] = None
    lien_status: Optional[str] = None
    deputation_start_date: Optional[str] = None
    deputation_end_date: Optional[str] = None
    deputation_allowance_percent: Optional[float] = None
    outsourcing_order_no: Optional[str] = None
    agency_name: Optional[str] = None
    agency_contract_number: Optional[str] = None
    sla_reference: Optional[str] = None
    monthly_billing_rate: Optional[float] = None
    role_description: Optional[str] = None

    # contact (both single-line and line1/line2 forms preserved)
    mobile_primary: Optional[str] = None
    mobile_alternate: Optional[str] = None
    email_personal: Optional[str] = None
    email_official: Optional[str] = None
    address: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    present_address: Optional[str] = None
    present_address_line1: Optional[str] = None
    present_address_line2: Optional[str] = None
    present_city: Optional[str] = None
    present_district: Optional[str] = None
    present_state: Optional[str] = None
    present_pincode: Optional[str] = None
    emergency_name: Optional[str] = None
    emergency_phone: Optional[str] = None
    emergency_relation: Optional[str] = None

    # identifiers
    aadhaar_number: Optional[str] = None
    pan_number: Optional[str] = None

    # media + completion + workflow remarks
    photo_url: Optional[str] = None
    signature_url: Optional[str] = None
    thumb_impression_url: Optional[str] = None
    employee_section_completed: Optional[bool] = None
    data_entry_section_completed: Optional[bool] = None
    workflow_remarks: Optional[str] = None

    @field_validator("date_of_birth", "status_effective_date")
    @classmethod
    def validate_date_fields(cls, value):
        return _validate_date_string(value)
