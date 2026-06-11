"""
System-admin entry point for department-owned establishment rows.

The route is mounted in the admin console namespace, but the data and write
rules stay in the Department bounded context.
"""

from __future__ import annotations

from typing import Any

from app_platform.auth.current_user import get_current_user
from app_platform.db.runtime import get_db
from contexts.organization_master.services import sanctioned_strength_service
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field


department_admin_establishment_router = APIRouter(
    prefix="/departments/manage",
    tags=["Department Establishment"],
)


class AdminSanctionedStrengthUpdateRequest(BaseModel):
    sanctioned_strength: list[dict[str, Any]] = Field(default_factory=list)
    reason: str = Field(..., min_length=3)


@department_admin_establishment_router.get("/{code}/sanctioned-strength")
async def get_department_sanctioned_strength(
    code: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await sanctioned_strength_service.get_sanctioned_strength_for_department_admin(
        db,
        code,
        current_user=current_user,
    )


@department_admin_establishment_router.put("/{code}/sanctioned-strength")
async def update_department_sanctioned_strength(
    code: str,
    payload: AdminSanctionedStrengthUpdateRequest,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await sanctioned_strength_service.update_sanctioned_strength_for_department_admin(
        db,
        code,
        current_user=current_user,
        rows=payload.sanctioned_strength,
        reason=payload.reason,
    )
