from __future__ import annotations

from typing import Any


async def list_collection(
    db,
    collection_name: str,
    *,
    query: dict[str, Any] | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    cursor = getattr(db, collection_name).find(query or {}, {"_id": 0}).limit(limit)
    return await cursor.to_list(limit)


async def list_employment_types(db) -> list[dict[str, Any]]:
    return await list_collection(db, "employment_types", limit=100)


async def list_service_event_types(db) -> list[dict[str, Any]]:
    return await list_collection(db, "service_event_types", limit=100)


async def list_leave_types(db) -> list[dict[str, Any]]:
    return await list_collection(db, "leave_types", limit=100)


async def list_pay_levels(db) -> list[dict[str, Any]]:
    return await list_collection(db, "pay_levels", limit=100)


async def list_service_groups(db) -> list[dict[str, Any]]:
    return await list_collection(db, "service_groups", limit=100)


async def list_services(db) -> list[dict[str, Any]]:
    return await list_collection(db, "services", limit=100)


async def list_caste_categories(db) -> list[dict[str, Any]]:
    return await list_collection(db, "caste_categories", limit=100)


async def list_departments(db) -> list[dict[str, Any]]:
    return await list_collection(db, "departments", limit=100)


async def list_designations(db) -> list[dict[str, Any]]:
    return await list_collection(db, "designations", limit=100)


async def list_offices(db, *, department_code: str | None) -> list[dict[str, Any]]:
    query: dict[str, Any] = {}
    if department_code:
        query["department_code"] = department_code
    return await list_collection(db, "offices", query=query, limit=100)
