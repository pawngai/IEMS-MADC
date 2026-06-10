"""
ESS (Employee Self-Service) Portal — Pydantic schemas.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class EssContactUpdate(BaseModel):
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    religion: Optional[str] = None
    blood_group: Optional[str] = None
    category: Optional[str] = None
    marital_status: Optional[str] = None
    spouse_name: Optional[str] = None

    mobile_number: Optional[str] = None
    mobile_alternate: Optional[str] = None
    alternate_mobile: Optional[str] = None
    personal_email: Optional[str] = None
    email_personal: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_number: Optional[str] = None
    emergency_name: Optional[str] = None
    emergency_phone: Optional[str] = None
    emergency_relation: Optional[str] = None

    current_address_line1: Optional[str] = None
    current_address_line2: Optional[str] = None
    current_city: Optional[str] = None
    current_state_code: Optional[str] = None
    current_pincode: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None

    aadhaar_number: Optional[str] = None
    pan_number: Optional[str] = None
    photo_url: Optional[str] = None


class EssProfileSummary(BaseModel):
    employee_id: str
    employee_code: Optional[str] = None
    full_name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    employment_type: Optional[str] = None
    current_department_id: Optional[str] = None
    current_designation_id: Optional[str] = None
    current_office_id: Optional[str] = None
    employee_status: Optional[str] = None
    workflow_status: Optional[str] = Field(
        default=None,
        description="Profile workflow status. Terminal status is LOCKED.",
    )
    contact: Optional[dict] = None
    date_of_initial_engagement: Optional[str] = None


class ServiceBookPartSummary(BaseModel):
    part: str
    entry_count: int


class EssServiceBookResponse(BaseModel):
    employee_id: str
    employee_name: Optional[str] = None
    available_parts: List[str] = []
    parts: dict = {}


class NotificationType(str, Enum):
    PROFILE_STATUS = "PROFILE_STATUS"
    LEAVE_STATUS = "LEAVE_STATUS"
    SERVICE_BOOK_UPDATE = "SERVICE_BOOK_UPDATE"
    SYSTEM = "SYSTEM"


class EssNotification(BaseModel):
    id: str
    type: str
    title: str
    message: str
    level: str = "info"
    timestamp: str
    read: bool = False
    action_url: Optional[str] = None


class EssNotificationsResponse(BaseModel):
    notifications: List[EssNotification] = []
    unread_count: int = 0


class EssActivityEntry(BaseModel):
    id: str
    source: str
    action: str
    details: Optional[str] = None
    actor: Optional[str] = None
    timestamp: str


class EssActivityResponse(BaseModel):
    activities: List[EssActivityEntry] = []
    total: int = 0


class EssDashboardStats(BaseModel):
    profile_status: Optional[str] = None
    workflow_status: Optional[str] = Field(
        default=None,
        description="Profile workflow status summary. Terminal status is LOCKED.",
    )
    service_book_entries: int = 0
    pending_leaves: int = 0
    approved_leaves: int = 0
    leave_balance_summary: dict = {}
    notifications_unread: int = 0
