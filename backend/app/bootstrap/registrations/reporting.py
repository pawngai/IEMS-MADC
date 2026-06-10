from __future__ import annotations

from contexts.reporting.api.router import reporting_router
from fastapi import APIRouter


def register(api_router: APIRouter) -> None:
    api_router.include_router(reporting_router)
