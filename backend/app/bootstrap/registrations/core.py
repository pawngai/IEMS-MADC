from __future__ import annotations

from contexts.identity_access.identity.api.router import auth_router
from app_platform.reference_data.api.router import masters_router
from fastapi import APIRouter


def register(api_router: APIRouter) -> None:
    api_router.include_router(auth_router)
    api_router.include_router(masters_router)
    api_router.include_router(APIRouter(prefix="/establishment", tags=["Establishment"]))

