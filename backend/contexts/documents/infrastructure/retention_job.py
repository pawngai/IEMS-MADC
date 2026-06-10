"""Retention sweep — archives expired documents and permanently deletes
already-archived documents whose ``delete_after_archive_days`` has elapsed.

The job is idempotent and safe to run repeatedly. It never touches documents
under legal hold or already-superseded version-history rows that still have
successors.

Operational shape: run from a cron / scheduler. ``run_once`` returns a
summary; the caller logs / emits metrics.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app_platform.event_bus.types import EventName
from contexts.documents.domain.retention import (
    RetentionPolicy,
    is_eligible_for_archive,
    is_eligible_for_delete,
    select_policy,
)
from contexts.documents.infrastructure.event_publish import publish_document_event
from contexts.documents.infrastructure.metadata_ops import (
    delete_document_metadata,
    metadata_repository,
    read_document_metadata,
    write_document_metadata,
)
from contexts.documents.infrastructure.storage import StorageBucket
from contexts.documents.infrastructure.storage_ops import storage
from contexts.documents.repository.retention_policy_repository import RetentionPolicyRepository


async def run_once(
    *,
    db,
    now: datetime | None = None,
    actor_id: str | None = "system:retention",
) -> dict[str, Any]:
    """Scan all known document metadata and apply retention transitions.

    Returns: ``{"archived": int, "deleted": int, "skipped_legal_hold": int,
    "no_policy": int}``."""
    if db is None:
        return {"archived": 0, "deleted": 0, "skipped_legal_hold": 0, "no_policy": 0}

    when = now or datetime.now(timezone.utc)
    policies = await RetentionPolicyRepository(db=db).list_active()
    if not policies:
        return {"archived": 0, "deleted": 0, "skipped_legal_hold": 0, "no_policy": 0}

    summary = {"archived": 0, "deleted": 0, "skipped_legal_hold": 0, "no_policy": 0}
    async for row in _iter_all_metadata(db):
        if row.get("legal_hold"):
            summary["skipped_legal_hold"] += 1
            continue

        policy = select_policy(row, policies)
        if policy is None:
            summary["no_policy"] += 1
            continue

        filename = row.get("filename")
        if not filename:
            continue

        if row.get("archived_at"):
            if is_eligible_for_delete(row, policy, now=when):
                await _permanent_delete(filename, row, db=db, actor_id=actor_id)
                summary["deleted"] += 1
            continue

        if is_eligible_for_archive(row, policy, now=when):
            await _archive(filename, row, policy=policy, db=db, actor_id=actor_id, now=when)
            summary["archived"] += 1

    return summary


async def _iter_all_metadata(db):
    from contexts.documents.repository.metadata_repository import COLLECTION

    await metadata_repository(db=db).ensure_indexes()
    cursor = db[COLLECTION].find({}, {"_id": 0})
    async for row in cursor:
        if isinstance(row, dict):
            yield row


async def _archive(
    filename: str,
    metadata: dict[str, Any],
    *,
    policy: RetentionPolicy,
    db,
    actor_id: str | None,
    now: datetime,
) -> None:
    s = storage()
    if not s.exists(StorageBucket.DOCUMENT, filename):
        # Storage already gone — just mark the metadata so we don't keep
        # re-evaluating this row each sweep.
        metadata["archived_at"] = now.isoformat()
        metadata["archived_to_bucket"] = "missing"
        await write_document_metadata(filename, metadata, db=db)
        return

    blob = s.read_bytes(StorageBucket.DOCUMENT, filename)
    s.write_bytes(StorageBucket.ARCHIVE, filename, blob, content_type=metadata.get("content_type"))
    s.delete(StorageBucket.DOCUMENT, filename)

    metadata.update(
        {
            "archived_at": now.isoformat(),
            "archived_to_bucket": StorageBucket.ARCHIVE.value,
            "retention_policy_key": policy.key,
        }
    )
    await write_document_metadata(filename, metadata, db=db)

    await publish_document_event(
        name=EventName.DOCUMENT_ARCHIVED.value,
        payload={
            "event_version": 1,
            "document_id": str(metadata.get("document_id") or filename),
            "filename": filename,
            "archived_at": metadata["archived_at"],
            "archived_by_user_id": actor_id,
            "retention_policy_key": policy.key,
            "uploaded_employee_id": metadata.get("uploaded_employee_id"),
            "subject_employee_id": metadata.get("subject_employee_id"),
        },
        db=db,
        actor_id=actor_id,
    )


async def _permanent_delete(
    filename: str,
    metadata: dict[str, Any],
    *,
    db,
    actor_id: str | None,
) -> None:
    # File should already live in the archive bucket; clean it up and remove
    # the metadata. If the archived blob is missing we still drop the row so
    # the sweep terminates.
    try:
        storage().delete(StorageBucket.ARCHIVE, filename)
    except Exception:
        pass
    await delete_document_metadata(filename, db=db)

    await publish_document_event(
        name=EventName.DOCUMENT_DELETED.value,
        payload={
            "event_version": 1,
            "document_id": str(metadata.get("document_id") or filename),
            "filename": filename,
            "original_name": metadata.get("original_name"),
            "deleted_at": datetime.now(timezone.utc).isoformat(),
            "deleted_by_user_id": actor_id,
            "uploaded_employee_id": metadata.get("uploaded_employee_id"),
            "uploaded_employee_code": metadata.get("uploaded_employee_code"),
            "subject_employee_id": metadata.get("subject_employee_id"),
            "subject_employee_code": metadata.get("subject_employee_code"),
            "document_type": metadata.get("document_type"),
            "category": metadata.get("category"),
            "source_context": metadata.get("source_context"),
            "version_number": metadata.get("version_number") or 1,
            "is_current": bool(metadata.get("is_current", True)),
            "supersedes_document_id": metadata.get("supersedes_document_id"),
        },
        db=db,
        actor_id=actor_id,
    )


