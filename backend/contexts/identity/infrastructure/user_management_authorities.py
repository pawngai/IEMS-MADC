from __future__ import annotations

from contexts.identity.infrastructure import repo
from contexts.identity.infrastructure.user_management_roles import NON_EXCLUSIVE_AUTHORITIES, _valid_authorities
from contexts.identity_access.contracts.access_control import require_system_admin

async def list_authorities(*, current_user: dict) -> dict:
    require_system_admin(current_user)
    return {"authorities": _valid_authorities()}


async def get_authority_holders(db, *, current_user: dict) -> dict:
    """Return {authority: {user_id, name, email}} for every non-EMPLOYEE role
    currently held by an active user."""
    require_system_admin(current_user)

    holders: dict[str, dict[str, str]] = {}
    for auth in _valid_authorities():
        if auth in NON_EXCLUSIVE_AUTHORITIES:
            continue
        users = await repo.find_users_with_authority(db, auth)
        if users:
            u = users[0]
            holders[auth] = {
                "user_id": u.get("id", ""),
                "name": u.get("name", ""),
                "email": u.get("email", ""),
            }
    return {"holders": holders}

