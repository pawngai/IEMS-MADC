from __future__ import annotations

from contexts.employee_identity.contracts.identity_directory import find_identity
from contexts.service_book.application.service import (
    generateServiceBookPrintModel,
    validateServiceBookEligibility,
)


async def build_part_print_view(*, db, employee_id: str, part_key: str) -> dict:
    identity = await find_identity(db, employee_id=employee_id)
    validateServiceBookEligibility(identity)
    return await generateServiceBookPrintModel(
        db=db,
        employee_id=employee_id,
        employee_or_type=identity,
        part_key=part_key,
    )


async def build_full_print_view(*, db, employee_id: str) -> dict:
    identity = await find_identity(db, employee_id=employee_id)
    validateServiceBookEligibility(identity)
    return await generateServiceBookPrintModel(
        db=db,
        employee_id=employee_id,
        employee_or_type=identity,
    )
