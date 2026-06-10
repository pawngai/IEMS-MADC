from __future__ import annotations

from typing import Any

from contexts.identity.infrastructure import repo


async def get_system_config(db) -> dict[str, Any]:
    config = await repo.get_system_config(db)
    return config or {}


async def set_system_config_key(
    db,
    *,
    key: str,
    value: Any,
    updated_by: str,
    reason: str,
) -> dict[str, Any]:
    return await repo.set_system_config_key(
        db,
        key=key,
        value=value,
        updated_by=updated_by,
        reason=reason,
    )
