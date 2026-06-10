from __future__ import annotations

from fastapi import APIRouter


service_book_corrections_router = APIRouter(prefix="/corrections", tags=["Service Book Corrections"])

__all__ = ["service_book_corrections_router"]
