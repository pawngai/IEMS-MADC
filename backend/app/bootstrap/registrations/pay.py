from __future__ import annotations

from contexts.pay_benefits.api.router import pay_router
from fastapi import APIRouter


def register(api_router: APIRouter) -> None:
    api_router.include_router(pay_router)
