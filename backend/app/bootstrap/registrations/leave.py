from __future__ import annotations

from contexts.leave.api.router import leave_router
from fastapi import APIRouter


def register(api_router: APIRouter) -> None:
    api_router.include_router(leave_router)
