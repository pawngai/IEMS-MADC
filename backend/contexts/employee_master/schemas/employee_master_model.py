"""Employee Master canonical document model.

EmployeeMasterSnapshot is the canonical merge of:
  - employee_identity.schemas.identity_model.EmployeeIdentity
  - employee_profile.schemas.profile_model.EmployeeIdentity (snapshot)
  - employee_profile.schemas.profile_model.EmployeeProfileExtension
  - the 35 employment-type fields accepted by EmployeeProfileExtensionUpsert and
    persisted loose on the profile document (inventory §2.5)

Zero field loss is mandatory. Any document key not declared here is preserved
under `legacy_fields` (risk R-1/R-3). See docs/refactor/.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from contexts.employee_master.schemas.enums import (
    EmployeeStatus,
    EmploymentType,
    Gender,
    WorkflowStatus,
)
from contexts.employee_master.schemas.value_objects import (
    ContactDetails,
    IdentityDocuments,
)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EmployeeMasterSnapshot(BaseModel):
    """Canonical, composed employee master record (identity + profile + engagement)."""

    # ── Identity core (employee_identity.EmployeeIdentity) ──────────────
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Document ID")
    employee_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="System-generated unique ID; cross-context join key",
    )
    employee_code: Optional[str] = None
    full_name: str = Field(..., min_length=2, max_length=100)
    gender: Gender
    date_of_birth: str
    employee_status: EmployeeStatus = Field(default=EmployeeStatus.ACTIVE)
    status_effective_date: Optional[str] = None
    status_remarks: Optional[str] = None

    # ── Appointment-time + current assignment (profile snapshot) ────────
    employment_type: Optional[EmploymentType] = None
    date_of_initial_engagement: Optional[str] = None
    current_department_id: Optional[str] = None       # FK -> organization_master
    current_designation_id: Optional[str] = None      # FK -> organization_master
    current_office_id: Optional[str] = None           # FK -> organization_master
    reporting_officer_id: Optional[str] = None        # FK -> employee_master (self)

    # ── Profile enrichment (EmployeeProfileExtension) ───────────────────
    father_name: Optional[str] = Field(None, max_length=100)
    mother_name: Optional[str] = Field(None, max_length=100)
    nationality: str = Field(default="Indian", max_length=50)
    category: Optional[str] = None
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

    # ── Embedded value objects ──────────────────────────────────────────
    contact: ContactDetails = Field(default_factory=ContactDetails)
    identifiers: Optional[IdentityDocuments] = None

    # ── Media ───────────────────────────────────────────────────────────
    photo_url: Optional[str] = None
    photo_updated_at: Optional[str] = None
    signature_url: Optional[str] = None
    thumb_impression_url: Optional[str] = None

    # ── Workflow / completion ───────────────────────────────────────────
    workflow_status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT)
    workflow_remarks: Optional[str] = None
    employee_section_completed: bool = Field(default=False)
    data_entry_section_completed: bool = Field(default=False)

    # ── Engagement: contract (inventory §2.5) ───────────────────────────
    contract_order_no: Optional[str] = None
    contract_start_date: Optional[str] = None
    contract_end_date: Optional[str] = None
    consolidated_pay: Optional[float] = None
    contract_authority: Optional[str] = None
    vendor_agency: Optional[str] = None
    renewal_allowed: Optional[str] = None

    # ── Engagement: order / wage ────────────────────────────────────────
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
    engagement_remarks: Optional[str] = None
    document_ids: List[str] = Field(default_factory=list)  # FK -> app_platform/documents

    # ── Engagement: deputation ──────────────────────────────────────────
    deputation_order_no: Optional[str] = None
    parent_department: Optional[str] = None
    parent_designation: Optional[str] = None
    lien_status: Optional[str] = None
    deputation_start_date: Optional[str] = None
    deputation_end_date: Optional[str] = None
    deputation_allowance_percent: Optional[float] = None

    # ── Engagement: outsourcing ─────────────────────────────────────────
    outsourcing_order_no: Optional[str] = None
    agency_name: Optional[str] = None
    agency_contract_number: Optional[str] = None
    sla_reference: Optional[str] = None
    monthly_billing_rate: Optional[float] = None
    role_description: Optional[str] = None

    # ── Audit columns ───────────────────────────────────────────────────
    created_at: str = Field(default_factory=_utcnow_iso)
    created_by: Optional[str] = None
    updated_at: str = Field(default_factory=_utcnow_iso)
    updated_by: Optional[str] = None
    verified_at: Optional[str] = None
    verified_by: Optional[str] = None
    approved_at: Optional[str] = None
    approved_by: Optional[str] = None
    locked_at: Optional[str] = None
    locked_by: Optional[str] = None
    version: int = Field(default=1)

    # ── Catch-all: any unknown legacy key is preserved, never dropped ───
    legacy_fields: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("date_of_birth")
    @classmethod
    def _validate_dob(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("Date must be in YYYY-MM-DD format") from exc
        return v

    @field_validator("date_of_initial_engagement", "status_effective_date")
    @classmethod
    def _validate_optional_dates(cls, v):
        if v in (None, ""):
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("Date must be in YYYY-MM-DD format") from exc
        return v
