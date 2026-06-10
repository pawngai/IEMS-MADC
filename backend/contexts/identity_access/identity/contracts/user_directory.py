from __future__ import annotations

from datetime import datetime, timezone
import secrets
import uuid

import bcrypt

from contexts.identity_access.contracts.access_control import has_authority


async def find_user_by_email(
    db,
    *,
    email: str,
    projection: dict | None = None,
) -> dict | None:
    if not email:
        return None
    return await db.users.find_one(
        {"email": email},
        projection or {"_id": 0},
    )


async def get_user_department_code(db, *, user_id: str) -> str | None:
    user = await db.users.find_one(
        {"id": user_id},
        {"_id": 0, "department_code": 1},
    )
    value = (user or {}).get("department_code")
    if not value:
        return None
    return str(value).strip().upper()


async def find_user_by_employee_id(
    db,
    *,
    employee_id: str,
    projection: dict | None = None,
) -> dict | None:
    if not employee_id:
        return None
    return await db.users.find_one(
        {"employee_id": employee_id},
        projection or {"_id": 0},
    )


async def get_user_display_name(db, *, user_id: str) -> str:
    user = await db.users.find_one(
        {"id": user_id},
        {"_id": 0, "name": 1, "email": 1},
    )
    if not user:
        return user_id
    return user.get("name") or user.get("email") or user_id


async def count_users(
    db,
    *,
    query: dict | None = None,
) -> int:
    return int(await db.users.count_documents(query or {}))


async def create_auto_provisioned_employee_user(
    db,
    *,
    employee_id: str,
    full_name: str,
    email: str,
    department_code: str,
    created_by: str,
) -> dict | None:
    if not email:
        return None

    existing = await find_user_by_email(db, email=email, projection={"_id": 0, "id": 1})
    if existing:
        return None

    temp_password = f"Tmp@{secrets.token_hex(4).upper()}"
    password_hash = bcrypt.hashpw(temp_password.encode(), bcrypt.gensalt()).decode()
    user_id = str(uuid.uuid4())

    await db.users.insert_one(
        {
            "id": user_id,
            "email": email,
            "password_hash": password_hash,
            "name": full_name,
            "authorities": ["EMPLOYEE"],
            "employee_id": employee_id,
            "department_code": department_code,
            "is_active": True,
            "must_change_password": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": created_by,
            "auto_provisioned": True,
        }
    )

    return {
        "user_id": user_id,
        "email": email,
        "temp_password": temp_password,
        "must_change_password": True,
        "message": "Account auto-created. A temporary password has been generated.",
    }


# ---------------------------------------------------------------------------
# Department-scoped authority sync
# ---------------------------------------------------------------------------

_DEPT_SCOPED_AUTHORITIES = {"HOD", "DEPT_DATA_ENTRY"}


async def sync_department_authority(
    db,
    *,
    employee_id: str,
    authority: str,
    department_code: str,
    actor_sub: str,
) -> dict:
    """Grant *authority* to the user linked to *employee_id* and revoke it
    from any current holder.  Identity context owns the write — boundary-safe
    for callers in other contexts.

    Returns ``{"granted_to": user_id, "revoked_from": old_user_id | None}``.
    Raises ``ValueError`` for invalid inputs.
    """
    authority = (authority or "").strip().upper()
    if authority not in _DEPT_SCOPED_AUTHORITIES:
        raise ValueError(f"sync_department_authority only handles {_DEPT_SCOPED_AUTHORITIES}")

    employee_id = (employee_id or "").strip()
    department_code = (department_code or "").strip().upper()
    if not employee_id or not department_code:
        raise ValueError("employee_id and department_code are required")

    # 1. Resolve target user
    target = await db.users.find_one(
        {"employee_id": employee_id},
        {"_id": 0, "password_hash": 0},
    )
    if not target:
        raise ValueError(f"No user record linked to employee_id={employee_id}")

    target_id = target["id"]

    # 2. Revoke from current holder(s) in the SAME department only
    revoked_from: str | None = None
    holders = await db.users.find(
        {
            "authorities": authority,
            "department_code": department_code,
            "is_active": {"$ne": False},
            "id": {"$ne": target_id},
        },
        {"_id": 0, "id": 1},
    ).to_list(length=100)

    for holder in holders:
        await db.users.update_one(
            {"id": holder["id"]},
            {"$pull": {"authorities": authority}},
        )
        revoked_from = holder["id"]

    # 3. Grant to target (idempotent)
    now = datetime.now(timezone.utc).isoformat()
    await db.users.update_one(
        {"id": target_id},
        {
            "$addToSet": {"authorities": authority},
            "$set": {
                "department_code": department_code,
                "updated_at": now,
                "updated_by": actor_sub,
            },
        },
    )

    return {"granted_to": target_id, "revoked_from": revoked_from}


async def revoke_department_authority(
    db,
    *,
    employee_id: str,
    authority: str,
    actor_sub: str,
) -> dict:
    """Revoke *authority* from the user linked to *employee_id* without
    granting it to anyone else.

    Returns ``{"revoked_from": user_id | None}``.
    """
    authority = (authority or "").strip().upper()
    if authority not in _DEPT_SCOPED_AUTHORITIES:
        raise ValueError(f"revoke_department_authority only handles {_DEPT_SCOPED_AUTHORITIES}")

    employee_id = (employee_id or "").strip()
    if not employee_id:
        return {"revoked_from": None}

    target = await db.users.find_one(
        {"employee_id": employee_id},
        {"_id": 0, "id": 1, "authorities": 1},
    )
    if not target:
        return {"revoked_from": None}

    if not has_authority(target, authority):
        return {"revoked_from": None}

    now = datetime.now(timezone.utc).isoformat()
    await db.users.update_one(
        {"id": target["id"]},
        {
            "$pull": {"authorities": authority},
            "$set": {"updated_at": now, "updated_by": actor_sub},
        },
    )
    return {"revoked_from": target["id"]}
