from __future__ import annotations

from typing import Any


def _approved_query(employee_id: str | None = None) -> dict[str, Any]:
    query: dict[str, Any] = {
        "status": "APPROVED",
        "is_voided": {"$ne": True},
    }
    if employee_id:
        query["employee_id"] = employee_id
    return query


async def list_approved_service_event_records(
    db,
    *,
    employee_id: str | None = None,
    limit: int = 10000,
) -> list[dict[str, Any]]:
    """Contract query for projections rebuilt from official Service Book records."""

    cursor = db.service_book_records.find(_approved_query(employee_id), {"_id": 0}).sort(
        [("employee_id", 1), ("sequence", 1)]
    )
    return await cursor.to_list(length=limit)
