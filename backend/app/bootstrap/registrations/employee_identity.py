from __future__ import annotations

from fastapi import APIRouter

from contexts.employee_master.identity.api.router import employee_identities_router


def register(api_router: APIRouter) -> None:
    api_router.include_router(employee_identities_router)
