from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from fastapi import HTTPException

from backend.contexts.organization_master.domain.sanctioned_strength import (
    normalize_sanctioned_strength_rows,
)


MIGRATION_MARKER = "department-establishment-backfill-v1"
CLEANUP_MARKER = "department-establishment-cleanup-v1"
MIGRATION_ACTOR = "migration-script"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_legacy_sanctioned_strength_rows(
    department_record: dict[str, Any],
) -> list[dict[str, Any]]:
    metadata = department_record.get("metadata") or {}
    return normalize_sanctioned_strength_rows(metadata.get("sanctioned_strength"))


def build_establishment_document(
    department_record: dict[str, Any],
    *,
    migrated_at: str | None = None,
    existing_document: dict[str, Any] | None = None,
) -> dict[str, Any]:
    migrated_at = migrated_at or utc_now_iso()
    code = str(department_record.get("code") or "").strip().upper()
    if not code:
        raise ValueError("Department code is required for establishment backfill.")

    items = get_legacy_sanctioned_strength_rows(department_record)
    existing_document = existing_document or {}

    created_at = (
        existing_document.get("created_at")
        or department_record.get("updated_at")
        or department_record.get("created_at")
        or migrated_at
    )
    created_by = (
        existing_document.get("created_by")
        or department_record.get("updated_by")
        or department_record.get("created_by")
        or MIGRATION_ACTOR
    )

    return {
        "id": existing_document.get("id") or str(uuid.uuid4()),
        "department_code": code,
        "items": items,
        "created_at": created_at,
        "created_by": created_by,
        "updated_at": migrated_at,
        "updated_by": MIGRATION_ACTOR,
        "migration_marker": MIGRATION_MARKER,
        "migration_at": migrated_at,
    }


async def backfill_department_establishments(
    db,
    *,
    department_code: str | None = None,
    dry_run: bool = False,
    overwrite: bool = False,
) -> dict[str, Any]:
    normalized_department_code = (
        str(department_code or "").strip().upper() or None
    )
    query = {"code": normalized_department_code} if normalized_department_code else {}
    cursor = db.departments.find(query, {"_id": 0})

    summary: dict[str, Any] = {
        "dry_run": dry_run,
        "overwrite": overwrite,
        "migration_marker": MIGRATION_MARKER,
        "departments_scanned": 0,
        "departments_backfilled": 0,
        "establishments_written": 0,
        "logs_written": 0,
        "skipped_empty": 0,
        "skipped_existing": 0,
        "errors": [],
        "departments": [],
    }

    async for department in cursor:
        summary["departments_scanned"] += 1
        code = str(department.get("code") or "").strip().upper()
        metadata = department.get("metadata") or {}
        raw_rows = metadata.get("sanctioned_strength") or []

        if not code:
            summary["errors"].append(
                {"department_code": None, "error": "Missing department code."}
            )
            continue

        if not raw_rows:
            summary["skipped_empty"] += 1
            summary["departments"].append(
                {"department_code": code, "action": "skipped_empty", "item_count": 0}
            )
            continue

        existing = await db.department_establishments.find_one(
            {"department_code": code},
            {"_id": 0},
        )
        if existing and not overwrite:
            summary["skipped_existing"] += 1
            summary["departments"].append(
                {
                    "department_code": code,
                    "action": "skipped_existing",
                    "item_count": len(existing.get("items") or []),
                }
            )
            continue

        migrated_at = utc_now_iso()
        try:
            document = build_establishment_document(
                department,
                migrated_at=migrated_at,
                existing_document=existing,
            )
        except (HTTPException, ValueError) as exc:
            summary["errors"].append(
                {"department_code": code, "error": str(getattr(exc, "detail", exc))}
            )
            continue

        action = "backfill_overwrite" if existing else "backfill_create"
        if not dry_run:
            await db.department_establishments.replace_one(
                {"department_code": code},
                document,
                upsert=True,
            )
            await db.department_establishment_logs.insert_one(
                {
                    "id": str(uuid.uuid4()),
                    "timestamp": migrated_at,
                    "action": action.upper(),
                    "department_code": code,
                    "actor_id": MIGRATION_ACTOR,
                    "actor_email": MIGRATION_ACTOR,
                    "reason": "Backfilled from legacy departments.metadata.sanctioned_strength.",
                    "before_state": existing,
                    "after_state": document,
                    "migration_marker": MIGRATION_MARKER,
                }
            )

        summary["departments_backfilled"] += 1
        summary["establishments_written"] += 1
        summary["logs_written"] += 0 if dry_run else 1
        summary["departments"].append(
            {
                "department_code": code,
                "action": action,
                "item_count": len(document.get("items") or []),
            }
        )

    return summary


