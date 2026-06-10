from __future__ import annotations

from typing import Any

from contexts.service_book.records.repository.service_summary_repository import (
    EmployeeServiceSummaryRepository,
)


async def get_employee_service_summary(db, *, employee_id: str) -> dict[str, Any] | None:
    repository = EmployeeServiceSummaryRepository(db=db)
    return await repository.get_summary(employee_id=employee_id)


async def get_employee_current_department_code(db, *, employee_id: str) -> str | None:
    summary = await get_employee_service_summary(db, employee_id=employee_id)
    value = (summary or {}).get("current_department_id")
    normalized = str(value or "").strip().upper()
    return normalized or None


async def list_employee_ids_by_service_summary(
    db,
    *,
    employment_type: str | None = None,
    department_code: str | None = None,
    limit: int = 5000,
) -> list[str]:
    query: dict[str, Any] = {}
    if employment_type:
        query["current_employment_type_code"] = str(employment_type).strip().upper()
    if department_code:
        query["current_department_id"] = str(department_code).strip().upper()
    if not query:
        return []
    collection = getattr(db, "employee_service_summaries", None)
    if collection is None:
        return []
    cursor = collection.find(query, {"_id": 0, "employee_id": 1})
    rows = await cursor.to_list(length=max(limit, 1))
    return [str(row.get("employee_id") or "") for row in rows if row.get("employee_id")]
