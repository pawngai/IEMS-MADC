from __future__ import annotations

from pydantic import BaseModel, Field


class EmployeeWorkflowEventDTO(BaseModel):
    employee_id: str
    status: str
    remarks: str | None = None
    actor_id: str | None = None
    department_id: str | None = None


class EmployeeWorkflowAuditDTO(BaseModel):
    employee_id: str
    action: str
    user_id: str
    user_name: str
    user_role: str
    status_before: str | None = None
    status_after: str | None = None
    remarks: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    previous_data: dict | None = None
    new_data: dict | None = None
    changed_fields: list[str] = Field(default_factory=list)
