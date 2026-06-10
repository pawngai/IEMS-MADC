from __future__ import annotations

from fastapi import APIRouter

from contexts.seniority.api.router import seniority_router


def register(api_router: APIRouter) -> None:
    api_router.include_router(seniority_router)
