"""Seniority Management domain models (request / response schemas)."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    service: str = Field(..., min_length=1, description="Service name")
    designation_code: Optional[str] = Field(default=None, description="Designation code (optional)")
    title: Optional[str] = None
    list_type: str = Field(default="DRAFT", description="DRAFT | PROVISIONAL | FINAL")


class RankOverride(BaseModel):
    employee_id: str
    new_rank: int = Field(..., ge=1)


class RankOverrideRequest(BaseModel):
    overrides: List[RankOverride] = Field(..., min_length=1)
    reason: str = Field(..., min_length=5)


class WorkflowActionRequest(BaseModel):
    remarks: Optional[str] = None


class PromoteRequest(BaseModel):
    remarks: Optional[str] = None
