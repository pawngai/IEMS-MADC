"""Documents infrastructure — document locking operations."""
from __future__ import annotations

from datetime import datetime, timezone

from app_platform.event_bus.types import EventName
from contexts.documents.domain.validation import extract_filename_from_attachment, is_document_locked
from contexts.documents.infrastructure.event_publish import publish_document_event
from contexts.documents.infrastructure.metadata_ops import read_document_metadata, write_document_metadata
from contexts.documents.infrastructure.paths import DOCUMENT_DIR
from contexts.documents.infrastructure.storage_ops import (
	storage,
	_validate_safe_filename_http,
)
from contexts.documents.infrastructure.storage import StorageBucket
from fastapi import HTTPException


async def lock_documents_for_approved_request(
	attachments: list[dict], *, request_id: str, status: str, db=None,
	lock_reason: str = "APPROVED_CHANGE_REQUEST",
	allowed_statuses: set[str] | None = None,
	session=None,
) -> None:
	normalized_status = str(status or "").upper()
	valid_statuses = {
		str(item or "").upper() for item in (allowed_statuses or {"APPROVED", "APPLIED"})
	}
	if normalized_status not in valid_statuses:
		return

	now = datetime.now(timezone.utc).isoformat()
	for attachment in attachments or []:
		filename = extract_filename_from_attachment(attachment)
		if not filename:
			continue
		try:
			_validate_safe_filename_http(filename, DOCUMENT_DIR)
		except HTTPException:
			continue
		if not storage().exists(StorageBucket.DOCUMENT, filename):
			continue

		meta = await read_document_metadata(filename, db=db, session=session) or {}
		meta.update(
			{
				"document_id": str(meta.get("document_id") or filename),
				"filename": filename,
				"is_locked": True,
				"locked_at": now,
				"lock_reason": lock_reason,
				"locked_by_request_id": request_id,
				"locked_status": normalized_status,
			}
		)
		await write_document_metadata(filename, meta, db=db, session=session)
		await publish_document_event(
			name=EventName.DOCUMENT_LOCKED.value,
			payload={
				"event_version": 1,
				"document_id": str(meta.get("document_id") or filename),
				"filename": filename,
				"locked_at": now,
				"lock_reason": str(meta.get("lock_reason") or lock_reason),
				"locked_by_request_id": meta.get("locked_by_request_id"),
				"locked_status": meta.get("locked_status"),
				"uploaded_employee_id": meta.get("uploaded_employee_id"),
				"uploaded_employee_code": meta.get("uploaded_employee_code"),
				"subject_employee_id": meta.get("subject_employee_id"),
				"subject_employee_code": meta.get("subject_employee_code"),
				"document_type": meta.get("document_type"),
				"category": meta.get("category"),
				"source_context": meta.get("source_context"),
				"version_number": meta.get("version_number") or 1,
				"is_current": bool(meta.get("is_current", True)),
				"supersedes_document_id": meta.get("supersedes_document_id"),
			},
			db=db,
			session=session,
		)


async def apply_legal_hold(
	filename: str,
	*,
	reason: str,
	applied_by_user_id: str | None,
	db=None,
	session=None,
) -> dict:
	"""Mark a document as under legal hold. Idempotent — applying twice keeps
	the original ``legal_hold_applied_at`` timestamp so the audit trail isn't
	rewritten on re-apply."""
	normalized_reason = str(reason or "").strip()
	if not normalized_reason:
		raise HTTPException(
			status_code=422,
			detail={
				"error_code": "LEGAL_HOLD_REASON_REQUIRED",
				"message": "Legal hold reason must be a non-empty string",
			},
		)

	if not storage().exists(StorageBucket.DOCUMENT, filename):
		raise HTTPException(status_code=404, detail="Document not found")

	meta = await read_document_metadata(filename, db=db, session=session) or {}
	now = datetime.now(timezone.utc).isoformat()
	already_held = bool(meta.get("legal_hold"))
	meta.update(
		{
			"document_id": str(meta.get("document_id") or filename),
			"filename": filename,
			"legal_hold": True,
			"legal_hold_reason": normalized_reason,
			"legal_hold_applied_at": meta.get("legal_hold_applied_at") or now if already_held else now,
			"legal_hold_applied_by_user_id": meta.get("legal_hold_applied_by_user_id") or applied_by_user_id if already_held else applied_by_user_id,
		}
	)
	await write_document_metadata(filename, meta, db=db, session=session)

	if not already_held:
		await publish_document_event(
			name=EventName.DOCUMENT_LEGAL_HOLD_APPLIED.value,
			payload={
				"event_version": 1,
				"document_id": str(meta.get("document_id") or filename),
				"filename": filename,
				"applied_at": str(meta.get("legal_hold_applied_at") or now),
				"applied_by_user_id": applied_by_user_id,
				"legal_hold_reason": normalized_reason,
				"uploaded_employee_id": meta.get("uploaded_employee_id"),
				"uploaded_employee_code": meta.get("uploaded_employee_code"),
				"subject_employee_id": meta.get("subject_employee_id"),
				"subject_employee_code": meta.get("subject_employee_code"),
				"document_type": meta.get("document_type"),
				"category": meta.get("category"),
				"source_context": meta.get("source_context"),
			},
			db=db,
			actor_id=applied_by_user_id,
			session=session,
		)

	return {
		"success": True,
		"document_id": str(meta.get("document_id") or filename),
		"filename": filename,
		"legal_hold": True,
		"legal_hold_applied_at": meta.get("legal_hold_applied_at"),
		"legal_hold_reason": normalized_reason,
	}


async def release_legal_hold(
	filename: str,
	*,
	released_by_user_id: str | None,
	release_reason: str | None = None,
	db=None,
	session=None,
) -> dict:
	"""Lift a legal hold. Records the release timestamp and reason on the
	metadata for audit, then strips the hold-active fields."""
	if not storage().exists(StorageBucket.DOCUMENT, filename):
		raise HTTPException(status_code=404, detail="Document not found")

	meta = await read_document_metadata(filename, db=db, session=session) or {}
	if not meta.get("legal_hold"):
		return {
			"success": True,
			"document_id": str(meta.get("document_id") or filename),
			"filename": filename,
			"legal_hold": False,
			"already_released": True,
		}

	now = datetime.now(timezone.utc).isoformat()
	meta.update(
		{
			"document_id": str(meta.get("document_id") or filename),
			"filename": filename,
			"legal_hold": False,
			"legal_hold_released_at": now,
			"legal_hold_released_by_user_id": released_by_user_id,
			"legal_hold_release_reason": str(release_reason or "").strip() or None,
		}
	)
	await write_document_metadata(filename, meta, db=db, session=session)

	await publish_document_event(
		name=EventName.DOCUMENT_LEGAL_HOLD_RELEASED.value,
		payload={
			"event_version": 1,
			"document_id": str(meta.get("document_id") or filename),
			"filename": filename,
			"released_at": now,
			"released_by_user_id": released_by_user_id,
			"release_reason": str(release_reason or "").strip() or None,
			"uploaded_employee_id": meta.get("uploaded_employee_id"),
			"uploaded_employee_code": meta.get("uploaded_employee_code"),
			"subject_employee_id": meta.get("subject_employee_id"),
			"subject_employee_code": meta.get("subject_employee_code"),
		},
		db=db,
		actor_id=released_by_user_id,
		session=session,
	)

	return {
		"success": True,
		"document_id": str(meta.get("document_id") or filename),
		"filename": filename,
		"legal_hold": False,
		"legal_hold_released_at": now,
	}
