"""Employee Master response models.

EmployeeDirectoryItem  == legacy EmployeeProfileResponse (directory row).
EmployeeMasterResponse == legacy EmployeeCompositeProfileResponse (full read).
Field sets preserved exactly; only the container names change (mapping §B).
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class EmployeeDirectoryItem(BaseModel):
    """Directory row (was EmployeeProfileResponse)."""

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


class EmployeeMasterResponse(EmployeeDirectoryItem):
    """Composed identity + profile-extension read (was EmployeeCompositeProfileResponse)."""

    data_entry_section_completed: Optional[bool] = None
    workflow_remarks: Optional[str] = None


class EmployeeDirectoryListResponse(BaseModel):
    """Paged directory response (was EmployeeProfileListResponse)."""

    profiles: List[EmployeeDirectoryItem]
    total: int
    page: int
    page_size: int
