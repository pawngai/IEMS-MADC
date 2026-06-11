from __future__ import annotations

from fastapi import APIRouter

from contexts.employee_master.profile.api.router import employee_profiles_router


def register(api_router: APIRouter) -> None:
    api_router.include_router(employee_profiles_router)
