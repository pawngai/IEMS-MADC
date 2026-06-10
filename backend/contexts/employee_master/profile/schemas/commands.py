"""Employee profile command models built on top of employee_identity."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, model_validator


def _format_field_list(fields: list[str], *, limit: int = 8) -> str:
    if len(fields) <= limit:
        return ", ".join(fields)
    visible = ", ".join(fields[:limit])
    return f"{visible}, and {len(fields) - limit} more"


def _reject_unexpected_extension_fields(
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

    raise ValueError(
        "Employee profile extension "
        f"{action} accepts only employee-owned profile fields. "
        "Move service-book or service-history fields to their owning context: "
        f"{_format_field_list(extra_fields)}."
    )


class EmployeeProfileExtensionUpsert(BaseModel):
    """Model for employee-owned profile enrichment updates."""

    @model_validator(mode="before")
    @classmethod
    def reject_unexpected_fields(cls, data):
        return _reject_unexpected_extension_fields(
            data,
            allowed_fields=set(cls.model_fields.keys()),
            action="update",
        )

    employment_type: Optional[str] = None
    date_of_initial_engagement: Optional[str] = None
    current_department_id: Optional[str] = None
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
    mobile_primary: Optional[str] = None
    mobile_alternate: Optional[str] = None
    email_personal: Optional[str] = None
    email_official: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    present_address_line1: Optional[str] = None
    present_address_line2: Optional[str] = None
    present_city: Optional[str] = None
    present_district: Optional[str] = None
    present_state: Optional[str] = None
    present_pincode: Optional[str] = None
    emergency_name: Optional[str] = None
    emergency_phone: Optional[str] = None
    emergency_relation: Optional[str] = None
    aadhaar_number: Optional[str] = None
    pan_number: Optional[str] = None
    photo_url: Optional[str] = None
    signature_url: Optional[str] = None
    thumb_impression_url: Optional[str] = None
    employee_section_completed: Optional[bool] = None
    data_entry_section_completed: Optional[bool] = None
    workflow_remarks: Optional[str] = None


class EmployeeProfileExtensionESSUpdate(BaseModel):
    """Model for ESS updates on the employee-owned profile extension."""

    @model_validator(mode="before")
    @classmethod
    def reject_unexpected_fields(cls, data):
        return _reject_unexpected_extension_fields(
            data,
            allowed_fields=set(cls.model_fields.keys()),
            action="update",
        )

    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    religion: Optional[str] = None
    blood_group: Optional[str] = None
    category: Optional[str] = None
    sub_caste: Optional[str] = None
    date_of_birth_saka: Optional[str] = None
    place_of_birth: Optional[str] = None
    height_cm: Optional[float] = None
    identification_marks: Optional[List[str]] = None
    marital_status: Optional[str] = None
    spouse_name: Optional[str] = None
    educational_qualifications_initial: Optional[List[dict]] = None
    educational_qualifications_acquired: Optional[List[dict]] = None
    professional_qualifications: Optional[List[dict]] = None
    mobile_primary: Optional[str] = None
    mobile_alternate: Optional[str] = None
    email_personal: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    present_address_line1: Optional[str] = None
    present_address_line2: Optional[str] = None
    present_city: Optional[str] = None
    present_district: Optional[str] = None
    present_state: Optional[str] = None
    present_pincode: Optional[str] = None
    emergency_name: Optional[str] = None
    emergency_phone: Optional[str] = None
    emergency_relation: Optional[str] = None
    aadhaar_number: Optional[str] = None
    pan_number: Optional[str] = None
    photo_url: Optional[str] = None
    signature_url: Optional[str] = None
    thumb_impression_url: Optional[str] = None
    employee_section_completed: Optional[bool] = None
