from __future__ import annotations

from contexts.service_book.api.router import service_book_router
from fastapi import APIRouter


def register(api_router: APIRouter) -> None:
    api_router.include_router(service_book_router)
