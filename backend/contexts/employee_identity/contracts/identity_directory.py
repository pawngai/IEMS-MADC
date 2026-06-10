from __future__ import annotations

from typing import Any

from contexts.employee_identity.application.identity_interface import (
    count_employee_identities,
    get_employee_identity,
    get_employee_name_map as get_employee_name_map_query,
    get_identity_editor_bootstrap,
    list_employee_ids_by_department,
    list_employee_identities,
    resolve_employee_department_code,
)


async def find_identity(
    db,
    *,
    employee_id: str,
    projection: dict | None = None,
) -> dict[str, Any] | None:
    return await get_employee_identity(db, employee_id=employee_id, projection=projection)


async def resolve_identity_ref(
    db,
    *,
    ref: str,
    projection: dict | None = None,
) -> dict[str, Any] | None:
    """Resolve either an employee_id (UUID) or employee_code to an identity dict."""
    return await get_employee_identity(db, employee_id=ref, projection=projection)


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
    return await get_employee_name_map_query(db, employee_ids=employee_ids)


async def find_identities_by_ids(
    db,
    *,
    employee_ids: list[str],
    projection: dict | None = None,
) -> list[dict[str, Any]]:
    """Batch lookup identities by employee_ids via the owned collection."""
    if not employee_ids:
        return []
    proj = projection or {"_id": 0}
    cursor = db.employee_identities.find(
        {"employee_id": {"$in": employee_ids}},
        proj,
    )
    return await cursor.to_list(length=len(employee_ids))


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
    return await list_employee_identities(
        db,
        search=search,
        employment_type=employment_type,
        department_code=department_code,
        status=status,
        skip=offset,
        limit=limit,
    )


async def count_identities(
    db,
    *,
    search: str | None = None,
    employment_type: str | None = None,
    department_code: str | None = None,
    status: str | None = None,
) -> int:
    return await count_employee_identities(
        db,
        search=search,
        employment_type=employment_type,
        department_code=department_code,
        status=status,
    )


async def get_identity_bootstrap(db) -> dict[str, Any]:
    return await get_identity_editor_bootstrap(db)
