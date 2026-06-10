from __future__ import annotations

from fastapi import APIRouter


service_book_verification_router = APIRouter(prefix="/verification", tags=["Service Book Verification"])

__all__ = ["service_book_verification_router"]
