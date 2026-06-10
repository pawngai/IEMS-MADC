from __future__ import annotations

from fastapi import APIRouter

from contexts.department.api.admin_establishment_router import department_admin_establishment_router
from contexts.system_admin.department.api.management_router import dept_management_router
from contexts.system_admin.api.router import system_admin_router


def register(api_router: APIRouter) -> None:
    api_router.include_router(system_admin_router)
    api_router.include_router(dept_management_router)
    api_router.include_router(department_admin_establishment_router)
