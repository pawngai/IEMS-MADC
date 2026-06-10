from __future__ import annotations

import re
from typing import Any

from contexts.employee_profile.application.profile_interface import (
    get_employee_identity,
    list_employee_ids_by_department,
    resolve_employee_department_code,
)


async def find_identity(
    db,
    *,
    employee_id: str,
    projection: dict | None = None,
) -> dict[str, Any] | None:
    return await get_employee_identity(db, employee_id=employee_id, projection=projection)


async def get_employee_department_code(db, *, employee_id: str) -> str | None:
    return await resolve_employee_department_code(db, employee_id=employee_id)


async def get_employee_ids_for_department(
    db,
    *,
    department_code: str,
    limit: int = 5000,
) -> list[str]:
    return await list_employee_ids_by_department(db, department_code=department_code, limit=limit)


async def get_employee_name_map(
    db,
    *,
    employee_ids: list[str],
) -> dict[str, str]:
    collection = getattr(db, "employee_identities", None)
    if collection is None:
        return {}
    cursor = collection.find(
        {"employee_id": {"$in": employee_ids}},
        {"_id": 0, "employee_id": 1, "full_name": 1},
    )
    return {
        doc["employee_id"]: doc.get("full_name", doc["employee_id"])
        async for doc in cursor
    }


async def list_identities(
    db,
    *,
    search: str | None = None,
    employment_type: str | None = None,
    department_code: str | None = None,
    status: str | None = None,
    limit: int = 500,
    offset: int = 0,
) -> list[dict[str, Any]]:
    collection = getattr(db, "employee_identities", None)
    if collection is None:
        return []
    query: dict[str, Any] = {}
    if department_code:
        query["current_department_id"] = department_code
    if employment_type:
        query["employment_type"] = employment_type
    if status:
        query["employee_status"] = status
    if search:
        safe_search = re.escape(search)
        query["$or"] = [
            {"full_name": {"$regex": safe_search, "$options": "i"}},
            {"employee_id": {"$regex": safe_search, "$options": "i"}},
            {"employee_code": {"$regex": safe_search, "$options": "i"}},
        ]
    return await (
        collection.find(query, {"_id": 0})
        .sort("full_name", 1)
        .skip(offset)
        .limit(limit)
        .to_list(length=limit)
    )


async def count_identities(
    db,
    *,
    search: str | None = None,
    employment_type: str | None = None,
    department_code: str | None = None,
    status: str | None = None,
) -> int:
    collection = getattr(db, "employee_identities", None)
    if collection is None:
        return 0
    query: dict[str, Any] = {}
    if department_code:
        query["current_department_id"] = department_code
    if employment_type:
        query["employment_type"] = employment_type
    if status:
        query["employee_status"] = status
    if search:
        safe_search = re.escape(search)
        query["$or"] = [
            {"full_name": {"$regex": safe_search, "$options": "i"}},
            {"employee_id": {"$regex": safe_search, "$options": "i"}},
            {"employee_code": {"$regex": safe_search, "$options": "i"}},
        ]
    return int(await collection.count_documents(query))
