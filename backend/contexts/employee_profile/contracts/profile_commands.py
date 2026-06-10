from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from contexts.employee_profile.application.profile_interface import (
    apply_employee_profile_updates,
    get_employee_profile,
)
from contexts.employee_identity.contracts.identity_directory import find_identity
from contexts.employee_profile.contracts.profile_directory import (
    _has_collection,
)
from contexts.employee_profile.domain.identity_layers import (
    compose_employee_record_view,
    utc_now_iso,
)


async def update_profile_fields(
    db,
    *,
    employee_id: str,
    updates: dict,
    session=None,
) -> None:
    await apply_employee_profile_updates(
        db,
        employee_id=employee_id,
        updates=updates,
        session=session,
    )


async def refresh_profile_projection(
    db,
    *,
    employee_id: str,
    allow_identity_workflow: bool = False,
) -> None:
    if not _has_collection(db, "employee_profile_read_models"):
        return

    identity = await find_identity(
        db,
        employee_id=employee_id,
        projection={"_id": 0},
    )
    if identity is not None and not allow_identity_workflow and not _identity_can_seed_profile(identity):
        await db.employee_profile_read_models.delete_one({"employee_id": employee_id})
        return

    extension = None
    if _has_collection(db, "employee_profile_extensions"):
        extension = await db.employee_profile_extensions.find_one(
            {"employee_id": employee_id},
            {"_id": 0},
        )
    composed = compose_employee_record_view(identity, extension)
    if not composed:
        await db.employee_profile_read_models.delete_one({"employee_id": employee_id})
        return

    payload = dict(composed)
    payload["read_model_updated_at"] = utc_now_iso()
    created_at = payload.pop("created_at", None) or utc_now_iso()
    await db.employee_profile_read_models.update_one(
        {"employee_id": employee_id},
        {"$set": payload, "$setOnInsert": {"created_at": created_at}},
        upsert=True,
    )


async def archive_and_delete_profile(
    db,
    *,
    employee_id: str,
    actor_user_id: str,
    reason: str,
) -> dict[str, Any] | None:
    profile = await get_employee_profile(
        db,
        employee_id=employee_id,
        projection={"_id": 0},
    )
    if not profile:
        return None

    archived = dict(profile)
    archived["deleted_at"] = datetime.now(timezone.utc).isoformat()
    archived["deleted_by"] = actor_user_id
    archived["delete_reason"] = reason

    if getattr(db, "employee_profiles_deleted", None) is not None:
        await db.employee_profiles_deleted.insert_one(archived)
    if getattr(db, "employee_profile_extensions", None) is not None:
        await db.employee_profile_extensions.delete_one({"employee_id": employee_id})
    if getattr(db, "employee_profile_read_models", None) is not None:
        await db.employee_profile_read_models.delete_one({"employee_id": employee_id})

    return archived


def _identity_can_seed_profile(identity: dict[str, Any] | None) -> bool:
    if not identity:
        return False
    workflow_status = str(identity.get("workflow_status") or "").strip().upper()
    return workflow_status in {"", "DRAFT", "SUBMITTED", "VERIFIED", "ACTIVE"}


__all__ = [
    "archive_and_delete_profile",
    "refresh_profile_projection",
    "update_profile_fields",
]