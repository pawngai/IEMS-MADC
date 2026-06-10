from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from contexts.employee_identity.contracts.employee_domain import isServiceBookEligible
from contexts.service_book.domain.service_book_rules import (
    SERVICE_BOOK_NOT_APPLICABLE_DETAIL,
    ServiceBookNotApplicableError,
    require_regular_employee_service_book,
)
from contexts.service_book.read_side.application.factory import (
    build_service_book_service,
)


def _resolve_service_book_eligibility(employee_or_type: Any) -> bool:
    if isinstance(employee_or_type, dict) and "eligible_for_service_book" in employee_or_type:
        return bool(employee_or_type.get("eligible_for_service_book"))
    return isServiceBookEligible(employee_or_type)


def validateServiceBookEligibility(employee_or_type: Any) -> bool:
    is_eligible = _resolve_service_book_eligibility(employee_or_type)
    try:
        return require_regular_employee_service_book(is_eligible=is_eligible)
    except ServiceBookNotApplicableError as exc:
        raise HTTPException(
            status_code=403,
            detail=SERVICE_BOOK_NOT_APPLICABLE_DETAIL,
        ) from exc


def buildServiceBookService(*, db):
    return build_service_book_service(db=db)


async def createServiceBookIfEligible(
    *,
    db,
    employee_id: str,
    employee_or_type: Any,
) -> dict[str, Any]:
    validateServiceBookEligibility(employee_or_type)
    service = buildServiceBookService(db=db)
    await service.get_service_book(employee_id=employee_id)
    return {"employee_id": employee_id, "projection_ready": True}


async def rebuildServiceBookProjection(
    *,
    db,
    employee_id: str,
    employee_or_type: Any,
) -> dict[str, Any]:
    validateServiceBookEligibility(employee_or_type)
    service = buildServiceBookService(db=db)
    rebuilt = await service.rebuild_from_approved_events(employee_id=employee_id)
    service_book = await service.get_service_book(employee_id=employee_id)
    return {
        **rebuilt,
        "service_book": service_book,
    }


async def generateServiceBookPrintModel(
    *,
    db,
    employee_id: str,
    employee_or_type: Any,
    part_key: str | None = None,
) -> dict[str, Any]:
    validateServiceBookEligibility(employee_or_type)
    service = buildServiceBookService(db=db)
    if part_key:
        return await service.build_part_print_view(employee_id=employee_id, part_key=part_key)
    return await service.build_full_print_view(employee_id=employee_id)
