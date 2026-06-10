from __future__ import annotations

import re
from typing import Any, Optional


# Repos in this project are intentionally thin: MongoDB I/O only.


async def find_user_by_email(db, email: str) -> Optional[dict[str, Any]]:
    normalized = (email or "").strip()
    if not normalized:
        return None
    return await db.users.find_one({
        "email": {
            "$regex": f"^{re.escape(normalized)}$",
            "$options": "i",
        }
    })


async def find_user_by_employee_id(
    db,
    *,
    employee_id: str,
    projection: Optional[dict[str, int]] = None,
) -> Optional[dict[str, Any]]:
    normalized = (employee_id or "").strip()
    if not normalized:
        return None
    return await db.users.find_one({"employee_id": normalized}, projection)


async def find_user_by_id(db, user_id: str, *, projection: Optional[dict[str, int]] = None) -> Optional[dict[str, Any]]:
    return await db.users.find_one({"id": user_id}, projection)


async def list_users(
    db,
    query: dict[str, Any],
    *,
    skip: int,
    limit: int,
    projection: Optional[dict[str, int]] = None,
) -> list[dict[str, Any]]:
    cursor = db.users.find(query, projection).skip(skip).limit(limit)
    return await cursor.to_list(limit)


async def count_users(db, query: dict[str, Any]) -> int:
    return int(await db.users.count_documents(query))


async def insert_user(db, user_doc: dict[str, Any]) -> None:
    await db.users.insert_one(user_doc)


async def update_user(db, user_id: str, updates: dict[str, Any]) -> Optional[dict[str, Any]]:
    await db.users.update_one({"id": user_id}, {"$set": updates})
    return await find_user_by_id(db, user_id, projection={"_id": 0, "password_hash": 0})


async def patch_user_authorities(
    db,
    user_id: str,
    *,
    add: list[str] | None = None,
    remove: list[str] | None = None,
    extra_set: dict[str, Any] | None = None,
) -> Optional[dict[str, Any]]:
    """Atomically add/remove specific authorities without replacing the full list."""
    ops: dict[str, Any] = {}
    if add:
        ops.setdefault("$addToSet", {})["authorities"] = {"$each": add}
    if remove:
        ops.setdefault("$pull", {})
        # $pull can only remove one at a time when combined with $addToSet,
        # so we do two operations if both add and remove are present.
    set_fields = dict(extra_set or {})
    if set_fields:
        ops["$set"] = set_fields

    if remove and add:
        # Two-phase: first add, then remove (to avoid conflicts)
        if ops:
            await db.users.update_one({"id": user_id}, ops)
        await db.users.update_one({"id": user_id}, {"$pullAll": {"authorities": remove}})
    elif remove:
        ops["$pullAll"] = {"authorities": remove}
        if ops:
            await db.users.update_one({"id": user_id}, ops)
    elif ops:
        await db.users.update_one({"id": user_id}, ops)

    return await find_user_by_id(db, user_id, projection={"_id": 0, "password_hash": 0})


async def find_users_with_authority(
    db,
    authority: str,
    *,
    exclude_user_id: str | None = None,
) -> list[dict[str, Any]]:
    """Return active users who hold the given authority, optionally excluding one user."""
    query: dict[str, Any] = {"authorities": authority, "is_active": {"$ne": False}}
    if exclude_user_id:
        query["id"] = {"$ne": exclude_user_id}
    cursor = db.users.find(query, {"_id": 0, "password_hash": 0})
    return await cursor.to_list(length=100)


async def delete_user(db, user_id: str) -> int:
    result = await db.users.delete_one({"id": user_id})
    return int(result.deleted_count)


async def insert_user_activity_log(db, activity: dict[str, Any]) -> None:
    await db.user_activity_logs.insert_one(activity)


async def list_user_activity_logs(
    db,
    query: dict[str, Any],
    *,
    skip: int,
    limit: int,
) -> list[dict[str, Any]]:
    cursor = db.user_activity_logs.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit)
    return await cursor.to_list(limit)


async def aggregate_user_activity_stats(db, pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return await db.user_activity_logs.aggregate(pipeline).to_list(length=1000)


async def insert_role_change_audit(db, doc: dict[str, Any]) -> None:
    await db.role_change_audit.insert_one(doc)


async def list_role_change_history(db, query: dict[str, Any], *, skip: int, limit: int) -> list[dict[str, Any]]:
    cursor = db.role_change_audit.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit)
    return await cursor.to_list(limit)


async def aggregate_role_change_stats(db, pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return await db.role_change_audit.aggregate(pipeline).to_list(length=1000)


async def get_system_config(db) -> Optional[dict[str, Any]]:
    return await db.system_config.find_one({"_id": "main"}, {"_id": 0})


async def set_system_config_key(
    db,
    *,
    key: str,
    value: Any,
    updated_by: str,
    reason: str,
) -> dict[str, Any]:
    updates = {
        key: value,
        "_meta.updated_by": updated_by,
        "_meta.update_reason": reason,
    }
    await db.system_config.update_one(
        {"_id": "main"},
        {"$set": updates},
        upsert=True,
    )
    config = await get_system_config(db)
    return config or {}

