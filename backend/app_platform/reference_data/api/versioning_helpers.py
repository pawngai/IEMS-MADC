from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Callable


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def actor_identity(current_user: dict) -> tuple[str, str]:
    return current_user.get("sub", "unknown"), current_user.get("email", "unknown")


def build_initial_record(*, code: str, name: str, description: str | None, metadata: dict | None, created_by: str) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "code": code,
        "name": name,
        "description": description,
        "metadata": metadata or {},
        "version": 1,
        "is_active": True,
        "created_at": utc_now_iso(),
        "created_by": created_by,
        "superseded_by": None,
        "superseded_at": None,
    }


def build_updated_version_record(
    *,
    code: str,
    current_record: dict[str, Any],
    updated_name: str | None,
    updated_description: str | None,
    updated_metadata: dict[str, Any] | None,
    created_by: str,
) -> tuple[dict[str, Any], int, str]:
    now = utc_now_iso()
    new_version = int(current_record.get("version", 1)) + 1
    new_record_id = str(uuid.uuid4())

    base_metadata = current_record.get("metadata", {}) or {}
    merged_metadata = {**base_metadata, **(updated_metadata or {})}
    new_record = {
        "id": new_record_id,
        "code": code,
        "name": updated_name or current_record.get("name"),
        "description": (
            updated_description
            if updated_description is not None
            else current_record.get("description")
        ),
        "metadata": merged_metadata,
        "version": new_version,
        "is_active": True,
        "created_at": now,
        "created_by": created_by,
        "superseded_by": None,
        "superseded_at": None,
        "previous_version_id": current_record.get("id"),
    }
    return new_record, new_version, now


def build_deprecated_version_record(
    *,
    code: str,
    current_record: dict[str, Any],
    reason: str,
    created_by: str,
) -> tuple[dict[str, Any], int, str]:
    now = utc_now_iso()
    new_version = int(current_record.get("version", 1)) + 1
    new_record_id = str(uuid.uuid4())
    new_record = {
        "id": new_record_id,
        "code": code,
        "name": current_record.get("name"),
        "description": current_record.get("description"),
        "metadata": {
            **current_record.get("metadata", {}),
            "is_deprecated": True,
            "deprecated_at": now,
            "deprecated_by": created_by,
            "deprecation_reason": reason,
        },
        "version": new_version,
        "is_active": True,
        "created_at": now,
        "created_by": created_by,
        "superseded_by": None,
        "superseded_at": None,
        "previous_version_id": current_record.get("id"),
    }
    return new_record, new_version, now


async def supersede_active_record(
    *,
    collection,
    current_record_raw: dict[str, Any],
    code: str,
    new_record_id: str,
    now: str,
    active_record_query: Callable[[str], dict[str, Any]],
) -> None:
    if "_id" in current_record_raw:
        old_filter: dict[str, Any] = {"_id": current_record_raw["_id"]}
    else:
        old_filter = active_record_query(code)

    await collection.update_one(
        old_filter,
        {
            "$set": {
                "is_active": False,
                "superseded_by": new_record_id,
                "superseded_at": now,
            }
        },
    )
