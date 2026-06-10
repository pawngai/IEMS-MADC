from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


MIGRATION_ACTOR = "migration:004_move_employee_identity_assignment_fields_to_profile"
MOVED_FIELDS = (
    "employment_type",
    "date_of_initial_engagement",
    "current_department_id",
)


def _normalize_index_key(key: Any) -> tuple[tuple[str, int], ...]:
    return tuple((str(name), int(direction)) for name, direction in (key or []))


async def _drop_assignment_indexes(collection) -> None:
    expected_keys = {
        (("current_department_id", 1),),
        (("employment_type", 1),),
    }
    index_info = await collection.index_information()
    for index_name, metadata in index_info.items():
        if _normalize_index_key(metadata.get("key")) in expected_keys:
            await collection.drop_index(index_name)


def _pick_profile_assignment_values(identity: dict[str, Any], extension: dict[str, Any] | None) -> dict[str, Any]:
    values: dict[str, Any] = {}
    extension = extension or {}
    for field_name in MOVED_FIELDS:
        extension_value = extension.get(field_name)
        if extension_value is not None and extension_value != "":
            values[field_name] = extension_value
            continue
        identity_value = identity.get(field_name)
        if identity_value is not None and identity_value != "":
            values[field_name] = identity_value
    return values


async def run(db) -> None:
    identities = await db.employee_identities.find(
        {"$or": [{field_name: {"$exists": True}} for field_name in MOVED_FIELDS]},
        {"_id": 0},
    ).to_list(length=None)
    if not identities:
        await _drop_assignment_indexes(db.employee_identities)
        return

    now = datetime.now(timezone.utc).isoformat()

    for identity in identities:
        employee_id = str(identity.get("employee_id") or "").strip()
        if not employee_id:
            continue

        extension = None
        if getattr(db, "employee_profile_extensions", None) is not None:
            extension = await db.employee_profile_extensions.find_one(
                {"employee_id": employee_id},
                {"_id": 0},
            )

        assignment_values = _pick_profile_assignment_values(identity, extension)
        if assignment_values and getattr(db, "employee_profile_extensions", None) is not None:
            next_version = int((extension or {}).get("version") or 0) + 1
            await db.employee_profile_extensions.update_one(
                {"employee_id": employee_id},
                {
                    "$set": {
                        **assignment_values,
                        "updated_at": now,
                        "updated_by": MIGRATION_ACTOR,
                        "version": next_version,
                    },
                    "$setOnInsert": {
                        "employee_id": employee_id,
                        "created_at": (extension or {}).get("created_at")
                        or identity.get("created_at")
                        or now,
                        "created_by": (extension or {}).get("created_by") or MIGRATION_ACTOR,
                    },
                },
                upsert=True,
            )

        if assignment_values and getattr(db, "employee_profile_read_models", None) is not None:
            await db.employee_profile_read_models.update_one(
                {"employee_id": employee_id},
                {
                    "$set": {
                        **assignment_values,
                        "updated_at": now,
                        "updated_by": MIGRATION_ACTOR,
                        "read_model_updated_at": now,
                    },
                    "$setOnInsert": {
                        "employee_id": employee_id,
                    },
                },
                upsert=True,
            )

        await db.employee_identities.update_one(
            {"employee_id": employee_id},
            {
                "$unset": {field_name: "" for field_name in MOVED_FIELDS},
                "$set": {
                    "updated_at": now,
                    "updated_by": MIGRATION_ACTOR,
                    "version": int(identity.get("version") or 1) + 1,
                },
            },
        )

    await _drop_assignment_indexes(db.employee_identities)