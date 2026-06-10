from __future__ import annotations

from typing import Optional

from contexts.seniority.application.seniority_service import list_designation_codes, list_services
from contexts.seniority.domain.seniority_policy import (
    ROLE_APPROVER,
    ROLE_DATA_ENTRY_SET,
    ROLE_VERIFIER,
    require_role,
)
from contexts.seniority.infrastructure.seniority_repository import get_list, list_lists


VIEW_ROLES = ROLE_DATA_ENTRY_SET | {ROLE_VERIFIER, ROLE_APPROVER, "SYSTEM_ADMIN"}


async def list_available_services(*, db, current_user: dict):
    require_role(current_user, VIEW_ROLES, "view seniority services")
    return await list_services(db)


async def list_available_designations(*, db, current_user: dict):
    require_role(current_user, VIEW_ROLES, "view seniority designations")
    return await list_designation_codes(db)


async def list_seniority_lists(
    *,
    db,
    current_user: dict,
    status: Optional[str],
    service: Optional[str],
    list_type: Optional[str],
    year: Optional[int],
    limit: int,
    offset: int,
) -> dict:
    require_role(current_user, VIEW_ROLES, "view seniority lists")
    query = {}
    if status:
        query["status"] = status.upper()
    if service:
        query["service"] = service
    if list_type:
        query["list_type"] = list_type.upper()
    if year:
        query["created_at"] = {
            "$gte": f"{year}-01-01T00:00:00",
            "$lt": f"{year + 1}-01-01T00:00:00",
        }

    items, total = await list_lists(db, query=query, limit=limit, offset=offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


async def get_seniority_list(*, db, current_user: dict, list_id: str) -> dict:
    require_role(current_user, VIEW_ROLES, "view seniority list")
    doc = await get_list(db, list_id)
    doc.pop("_id", None)
    return doc


async def get_seniority_list_for_export(*, db, current_user: dict, list_id: str) -> dict:
    require_role(current_user, VIEW_ROLES, "export seniority list")
    return await get_list(db, list_id)
