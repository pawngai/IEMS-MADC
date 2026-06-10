from __future__ import annotations

from app_platform.db.runtime import get_db
from contexts.service_book.application.errors import ServiceBookApplicationError
from contexts.service_book.application.queries.print_queries import ServiceBookPrintUseCases
from fastapi import APIRouter, Depends, HTTPException
from app_platform.auth.current_user import get_current_user


service_book_print_router = APIRouter()


def get_service_book_print_use_cases(db=Depends(get_db)) -> ServiceBookPrintUseCases:
    return ServiceBookPrintUseCases(db=db)


def _raise_http(exc: ServiceBookApplicationError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@service_book_print_router.get("/employees/{employee_id}/print/part/{part_key}")
async def print_service_book_part(
    employee_id: str,
    part_key: str,
    use_cases: ServiceBookPrintUseCases = Depends(get_service_book_print_use_cases),
    current_user: dict = Depends(get_current_user),
):
    try:
        return await use_cases.build_part(
            employee_ref=employee_id,
            part_key=part_key,
            current_user=current_user,
        )
    except ServiceBookApplicationError as exc:
        _raise_http(exc)


@service_book_print_router.get("/employees/{employee_id}/print/full")
async def print_service_book_full(
    employee_id: str,
    use_cases: ServiceBookPrintUseCases = Depends(get_service_book_print_use_cases),
    current_user: dict = Depends(get_current_user),
):
    try:
        return await use_cases.build_full(
            employee_ref=employee_id,
            current_user=current_user,
        )
    except ServiceBookApplicationError as exc:
        _raise_http(exc)
