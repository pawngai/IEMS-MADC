"""Bulk document operations.

* ``stream_bulk_download_zip`` — yield a zip archive of multiple documents,
  re-checking the per-file access gate so the caller can't escalate by
  bundling someone else's docs into one request.
* ``bulk_apply_tags`` / ``bulk_remove_tags`` — atomic-per-doc tag mutations
  with the standard owner / manager gate.
"""
from __future__ import annotations

import io
import zipfile
from typing import AsyncIterator

from app_platform.event_bus.types import EventName
from contexts.documents.domain.validation import (
    is_document_owner,
    normalize_tags,
)
from contexts.documents.infrastructure.access_control import (
    can_manage_all_documents,
    get_user_id,
)
from contexts.documents.infrastructure.event_publish import publish_document_event
from contexts.documents.infrastructure.metadata_ops import (
    read_document_metadata,
    write_document_metadata,
)
from contexts.documents.infrastructure.storage import StorageBucket
from contexts.documents.infrastructure.storage_ops import storage
from fastapi import HTTPException


MAX_BULK_FILES = 50


async def stream_bulk_download_zip(
    *,
    filenames: list[str],
    current_user: dict,
    db,
) -> AsyncIterator[bytes]:
    """Stream a zip archive over the wire one file at a time. We build the
    archive in memory because Python's stdlib ``zipfile`` doesn't expose a
    chunked writer; for large files this is bounded by ``MAX_BULK_FILES``
    times the per-file size cap (10 MB) so a single request can't pin a
    pathological amount of memory."""
    if not filenames:
        raise HTTPException(status_code=400, detail="No filenames supplied")
    if len(filenames) > MAX_BULK_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Bulk download is limited to {MAX_BULK_FILES} files per request",
        )

    s = storage()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for filename in filenames:
            if not s.exists(StorageBucket.DOCUMENT, filename):
                continue
            metadata = await read_document_metadata(filename, db=db) or {}
            if not can_manage_all_documents(current_user) and not is_document_owner(metadata, current_user):
                # Skip silently so a partial-success path is possible — the
                # client knows what they asked for and can reconcile.
                continue
            if str(metadata.get("scan_status") or "").upper() == "INFECTED":
                continue
            label = str(metadata.get("original_name") or filename)
            zf.writestr(label, s.read_bytes(StorageBucket.DOCUMENT, filename))

    buf.seek(0)
    while chunk := buf.read(64 * 1024):
        yield chunk


async def bulk_apply_tags(
    *,
    filenames: list[str],
    tags: list[str],
    current_user: dict,
    db,
) -> dict:
    return await _bulk_mutate_tags(
        filenames=filenames,
        tags=tags,
        current_user=current_user,
        db=db,
        mode="add",
    )


async def bulk_remove_tags(
    *,
    filenames: list[str],
    tags: list[str],
    current_user: dict,
    db,
) -> dict:
    return await _bulk_mutate_tags(
        filenames=filenames,
        tags=tags,
        current_user=current_user,
        db=db,
        mode="remove",
    )


async def _bulk_mutate_tags(
    *,
    filenames: list[str],
    tags: list[str],
    current_user: dict,
    db,
    mode: str,
) -> dict:
    if not filenames:
        raise HTTPException(status_code=400, detail="No filenames supplied")
    if len(filenames) > MAX_BULK_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Bulk tag operations are limited to {MAX_BULK_FILES} files per request",
        )
    normalized = normalize_tags(tags) or []
    if not normalized:
        raise HTTPException(status_code=400, detail="No tags supplied")

    updated: list[str] = []
    skipped: list[str] = []
    s = storage()
    for filename in filenames:
        if not s.exists(StorageBucket.DOCUMENT, filename):
            skipped.append(filename)
            continue
        metadata = await read_document_metadata(filename, db=db) or {}
        if not can_manage_all_documents(current_user) and not is_document_owner(metadata, current_user):
            skipped.append(filename)
            continue
        existing = set(metadata.get("tags") or [])
        if mode == "add":
            new_tags = sorted(existing | set(normalized))
        else:
            new_tags = sorted(existing - set(normalized))
        if new_tags == sorted(existing):
            continue
        metadata["tags"] = new_tags
        await write_document_metadata(filename, metadata, db=db)
        updated.append(filename)

        await publish_document_event(
            name=EventName.DOCUMENT_METADATA_UPDATED.value,
            payload={
                "event_version": 1,
                "document_id": str(metadata.get("document_id") or filename),
                "filename": filename,
                "updated_at": "",
                "updated_by_user_id": get_user_id(current_user) or None,
                "uploaded_employee_id": metadata.get("uploaded_employee_id"),
                "uploaded_employee_code": metadata.get("uploaded_employee_code"),
                "subject_employee_id": metadata.get("subject_employee_id"),
                "subject_employee_code": metadata.get("subject_employee_code"),
                "entity_type": metadata.get("entity_type"),
                "entity_id": metadata.get("entity_id"),
                "document_type": metadata.get("document_type"),
                "category": metadata.get("category"),
                "source_context": metadata.get("source_context"),
                "version_number": int(metadata.get("version_number") or 1),
                "is_current": bool(metadata.get("is_current", True)),
                "supersedes_document_id": metadata.get("supersedes_document_id"),
                "updated_fields": ["tags"],
            },
            db=db,
            actor_id=get_user_id(current_user) or None,
        )

    return {"success": True, "updated": updated, "skipped": skipped, "tags": normalized}
