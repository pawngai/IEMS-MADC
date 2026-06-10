from __future__ import annotations

from contexts.identity.contracts.user_directory import (
    revoke_department_authority as _revoke_department_authority,
    sync_department_authority as _sync_department_authority,
)


async def sync_department_authority(
    db,
    *,
    employee_id: str,
    authority: str,
    department_code: str,
    actor_sub: str,
) -> dict:
    return await _sync_department_authority(
        db,
        employee_id=employee_id,
        authority=authority,
        department_code=department_code,
        actor_sub=actor_sub,
    )


async def revoke_department_authority(
    db,
    *,
    employee_id: str,
    authority: str,
    actor_sub: str,
) -> dict:
    return await _revoke_department_authority(
        db,
        employee_id=employee_id,
        authority=authority,
        actor_sub=actor_sub,
    )


__all__ = ["sync_department_authority", "revoke_department_authority"]