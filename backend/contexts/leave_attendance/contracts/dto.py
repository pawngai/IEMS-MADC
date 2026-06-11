from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LeaveStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    RECOMMENDED = "RECOMMENDED"
    SANCTIONED = "SANCTIONED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class LeaveAttachmentDTO(BaseModel):
    url: str
    filename: str
    original_name: Optional[str] = None
    file_size: Optional[int] = None
    content_type: Optional[str] = None


class LeaveApplicationCreateDTO(BaseModel):
    leave_type_code: str = Field(..., description="Leave code (EL, HPL, CL, etc.)")
    from_date: str = Field(..., description="YYYY-MM-DD")
    to_date: str = Field(..., description="YYYY-MM-DD")
    reason: str
    leave_station: Optional[str] = None
    contact_during_leave: str
    medical_certificate_provided: Optional[bool] = None
    commuted_leave_basis: Optional[str] = Field(
        default=None,
        description="Commuted leave basis, for example MEDICAL or STUDY_PUBLIC_INTEREST",
    )
    expected_delivery_date: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    childbirth_date: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    adoption_date: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    child_date_of_birth: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    child_has_disability: Optional[bool] = None
    child_order: Optional[int] = None
    attachments: list[LeaveAttachmentDTO] = Field(default_factory=list)


class LeaveActionDTO(BaseModel):
    remarks: Optional[str] = None
    order_number: Optional[str] = None
    order_date: Optional[str] = None


class LeaveApplicationResponseDTO(BaseModel):
    id: str
    employee_id: str
    employee_name: Optional[str] = None
    leave_type_code: str
    from_date: str
    to_date: str
    days_applied: float
    reason: str
    leave_station: Optional[str] = None
    contact_during_leave: Optional[str] = None
    medical_certificate_provided: Optional[bool] = None
    commuted_leave_basis: Optional[str] = None
    expected_delivery_date: Optional[str] = None
    childbirth_date: Optional[str] = None
    adoption_date: Optional[str] = None
    child_date_of_birth: Optional[str] = None
    child_has_disability: Optional[bool] = None
    child_order: Optional[int] = None
    attachments: list[LeaveAttachmentDTO] = Field(default_factory=list)
    status: str
    applied_by: str
    applied_at: str
    recommended_by: Optional[str] = None
    recommended_by_name: Optional[str] = None
    recommended_at: Optional[str] = None
    sanctioned_by: Optional[str] = None
    sanctioned_at: Optional[str] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[str] = None
    remarks: Optional[str] = None
    order_number: Optional[str] = None
    order_date: Optional[str] = None
