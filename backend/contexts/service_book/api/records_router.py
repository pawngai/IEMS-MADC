from __future__ import annotations

from fastapi import APIRouter

from contexts.service_book.records.api.router import (
    employee_service_summaries_router,
    service_book_records_command_router,
    service_records_router,
)


service_book_records_router = APIRouter(tags=["Service Book Records"])
service_book_records_router.include_router(service_book_records_command_router)
service_book_records_router.include_router(service_records_router)
service_book_records_router.include_router(employee_service_summaries_router)

__all__ = ["service_book_records_router"]
