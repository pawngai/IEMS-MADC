from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from contexts.identity_access.identity.infrastructure import repo

async def _log_activity(
    db,
    *,
    action: str,
    current_user: dict,
    target_user: Optional[dict] = None,
    details: Optional[dict] = None,
) -> dict:
    activity = {
        "id": str(uuid.uuid4()),
        "action": action,
        "target_user_id": target_user.get("id") if target_user else None,
        "target_user_email": target_user.get("email") if target_user else None,
        "target_user_name": target_user.get("name") if target_user else None,
        "performed_by_id": current_user["sub"],
        "performed_by_name": current_user.get("name", "Unknown"),
        "performed_by_email": current_user.get("email", "Unknown"),
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await repo.insert_user_activity_log(db, activity)
    return activity


async def _log_role_change(
    db,
    *,
    current_user: dict,
    target_user: dict,
    old_roles: list[str],
    new_roles: list[str],
) -> dict:
    added_roles = list(set(new_roles) - set(old_roles))
    removed_roles = list(set(old_roles) - set(new_roles))

    role_change = {
        "id": str(uuid.uuid4()),
        "target_user_id": target_user.get("id"),
        "target_user_email": target_user.get("email"),
        "target_user_name": target_user.get("name"),
        "old_roles": old_roles,
        "new_roles": new_roles,
        "roles_added": added_roles,
        "roles_removed": removed_roles,
        "changed_by_id": current_user["sub"],
        "changed_by_name": current_user.get("name", "Unknown"),
        "changed_by_email": current_user.get("email", "Unknown"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "change_type": (
            "ROLE_ASSIGNMENT"
            if added_roles
            else "ROLE_REVOCATION" if removed_roles else "ROLE_MODIFICATION"
        ),
    }
    await repo.insert_role_change_audit(db, role_change)
    return role_change

