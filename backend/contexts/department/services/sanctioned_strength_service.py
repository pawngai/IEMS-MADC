from __future__ import annotations

from typing import Any, Callable, Awaitable

from contexts.department.domain.sanctioned_strength import normalize_sanctioned_strength_rows
from contexts.department.repository import department_portal_repo as repo
from contexts.department.services.portal_common import _actor_identity, _normalize
from fastapi import HTTPException

from contexts.rbac.contracts.access_control import require_permissions, require_system_admin
from contexts.rbac.contracts.models import Permission

ResolveDepartment = Callable[[Any, dict], Awaitable[str]]
RequireAuthority = Callable[[dict], None]


async def build_sanctioned_strength_summary(
    db,
    department_code: str,
    *,
    repository=repo,
) -> dict[str, Any]:
    configured_rows = await repository.get_department_establishment_rows(db, department_code)
    items: list[dict[str, Any]] = []
    sanctioned_total = 0
    filled_total = 0
    vacancy_total = 0
    over_strength_total = 0

    for row in configured_rows:
        designation_code = _normalize(row.get("designation_code"))
        if not designation_code:
            continue

        employment_type = _normalize(row.get("employment_type")) or None
        sanctioned_count = int(row.get("sanctioned_count") or 0)
        filled_count = await repository.count_active_employees_for_establishment_row(
            db,
            department_code,
            designation_code=designation_code,
            employment_type=employment_type,
        )
        vacancy_count = max(sanctioned_count - filled_count, 0)
        over_strength_count = max(filled_count - sanctioned_count, 0)
        occupancy_rate = round((filled_count / sanctioned_count) * 100) if sanctioned_count > 0 else 0

        items.append(
            {
                "designation_code": designation_code,
                "employment_type": employment_type,
                "sanctioned_count": sanctioned_count,
                "filled_count": filled_count,
                "vacancy_count": vacancy_count,
                "over_strength_count": over_strength_count,
                "occupancy_rate": occupancy_rate,
                "order_number": row.get("order_number"),
                "order_date": row.get("order_date"),
                "remarks": row.get("remarks"),
            }
        )

        sanctioned_total += sanctioned_count
        filled_total += filled_count
        vacancy_total += vacancy_count
        over_strength_total += over_strength_count

    return {
        "configured": len(items) > 0,
        "items": items,
        "total_rows": len(items),
        "totals": {
            "sanctioned_strength_total": sanctioned_total,
            "filled_strength_total": filled_total,
            "vacancy_count": vacancy_total,
            "over_strength_count": over_strength_total,
        },
    }


async def get_sanctioned_strength(
    db,
    *,
    current_user: dict,
    resolve_department: ResolveDepartment,
    require_department_authority: RequireAuthority,
    repository=repo,
) -> dict[str, Any]:
    require_permissions(current_user, Permission.IDENTITY_READ_ALL)
    require_department_authority(current_user)

    department_code = await resolve_department(db, current_user)
    dept_info = await repository.get_department_info(db, department_code)
    department_name = (dept_info or {}).get("name") if dept_info else None
    establishment = await build_sanctioned_strength_summary(
        db,
        department_code,
        repository=repository,
    )

    return {
        "department_code": department_code,
        "department_name": department_name,
        **establishment,
    }


async def update_sanctioned_strength(
    db,
    *,
    current_user: dict,
    rows: list[dict[str, Any]],
    reason: str,
    resolve_department: ResolveDepartment,
    require_department_authority: RequireAuthority,
    repository=repo,
) -> dict[str, Any]:
    require_permissions(current_user, Permission.PROFILE_UPDATE_ALL)
    require_department_authority(current_user)

    department_code = await resolve_department(db, current_user)
    normalized_rows = normalize_sanctioned_strength_rows(rows)
    actor_id, actor_email = _actor_identity(current_user)

    await repository.upsert_department_establishment(
        db,
        department_code,
        items=normalized_rows,
        reason=reason.strip(),
        actor_id=actor_id,
        actor_email=actor_email,
    )

    establishment = await build_sanctioned_strength_summary(
        db,
        department_code,
        repository=repository,
    )
    return {
        "success": True,
        "department_code": department_code,
        "message": "Sanctioned strength updated.",
        "reason": reason.strip(),
        **establishment,
    }


async def get_sanctioned_strength_for_department_admin(
    db,
    department_code: str,
    *,
    current_user: dict,
    repository=repo,
) -> dict[str, Any]:
    require_system_admin(current_user)

    normalized_department_code = _normalize(department_code)
    if not normalized_department_code:
        raise HTTPException(status_code=400, detail="department_code is required.")

    dept_info = await repository.get_department_info(db, normalized_department_code)
    if not dept_info:
        raise HTTPException(
            status_code=404,
            detail=f"Department not found: {normalized_department_code}",
        )

    establishment = await build_sanctioned_strength_summary(
        db,
        normalized_department_code,
        repository=repository,
    )

    return {
        "department_code": normalized_department_code,
        "department_name": dept_info.get("name"),
        **establishment,
    }


async def update_sanctioned_strength_for_department_admin(
    db,
    department_code: str,
    *,
    current_user: dict,
    rows: list[dict[str, Any]],
    reason: str,
    repository=repo,
) -> dict[str, Any]:
    require_system_admin(current_user)

    normalized_department_code = _normalize(department_code)
    if not normalized_department_code:
        raise HTTPException(status_code=400, detail="department_code is required.")

    dept_info = await repository.get_department_info(db, normalized_department_code)
    if not dept_info:
        raise HTTPException(
            status_code=404,
            detail=f"Department not found: {normalized_department_code}",
        )

    normalized_rows = normalize_sanctioned_strength_rows(rows)
    actor_id, actor_email = _actor_identity(current_user)

    await repository.upsert_department_establishment(
        db,
        normalized_department_code,
        items=normalized_rows,
        reason=reason.strip(),
        actor_id=actor_id,
        actor_email=actor_email,
    )

    establishment = await build_sanctioned_strength_summary(
        db,
        normalized_department_code,
        repository=repository,
    )
    return {
        "success": True,
        "department_code": normalized_department_code,
        "department_name": dept_info.get("name"),
        "message": "Sanctioned strength updated.",
        "reason": reason.strip(),
        **establishment,
    }


__all__ = [
    "build_sanctioned_strength_summary",
    "get_sanctioned_strength",
    "get_sanctioned_strength_for_department_admin",
    "update_sanctioned_strength",
    "update_sanctioned_strength_for_department_admin",
]
