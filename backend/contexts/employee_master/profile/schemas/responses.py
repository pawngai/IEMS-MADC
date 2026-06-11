"""Employee response and workflow action models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field

from contexts.employee_master.profile.schemas.profile_model import WorkflowStatus


class WorkflowAction(BaseModel):
    """Workflow action request"""
    remarks: Optional[str] = None


class WorkflowActionResponse(BaseModel):
    """Workflow action response"""
    success: bool
    message: str
    employee_id: str
    previous_status: WorkflowStatus
    new_status: WorkflowStatus
    action_performed: str
    performed_by: str
    timestamp: str
    audit_log_id: str


class ProfileAuditLog(BaseModel):
    """Audit log for profile changes"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    action: str

    performed_by_id: str
    performed_by_name: str
    performed_by_role: str

    previous_data: Optional[dict] = None
    new_data: Optional[dict] = None
    changed_fields: List[str] = []

    workflow_status_before: Optional[str] = None
    workflow_status_after: Optional[str] = None
    remarks: Optional[str] = None

    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    integrity_hash: Optional[str] = None


class EmployeeProfileResponse(BaseModel):
    """Response model for employee identity directory rows."""
    employee_id: str
    employee_code: Optional[str]
    full_name: str
    gender: str
    date_of_birth: str
    employment_type: str
    date_of_initial_engagement: str
    current_department_id: str
    current_designation_id: Optional[str]
    current_office_id: Optional[str]
    employee_status: str
    workflow_status: str
    employee_section_completed: Optional[bool] = None
    photo_url: Optional[str]
    created_at: str
    updated_at: str


class EmployeeIdentityResponse(EmployeeProfileResponse):
    """Identity-first response model."""


class EmployeeCompositeProfileResponse(EmployeeProfileResponse):
    """Composed identity + profile-extension response."""

    data_entry_section_completed: Optional[bool] = None
    workflow_remarks: Optional[str] = None


class EmployeeProfileListResponse(BaseModel):
    """Response model for profile list"""
    profiles: List[EmployeeProfileResponse]
    total: int
    page: int
    page_size: int
