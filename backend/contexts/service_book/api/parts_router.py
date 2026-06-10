from __future__ import annotations

from fastapi import APIRouter


service_book_parts_router = APIRouter(prefix="/parts", tags=["Service Book Parts"])

__all__ = ["service_book_parts_router"]
