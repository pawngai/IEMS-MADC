from __future__ import annotations

from contexts.identity.api.router import users_router
from fastapi import APIRouter


def register(api_router: APIRouter) -> None:
    api_router.include_router(users_router)
