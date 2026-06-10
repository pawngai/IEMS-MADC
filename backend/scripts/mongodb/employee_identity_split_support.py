from __future__ import annotations

from typing import Any

from contexts.employee_profile.domain.identity_layers import (
    compose_employee_record_view,
    split_employee_payload,
    utc_now_iso,
)


MIGRATION_MARKER = "employee-identity-split-v2"


def build_split_documents(
    profile: dict[str, Any],
    *,
    migrated_at: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    migrated_at = migrated_at or utc_now_iso()
    identity, extension = split_employee_payload(profile)

    employee_id = str(profile.get("employee_id") or "").strip()
    created_at = profile.get("created_at") or migrated_at
    updated_at = profile.get("updated_at") or migrated_at
    created_by = profile.get("created_by")
    updated_by = profile.get("updated_by") or created_by
    version = int(profile.get("version") or 1)

    identity.update(
        {
            "employee_id": employee_id,
            "created_at": identity.get("created_at") or created_at,
            "updated_at": identity.get("updated_at") or updated_at,
            "version": int(identity.get("version") or version),
            "identity_migration_marker": MIGRATION_MARKER,
            "identity_migration_at": migrated_at,
        }
    )
    if created_by is not None:
        identity.setdefault("created_by", created_by)
    if updated_by is not None:
        identity.setdefault("updated_by", updated_by)

    extension.update(
        {
            "employee_id": employee_id,
            "created_at": extension.get("created_at") or created_at,
            "updated_at": extension.get("updated_at") or updated_at,
            "version": int(extension.get("version") or version),
            "workflow_status": extension.get("workflow_status")
            or profile.get("workflow_status")
            or "DRAFT",
            "employee_section_completed": bool(
                extension.get("employee_section_completed")
                if "employee_section_completed" in extension
                else profile.get("employee_section_completed")
            ),
            "data_entry_section_completed": bool(
                extension.get("data_entry_section_completed")
                if "data_entry_section_completed" in extension
                else profile.get("data_entry_section_completed")
            ),
            "profile_extension_migration_marker": MIGRATION_MARKER,
            "profile_extension_migration_at": migrated_at,
        }
    )
    if created_by is not None:
        extension.setdefault("created_by", created_by)
    if updated_by is not None:
        extension.setdefault("updated_by", updated_by)

    projection = compose_employee_record_view(identity, extension)
    projection["read_model_updated_at"] = migrated_at
    projection["read_model_migration_marker"] = MIGRATION_MARKER
    projection["read_model_migration_at"] = migrated_at

    return identity, extension, projection


async def backfill_employee_profile_split(
    db,
    *,
    employee_id: str | None = None,
    dry_run: bool = False,
    overwrite: bool = False,
) -> dict[str, Any]:
    query = {"employee_id": employee_id} if employee_id else {}
    cursor = db.employee_profiles.find(query, {"_id": 0})

    summary: dict[str, Any] = {
        "dry_run": dry_run,
        "overwrite": overwrite,
        "migration_marker": MIGRATION_MARKER,
        "profiles_scanned": 0,
        "profiles_backfilled": 0,
        "identities_written": 0,
        "extensions_written": 0,
        "read_models_written": 0,
        "employees": [],
    }

    async for profile in cursor:
        summary["profiles_scanned"] += 1
        current_employee_id = str(profile.get("employee_id") or "").strip()
        if not current_employee_id:
            continue

        migrated_at = utc_now_iso()
        identity, extension, projection = build_split_documents(
            profile,
            migrated_at=migrated_at,
        )

        existing_identity = await db.employee_identities.find_one(
            {"employee_id": current_employee_id},
            {"_id": 0},
        )
        existing_extension = await db.employee_profile_extensions.find_one(
            {"employee_id": current_employee_id},
            {"_id": 0},
        )

        writes = {
            "employee_id": current_employee_id,
            "identity_written": overwrite or not bool(existing_identity),
            "extension_written": overwrite or not bool(existing_extension),
            "read_model_written": True,
        }

        projection_identity = identity if writes["identity_written"] else (existing_identity or identity)
        projection_extension = extension if writes["extension_written"] else (existing_extension or extension)
        projection = compose_employee_record_view(projection_identity, projection_extension)
        projection["read_model_updated_at"] = migrated_at
        projection["read_model_migration_marker"] = MIGRATION_MARKER
        projection["read_model_migration_at"] = migrated_at

        if not dry_run:
            if writes["identity_written"]:
                await db.employee_identities.replace_one(
                    {"employee_id": current_employee_id},
                    identity,
                    upsert=True,
                )
            if writes["extension_written"]:
                await db.employee_profile_extensions.replace_one(
                    {"employee_id": current_employee_id},
                    extension,
                    upsert=True,
                )
            await db.employee_profile_read_models.replace_one(
                {"employee_id": current_employee_id},
                projection,
                upsert=True,
            )

        summary["profiles_backfilled"] += 1
        summary["identities_written"] += int(writes["identity_written"])
        summary["extensions_written"] += int(writes["extension_written"])
        summary["read_models_written"] += 1
        summary["employees"].append(writes)

    return summary
