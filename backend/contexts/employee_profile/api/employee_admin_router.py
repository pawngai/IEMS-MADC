from __future__ import annotations

from fastapi import APIRouter

from contexts.employee_profile.api.admin_router import admin_router
from contexts.employee_profile.api.workflow_router import workflow_router

employee_admin_router = APIRouter()
employee_admin_router.include_router(admin_router)
employee_admin_router.include_router(workflow_router)

__all__ = ["employee_admin_router"]


