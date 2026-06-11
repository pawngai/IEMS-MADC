from __future__ import annotations

from fastapi import APIRouter

from contexts.employee_master.profile.api.admin_router import admin_router
from contexts.employee_master.profile.api.completion_router import completion_router
from contexts.employee_master.profile.api.read_router import read_router
from contexts.employee_master.profile.api.workflow_router import workflow_router
from contexts.employee_master.profile.api.write_router import write_router

employee_profiles_router = APIRouter(
    prefix="/employee-profiles",
    tags=["Employee Profiles"],
)
employee_profiles_router.include_router(completion_router)
employee_profiles_router.include_router(read_router)
employee_profiles_router.include_router(workflow_router)
employee_profiles_router.include_router(admin_router)
employee_profiles_router.include_router(write_router)

__all__ = ["employee_profiles_router"]
