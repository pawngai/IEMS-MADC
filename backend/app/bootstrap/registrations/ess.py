from __future__ import annotations

from contexts.ess.api.router import ess_router
from fastapi import APIRouter


def register(api_router: APIRouter) -> None:
    api_router.include_router(ess_router)
