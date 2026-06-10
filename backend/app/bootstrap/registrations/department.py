from __future__ import annotations

from fastapi import APIRouter

from contexts.department.api.router import department_portal_router


def register(api_router: APIRouter) -> None:
    api_router.include_router(department_portal_router)