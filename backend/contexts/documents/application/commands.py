"""Documents application — command handlers (orchestration layer)."""
from __future__ import annotations

from typing import Any

from app_platform.event_bus.types import EventName
from contexts.documents.domain.metadata_rules import validate_document_metadata
from contexts.employee_master.contracts.identity_directory import resolve_identity_ref
from fastapi import HTTPException, UploadFile


def _error_detail(*, error_code: str, message: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
	detail: dict[str, Any] = {"error_code": error_code, "message": message}
	if extra:
		detail.update(extra)
	return detail


def _validate_metadata_http(metadata: dict[str, Any] | None) -> dict[str, Any]:
	"""Adapt domain ValueError to HTTPException for API callers."""
	try:
		return validate_document_metadata(metadata)
	except ValueError as exc:
		msg = str(exc)
		raw = dict(metadata or {})
		# Derive structured error code from the domain error message
		if "service-history truth" in msg:
			code = "DOCUMENT_METADATA_TRUTH_FORBIDDEN"
			extra: dict[str, Any] = {}
		elif "entity_id is required" in msg:
			code = "DOCUMENT_ENTITY_ID_REQUIRED"
			extra = {"entity_type": raw.get("entity_type")}
		elif "entity_type is required" in msg:
			code = "DOCUMENT_ENTITY_TYPE_REQUIRED"
			extra = {"entity_id": raw.get("entity_id")}
		elif "entity_type" in msg:
			code = "DOCUMENT_ENTITY_TYPE_INVALID"
			extra = {"entity_type": raw.get("entity_type")}
		elif "document_type" in msg:
			code = "DOCUMENT_TYPE_INVALID"
			extra = {"document_type": raw.get("document_type")}
		elif "source_context" in msg:
			code = "DOCUMENT_SOURCE_CONTEXT_INVALID"
			extra = {"source_context": raw.get("source_context")}
		elif "category" in msg:
			code = "DOCUMENT_CATEGORY_INVALID"
			extra = {"category": raw.get("category")}
		else:
			code = "DOCUMENT_METADATA_INVALID"
			extra = {}
		raise HTTPException(status_code=422, detail=_error_detail(error_code=code, message=msg, extra=extra)) from exc


async def _resolve_subject_employee(metadata: dict[str, Any], *, db=None) -> dict[str, str]:
	subject_employee_code = str(metadata.get("subject_employee_code") or "").strip()
	if not subject_employee_code or db is None:
		return {}

	identity = await resolve_identity_ref(
		db,
		ref=subject_employee_code,
		projection={"_id": 0, "employee_id": 1, "employee_code": 1},
	)
	subject_employee_id = str((identity or {}).get("employee_id") or "").strip()
	if not subject_employee_id:
		raise HTTPException(
			status_code=422,
			detail=_error_detail(
				error_code="DOCUMENT_SUBJECT_EMPLOYEE_INVALID",
				message="subject_employee_code does not reference an existing employee identity",
				extra={"subject_employee_code": subject_employee_code},
			),
		)

	resolved_code = str((identity or {}).get("employee_code") or subject_employee_code).strip()
	return {
		"subject_employee_id": subject_employee_id,
		"subject_employee_code": resolved_code or subject_employee_code,
	}


async def _validate_entity_access(
	entity_type: str | None,
	entity_id: str | None,
	*,
	current_user: dict,
	db=None,
) -> None:
	"""Validate the caller has access to the entity they are attaching to."""
	if not entity_type or not entity_id or db is None:
		return

	from contexts.documents.infrastructure.access_control import can_manage_all_documents
	if can_manage_all_documents(current_user):
		return

	caller_employee_id = str(current_user.get("employee_id") or "").strip()
	if not caller_employee_id:
		raise HTTPException(status_code=403, detail=_error_detail(
			error_code="DOCUMENT_ENTITY_ACCESS_DENIED",
			message="Only document managers or the owning employee may attach documents to this entity",
			extra={"entity_type": entity_type, "entity_id": entity_id},
		))

	# For entity types that map to specific contexts, verify the entity exists
	# and the caller has a relationship to it.  Use cross-context contract
	# facades — never access foreign collections directly.
	normalized = entity_type.upper()
	if normalized == "CHANGE_REQUEST":
		from contexts.change_requests.contracts.change_request_directory import get_change_request_by_id
		request_doc = await get_change_request_by_id(
			db,
			request_id=entity_id,
			projection={"_id": 0, "employee_id": 1, "request_id": 1},
		)
		if not request_doc:
			raise HTTPException(status_code=404, detail=_error_detail(
				error_code="DOCUMENT_ENTITY_NOT_FOUND",
				message=f"Entity {entity_type}/{entity_id} not found",
				extra={"entity_type": entity_type, "entity_id": entity_id},
			))
		if str(request_doc.get("employee_id") or "").strip() != caller_employee_id:
			raise HTTPException(status_code=403, detail=_error_detail(
				error_code="DOCUMENT_ENTITY_ACCESS_DENIED",
				message="You can only attach documents to your own change requests",
				extra={"entity_type": entity_type, "entity_id": entity_id},
			))
	elif normalized == "LEAVE":
		from contexts.leave.contracts.leave_directory import get_leave_application_by_id
		leave_doc = await get_leave_application_by_id(db, leave_id=entity_id)
		if not leave_doc:
			raise HTTPException(status_code=404, detail=_error_detail(
				error_code="DOCUMENT_ENTITY_NOT_FOUND",
				message=f"Entity {entity_type}/{entity_id} not found",
				extra={"entity_type": entity_type, "entity_id": entity_id},
			))
		if str(leave_doc.get("employee_id") or "").strip() != caller_employee_id:
			raise HTTPException(status_code=403, detail=_error_detail(
				error_code="DOCUMENT_ENTITY_ACCESS_DENIED",
				message="You can only attach documents to your own leave applications",
				extra={"entity_type": entity_type, "entity_id": entity_id},
			))
	# SERVICE_EVENT, SERVICE_BOOK, MASTER_DATA — existence-check only for known types.
	# For unknown types, skip (open-world).


async def attach_document_to_entity(
	*,
	file: UploadFile,
	current_user: dict,
	metadata: dict[str, Any] | None = None,
	db=None,
) -> dict[str, Any]:
	from contexts.documents.infrastructure.event_publish import publish_document_event
	from contexts.documents.infrastructure.metadata_ops import (
		delete_document_metadata,
		read_document_metadata,
		read_document_metadata_by_document_id,
		write_document_metadata,
	)
	from contexts.documents.infrastructure.storage import StorageBucket
	from contexts.documents.infrastructure.storage_ops import storage, upload_document
	from contexts.documents.domain.validation import is_document_locked, is_legal_hold_active

	validated = _validate_metadata_http(metadata)
	validated.update(await _resolve_subject_employee(validated, db=db))

	# Entity-level authorization
	await _validate_entity_access(
		validated.get("entity_type"),
		validated.get("entity_id"),
		current_user=current_user,
		db=db,
	)

	# --- Pre-upload supersede validation ---
	superseded_metadata: dict[str, Any] | None = None
	superseded_filename: str | None = None
	supersedes_document_id = str(validated.get("supersedes_document_id") or "").strip()
	if supersedes_document_id:
		superseded_metadata = await read_document_metadata_by_document_id(
			supersedes_document_id, db=db,
		)
		if superseded_metadata is None:
			raise HTTPException(
				status_code=404,
				detail=_error_detail(
					error_code="DOCUMENT_SUPERSEDE_NOT_FOUND",
					message="supersedes_document_id does not reference an existing document",
					extra={"supersedes_document_id": supersedes_document_id},
				),
			)
		if is_legal_hold_active(superseded_metadata):
			raise HTTPException(
				status_code=409,
				detail=_error_detail(
					error_code="DOCUMENT_SUPERSEDE_LEGAL_HOLD",
					message="Documents under legal hold cannot be superseded",
					extra={"supersedes_document_id": supersedes_document_id},
				),
			)
		if is_document_locked(superseded_metadata):
			raise HTTPException(
				status_code=409,
				detail=_error_detail(
					error_code="DOCUMENT_SUPERSEDE_LOCKED",
					message="Locked documents cannot be superseded",
					extra={"supersedes_document_id": supersedes_document_id},
				),
			)
		superseded_filename = str(superseded_metadata.get("filename") or "").strip() or None
		validated["supersedes_document_id"] = supersedes_document_id
		validated["version_number"] = int(superseded_metadata.get("version_number") or 1) + 1
		validated["is_current"] = True

	uploaded = await upload_document(file, current_user=current_user, db=db)
	actor_id = str(current_user.get("sub") or current_user.get("id") or "") or None
	department_id = str(current_user.get("department_code") or current_user.get("department_id") or "") or None

	filename = uploaded.get("filename")
	merged_metadata: dict[str, Any] | None = None
	if filename:
		superseded_before_update = dict(superseded_metadata) if superseded_metadata else None
		try:
			existing = await read_document_metadata(filename, db=db) or {}
			existing_before_update = dict(existing)
			existing.update(validated)
			await write_document_metadata(filename, existing, db=db)

			if superseded_metadata and superseded_filename:
				superseded_metadata["is_current"] = False
				await write_document_metadata(superseded_filename, superseded_metadata, db=db)
				await publish_document_event(
					name=EventName.DOCUMENT_METADATA_UPDATED.value,
					payload={
						"event_version": 1,
						"document_id": str(superseded_metadata.get("document_id") or superseded_filename),
						"filename": superseded_filename,
						"updated_at": str(existing.get("uploaded_at") or uploaded.get("uploaded_at") or ""),
						"updated_by_user_id": existing.get("uploaded_by_user_id") or actor_id,
						"uploaded_employee_id": superseded_metadata.get("uploaded_employee_id"),
						"uploaded_employee_code": superseded_metadata.get("uploaded_employee_code"),
						"subject_employee_id": superseded_metadata.get("subject_employee_id"),
						"subject_employee_code": superseded_metadata.get("subject_employee_code"),
						"entity_type": superseded_metadata.get("entity_type"),
						"entity_id": superseded_metadata.get("entity_id"),
						"document_type": superseded_metadata.get("document_type"),
						"category": superseded_metadata.get("category"),
						"source_context": superseded_metadata.get("source_context"),
						"version_number": superseded_metadata.get("version_number") or 1,
						"is_current": False,
						"supersedes_document_id": superseded_metadata.get("supersedes_document_id"),
						"updated_fields": ["is_current"],
					},
					db=db,
					actor_id=actor_id,
					department_id=department_id,
				)

			merged_metadata = existing
			changed_fields = sorted(
				key
				for key, value in validated.items()
				if existing_before_update.get(key) != value
			)
			if changed_fields:
				await publish_document_event(
					name=EventName.DOCUMENT_METADATA_UPDATED.value,
					payload={
						"event_version": 1,
						"document_id": str(existing.get("document_id") or filename),
						"filename": filename,
						"updated_at": str(existing.get("uploaded_at") or uploaded.get("uploaded_at") or ""),
						"updated_by_user_id": existing.get("uploaded_by_user_id") or actor_id,
						"uploaded_employee_id": existing.get("uploaded_employee_id"),
						"uploaded_employee_code": existing.get("uploaded_employee_code"),
						"subject_employee_id": existing.get("subject_employee_id"),
						"subject_employee_code": existing.get("subject_employee_code"),
						"entity_type": existing.get("entity_type"),
						"entity_id": existing.get("entity_id"),
						"document_type": existing.get("document_type"),
						"category": existing.get("category"),
						"source_context": existing.get("source_context"),
						"version_number": existing.get("version_number") or 1,
						"is_current": bool(existing.get("is_current", True)),
						"supersedes_document_id": existing.get("supersedes_document_id"),
						"updated_fields": changed_fields,
					},
					db=db,
					actor_id=actor_id,
					department_id=department_id,
				)

			await publish_document_event(
				name=EventName.DOCUMENT_UPLOADED.value,
				payload={
					"event_version": 1,
					"document_id": str(existing.get("document_id") or filename),
					"filename": filename,
					"original_name": str(existing.get("original_name") or uploaded.get("original_name") or filename),
					"content_type": str(existing.get("content_type") or uploaded.get("content_type") or "application/octet-stream"),
					"file_size": int(existing.get("file_size") or uploaded.get("file_size") or 0),
					"uploaded_at": str(existing.get("uploaded_at") or uploaded.get("uploaded_at") or ""),
					"uploaded_by_user_id": existing.get("uploaded_by_user_id"),
					"uploaded_employee_id": existing.get("uploaded_employee_id"),
					"uploaded_employee_code": existing.get("uploaded_employee_code"),
					"subject_employee_id": existing.get("subject_employee_id"),
					"subject_employee_code": existing.get("subject_employee_code"),
					"entity_type": existing.get("entity_type"),
					"entity_id": existing.get("entity_id"),
					"document_type": existing.get("document_type"),
					"category": existing.get("category"),
					"source_context": existing.get("source_context"),
					"version_number": existing.get("version_number") or 1,
					"is_current": bool(existing.get("is_current", True)),
					"supersedes_document_id": existing.get("supersedes_document_id"),
				},
				db=db,
				actor_id=actor_id,
				department_id=department_id,
			)
		except Exception:
			storage().delete(StorageBucket.DOCUMENT, filename)
			await delete_document_metadata(filename, db=db)
			if superseded_before_update and superseded_filename:
				await write_document_metadata(superseded_filename, superseded_before_update, db=db)
			raise

	return {
		**uploaded,
		"metadata": merged_metadata or validated,
		"documents_are_not_service_history_truth": True,
	}
