from __future__ import annotations

from typing import Any, List

from fastapi import HTTPException
from pydantic import BaseModel, Field

from contexts.rbac.application.access_control import require_system_admin
from contexts.service_book.contracts.service_book_directory import count_service_book_parts


def get_db():
    from app_platform.db.runtime import mongo_state

    if mongo_state.db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    return mongo_state.db


async def _count_service_book_parts(db, employee_id: str) -> int:
    """Count Service Book parts via the published Service Book contract."""
    return await count_service_book_parts(db, employee_id=employee_id)


class WorkflowUnlockRequest(BaseModel):
    reason: str = Field(..., min_length=10, description="Mandatory reason for unlock")


class SystemConfigUpdate(BaseModel):
    key: str
    value: Any
    reason: str = Field(..., min_length=10)


class EmployeeDeleteRequest(BaseModel):
    reason: str = Field(..., min_length=10, description="Mandatory reason for deletion")


class TransitionOverrideRequest(BaseModel):
    workflow_type: str = Field(..., description="profile | service_book | leave")
    from_stage: str
    to_stage: str
    authorities: List[str] = Field(..., min_length=1, description="Authorities allowed for this transition")
    reason: str = Field(..., min_length=10)


class SodToggleRequest(BaseModel):
    rule_index: int = Field(..., ge=0, description="Index of the SOD rule to toggle")
    enabled: bool = Field(..., description="True = enforced, False = disabled")
    reason: str = Field(..., min_length=10)


class WorkflowConfigResetRequest(BaseModel):
    reason: str = Field(..., min_length=10, description="Mandatory reason for reset")