async def cleanup_legacy_department_establishment_metadata(
    db,
    *,
    department_code: str | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    normalized_department_code = str(department_code or "").strip().upper() or None
    query = {"code": normalized_department_code} if normalized_department_code else {}
    cursor = db.departments.find(query, {"_id": 0})

    summary: dict[str, Any] = {
        "dry_run": dry_run,
        "force": force,
        "migration_marker": CLEANUP_MARKER,
        "departments_scanned": 0,
        "departments_cleaned": 0,
        "departments_updated": 0,
        "logs_written": 0,
        "skipped_empty": 0,
        "skipped_missing_establishment": 0,
        "skipped_mismatch": 0,
        "errors": [],
        "departments": [],
    }

    async for department in cursor:
        summary["departments_scanned"] += 1
        code = str(department.get("code") or "").strip().upper()
        metadata = department.get("metadata") or {}
        raw_rows = metadata.get("sanctioned_strength") or []

        if not code:
            summary["errors"].append(
                {"department_code": None, "error": "Missing department code."}
            )
            continue

        if not raw_rows:
            summary["skipped_empty"] += 1
            summary["departments"].append(
                {"department_code": code, "action": "skipped_empty", "item_count": 0}
            )
            continue

        try:
            legacy_rows = get_legacy_sanctioned_strength_rows(department)
        except (HTTPException, ValueError) as exc:
            summary["errors"].append(
                {"department_code": code, "error": str(getattr(exc, "detail", exc))}
            )
            continue

        establishment = await db.department_establishments.find_one(
            {"department_code": code},
            {"_id": 0},
        )
        if not establishment:
            summary["skipped_missing_establishment"] += 1
            summary["departments"].append(
                {
                    "department_code": code,
                    "action": "skipped_missing_establishment",
                    "item_count": len(legacy_rows),
                }
            )
            continue

        canonical_rows = normalize_sanctioned_strength_rows(establishment.get("items"))
        if legacy_rows != canonical_rows and not force:
            summary["skipped_mismatch"] += 1
            summary["departments"].append(
                {
                    "department_code": code,
                    "action": "skipped_mismatch",
                    "legacy_item_count": len(legacy_rows),
                    "canonical_item_count": len(canonical_rows),
                }
            )
            continue

        if not dry_run:
            await db.departments.update_one(
                {"code": code},
                {"$unset": {"metadata.sanctioned_strength": ""}},
            )
            await db.department_establishment_logs.insert_one(
                {
                    "id": str(uuid.uuid4()),
                    "timestamp": utc_now_iso(),
                    "action": "CLEANUP_LEGACY_METADATA",
                    "department_code": code,
                    "actor_id": MIGRATION_ACTOR,
                    "actor_email": MIGRATION_ACTOR,
                    "reason": "Removed legacy departments.metadata.sanctioned_strength after canonical backfill.",
                    "before_state": {"sanctioned_strength": legacy_rows},
                    "after_state": {"legacy_metadata_removed": True},
                    "migration_marker": CLEANUP_MARKER,
                }
            )

        summary["departments_cleaned"] += 1
        summary["departments_updated"] += 0 if dry_run else 1
        summary["logs_written"] += 0 if dry_run else 1
        summary["departments"].append(
            {
                "department_code": code,
                "action": "cleanup_remove",
                "item_count": len(legacy_rows),
            }
        )

    return summary