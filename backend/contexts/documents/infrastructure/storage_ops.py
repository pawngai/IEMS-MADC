"""Documents infrastructure — storage I/O operations (upload, serve, delete)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from app_platform.config.settings import settings
from contexts.documents.domain.validation import (
	ALLOWED_DOCUMENT_TYPES,
	ALLOWED_IMAGE_TYPES,
	MAX_DOCUMENT_SIZE,
	MAX_FILE_SIZE,
	content_type_for_document,
	content_type_for_image,
	extension_for_content_type,
	validate_document_content_type,
	validate_file_size,
	validate_image_content_type,
	validate_magic_bytes,
	validate_safe_filename,
)
from contexts.documents.infrastructure.storage import (
	DocumentStorage,
	GcsDocumentStorage,
	LocalDocumentStorage,
	ResilientDocumentStorage,
	StorageBucket,
)
from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse, Response


def _get_paths():
	"""Lazily read path constants so monkeypatching on the service facade works."""
	from contexts.documents.infrastructure import paths
	return paths


def _local_storage() -> LocalDocumentStorage:
	p = _get_paths()
	return LocalDocumentStorage(
		photo_dir=p.PHOTO_DIR,
		signature_dir=p.SIGNATURE_DIR,
		document_dir=p.DOCUMENT_DIR,
		archive_dir=getattr(p, "ARCHIVE_DIR", None),
		preview_dir=getattr(p, "PREVIEW_DIR", None),
	)


def storage() -> DocumentStorage:
	if settings.document_storage_backend == "gcs":
		if not settings.gcs_bucket_name and not settings.document_storage_local_fallback_enabled:
			raise RuntimeError("GCS_BUCKET_NAME is required when DOCUMENT_STORAGE_BACKEND=gcs")
		if not settings.gcs_bucket_name:
			return _local_storage()
		primary = GcsDocumentStorage(
			bucket_name=settings.gcs_bucket_name,
			project_id=settings.gcp_project_id,
		)
		if settings.document_storage_local_fallback_enabled:
			return ResilientDocumentStorage(primary=primary, fallback=_local_storage())
		return primary
	return _local_storage()


try:
	storage()
except Exception:
	pass


# ── Thin adapter wrappers (ValueError → HTTPException) ──────────────

def _validate_magic_bytes_http(contents: bytes, claimed_type: str) -> None:
	try:
		validate_magic_bytes(contents, claimed_type)
	except ValueError as exc:
		raise HTTPException(status_code=400, detail={"error_code": "FILE_CONTENT_MISMATCH", "message": str(exc)}) from exc


def _validate_safe_filename_http(filename: str, base_dir: Path) -> Path:
	try:
		return validate_safe_filename(filename, base_dir)
	except ValueError as exc:
		raise HTTPException(status_code=400, detail=str(exc)) from exc


def content_type_for_img(filename: str) -> str:
	return content_type_for_image(filename)


def content_type_for_doc(filename: str) -> str:
	return content_type_for_document(filename)


def _media_url(bucket: StorageBucket, filename: str) -> str:
	if bucket == StorageBucket.PHOTO:
		return f"/api/documents/photos/{filename}"
	if bucket == StorageBucket.SIGNATURE:
		return f"/api/documents/signatures/{filename}"
	return f"/api/documents/files/{filename}"


async def _require_media_access(
	bucket: StorageBucket,
	filename: str,
	*,
	current_user: dict | None,
	db=None,
) -> None:
	if current_user is None:
		return

	from contexts.rbac.application.access_control import has_active_authority
	from contexts.documents.infrastructure.access_control import can_manage_all_documents

	if can_manage_all_documents(current_user):
		return
	if has_active_authority(
		current_user,
		"HOD",
		"VERIFIER",
		"APPROVING_AUTHORITY",
		"AUDITOR",
		"DDO",
		"APPOINTING_AUTHORITY",
		"DISCIPLINARY_AUTHORITY",
	):
		return

	employee_id = str(current_user.get("employee_id") or "").strip()
	if not employee_id or db is None:
		raise HTTPException(status_code=403, detail="You can only access your own media")

	from contexts.employee_profile.contracts.media_directory import employee_owns_media

	field = "photo_url" if bucket == StorageBucket.PHOTO else "signature_url"
	if await employee_owns_media(
		db,
		employee_id=employee_id,
		field=field,
		expected_url=_media_url(bucket, filename),
		filename=filename,
	):
		return

	raise HTTPException(status_code=403, detail="You can only access your own media")


def _validate_image_file_type(file: UploadFile) -> None:
	try:
		validate_image_content_type(file.content_type)
	except ValueError as exc:
		raise HTTPException(
			status_code=400,
			detail={"error_code": "INVALID_FILE_TYPE", "message": str(exc), "allowed_types": list(ALLOWED_IMAGE_TYPES)},
		) from exc


def _validate_document_file_type(file: UploadFile) -> None:
	try:
		validate_document_content_type(file.content_type)
	except ValueError as exc:
		raise HTTPException(
			status_code=400,
			detail={"error_code": "INVALID_FILE_TYPE", "message": str(exc), "allowed_types": list(ALLOWED_DOCUMENT_TYPES)},
		) from exc


def _validate_file_size_http(file_size: int, max_size: int = MAX_FILE_SIZE) -> None:
	try:
		validate_file_size(file_size, max_size)
	except ValueError as exc:
		raise HTTPException(
			status_code=400,
			detail={"error_code": "FILE_TOO_LARGE", "message": str(exc), "max_size_mb": max_size / 1024 / 1024},
		) from exc


def make_unique_filename(file: UploadFile, *, default_ext: str) -> str:
	"""Derive the stored filename from the validated content_type, never from
	the uploader-supplied filename. Earlier upload steps (``_validate_image_file_type``
	/ ``_validate_document_file_type``) reject unknown MIME types, so the
	canonical extension is always available for accepted uploads. The
	``default_ext`` fallback is a defensive last resort for callers that bypass
	those checks."""
	canonical_ext = extension_for_content_type(file.content_type)
	file_ext = (canonical_ext or default_ext).strip().lower() or default_ext
	return f"{uuid.uuid4().hex}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.{file_ext}"


# ── Photo operations ────────────────────────────────────────────────

async def upload_photo(file: UploadFile, *, current_user: dict) -> dict:
	_validate_image_file_type(file)
	contents = await file.read()
	file_size = len(contents)
	_validate_file_size_http(file_size)
	_validate_magic_bytes_http(contents, file.content_type)

	unique_filename = make_unique_filename(file, default_ext="jpg")
	storage().write_bytes(StorageBucket.PHOTO, unique_filename, contents)

	photo_url = f"/api/documents/photos/{unique_filename}"
	return {
		"success": True,
		"message": "Photo uploaded successfully",
		"photo_url": photo_url,
		"filename": unique_filename,
		"file_size": file_size,
		"uploaded_by_user_id": current_user.get("sub", "unknown"),
		"uploaded_at": datetime.now(timezone.utc).isoformat(),
	}


async def upload_signature(file: UploadFile, *, current_user: dict) -> dict:
	_validate_image_file_type(file)
	contents = await file.read()
	file_size = len(contents)
	_validate_file_size_http(file_size)
	_validate_magic_bytes_http(contents, file.content_type)

	unique_filename = make_unique_filename(file, default_ext="png")
	storage().write_bytes(StorageBucket.SIGNATURE, unique_filename, contents)

	signature_url = f"/api/documents/signatures/{unique_filename}"
	return {
		"success": True,
		"message": "Signature uploaded successfully",
		"signature_url": signature_url,
		"filename": unique_filename,
		"file_size": file_size,
		"uploaded_by_user_id": current_user.get("sub", "unknown"),
		"uploaded_at": datetime.now(timezone.utc).isoformat(),
	}


async def get_photo(filename: str, *, current_user: dict | None = None, db=None) -> FileResponse:
	if not storage().exists(StorageBucket.PHOTO, filename):
		raise HTTPException(status_code=404, detail="Photo not found")
	await _require_media_access(
		StorageBucket.PHOTO,
		filename,
		current_user=current_user,
		db=db,
	)
	return storage().inline_response(
		StorageBucket.PHOTO,
		filename,
		media_type=content_type_for_img(filename),
	)


async def get_signature(filename: str, *, current_user: dict | None = None, db=None) -> FileResponse:
	if not storage().exists(StorageBucket.SIGNATURE, filename):
		raise HTTPException(status_code=404, detail="Signature not found")
	await _require_media_access(
		StorageBucket.SIGNATURE,
		filename,
		current_user=current_user,
		db=db,
	)
	return storage().inline_response(
		StorageBucket.SIGNATURE,
		filename,
		media_type=content_type_for_img(filename),
	)


def delete_photo(filename: str, *, current_user: dict) -> dict:
	if not storage().exists(StorageBucket.PHOTO, filename):
		raise HTTPException(status_code=404, detail="Photo not found")
	storage().delete(StorageBucket.PHOTO, filename)
	return {
		"success": True,
		"message": "Photo deleted successfully",
		"filename": filename,
		"deleted_by": current_user.get("sub", "unknown"),
		"deleted_at": datetime.now(timezone.utc).isoformat(),
	}


def delete_signature(filename: str, *, current_user: dict) -> dict:
	if not storage().exists(StorageBucket.SIGNATURE, filename):
		raise HTTPException(status_code=404, detail="Signature not found")
	storage().delete(StorageBucket.SIGNATURE, filename)
	return {
		"success": True,
		"message": "Signature deleted successfully",
		"filename": filename,
		"deleted_by": current_user.get("sub", "unknown"),
		"deleted_at": datetime.now(timezone.utc).isoformat(),
	}


# ── Document upload ─────────────────────────────────────────────────

async def upload_document(file: UploadFile, *, current_user: dict, db=None) -> dict:
	from contexts.documents.infrastructure.access_control import (
		get_employee_code,
		get_employee_id,
		get_user_id,
	)
	from contexts.documents.infrastructure.event_publish import publish_document_event
	from contexts.documents.infrastructure.malware_scanner import scanner
	from contexts.documents.infrastructure.metadata_ops import write_document_metadata
	from contexts.documents.domain.scanning import ScanStatus
	from app_platform.event_bus.types import EventName

	_validate_document_file_type(file)
	contents = await file.read()
	file_size = len(contents)
	try:
		validate_file_size(file_size, MAX_DOCUMENT_SIZE)
	except ValueError as exc:
		raise HTTPException(
			status_code=400,
			detail={"error_code": "FILE_TOO_LARGE", "message": str(exc), "max_size_mb": MAX_DOCUMENT_SIZE / 1024 / 1024},
		) from exc
	_validate_magic_bytes_http(contents, file.content_type)

	# Malware scan up-front. Infected files never touch the document bucket;
	# they are rejected at the API boundary with a structured error.
	scan_result = scanner().scan(contents, content_type=file.content_type)
	if scan_result.status == ScanStatus.INFECTED:
		raise HTTPException(
			status_code=400,
			detail={
				"error_code": "DOCUMENT_INFECTED",
				"message": "Upload rejected: malware scan detected a threat",
				"threat_name": scan_result.threat_name,
				"scanner_backend": scan_result.backend,
			},
		)

	unique_filename = make_unique_filename(file, default_ext="pdf")
	document_id = uuid.uuid4().hex
	storage().write_bytes(
		StorageBucket.DOCUMENT,
		unique_filename,
		contents,
		content_type=file.content_type,
	)

	# Best-effort preview generation. Failure here must not block the upload
	# — previews are a convenience, not a correctness requirement.
	preview_filename: str | None = None
	try:
		from contexts.documents.infrastructure.preview import preview_filename_for, preview_generator
		gen = preview_generator()
		if gen.can_generate(content_type=file.content_type):
			preview = gen.generate(content=contents, content_type=file.content_type)
			if preview is not None:
				preview_filename = preview_filename_for(unique_filename, suffix=preview.suffix)
				storage().write_bytes(
					StorageBucket.PREVIEW,
					preview_filename,
					preview.content,
					content_type=preview.media_type,
				)
	except Exception:
		preview_filename = None

	uploaded_at = datetime.now(timezone.utc).isoformat()
	try:
		await write_document_metadata(
			unique_filename,
			{
				"document_id": document_id,
				"filename": unique_filename,
				"original_name": file.filename or unique_filename,
				"uploaded_employee_id": get_employee_id(current_user),
				"uploaded_employee_code": get_employee_code(current_user),
				"uploaded_by_user_id": get_user_id(current_user),
				"uploaded_at": uploaded_at,
				"content_type": file.content_type,
				"file_size": file_size,
				"version_number": 1,
				"is_current": True,
				"scan_status": scan_result.status,
				"scan_completed_at": uploaded_at,
				"scan_threat_name": scan_result.threat_name,
				"preview_filename": preview_filename,
			},
			db=db,
		)
	except Exception:
		storage().delete(StorageBucket.DOCUMENT, unique_filename)
		raise

	await publish_document_event(
		name=EventName.DOCUMENT_SCAN_COMPLETED.value,
		payload={
			"event_version": 1,
			"document_id": document_id,
			"filename": unique_filename,
			"scanned_at": uploaded_at,
			"scan_status": scan_result.status,
			"scanner_backend": scan_result.backend,
			"threat_name": scan_result.threat_name,
		},
		db=db,
		actor_id=get_user_id(current_user) or None,
	)

	doc_url = f"/api/documents/files/{unique_filename}"
	return {
		"success": True,
		"message": "Document uploaded successfully",
		"url": doc_url,
		"document_id": document_id,
		"filename": unique_filename,
		"original_name": file.filename or unique_filename,
		"file_size": file_size,
		"content_type": file.content_type,
		"uploaded_by_user_id": current_user.get("sub", "unknown"),
		"uploaded_employee_id": get_employee_id(current_user) or None,
		"uploaded_employee_code": get_employee_code(current_user) or None,
		"uploaded_at": uploaded_at,
		"version_number": 1,
		"is_current": True,
	}


# ── Document get / download / delete ────────────────────────────────

async def _enforce_scan_gate(filename: str, *, db) -> None:
	"""Refuse to serve a document whose scan didn't complete CLEAN. Pending
	and ERROR statuses are blocked when ``DOCUMENT_SCANNER_BLOCK_ON_PENDING``
	is set (default in production); INFECTED is always blocked."""
	from contexts.documents.infrastructure.malware_scanner import block_on_pending
	from contexts.documents.infrastructure.metadata_ops import read_document_metadata
	from contexts.documents.domain.scanning import ScanStatus

	metadata = await read_document_metadata(filename, db=db) or {}
	status = str(metadata.get("scan_status") or "").upper()
	if status == ScanStatus.CLEAN or status == "":
		# Empty status covers legacy rows that pre-date scanning.
		return
	if status == ScanStatus.INFECTED:
		raise HTTPException(
			status_code=403,
			detail={
				"error_code": "DOCUMENT_INFECTED",
				"message": "This document is quarantined and cannot be served",
				"threat_name": metadata.get("scan_threat_name"),
			},
		)
	if status in {ScanStatus.PENDING, ScanStatus.ERROR} and block_on_pending():
		raise HTTPException(
			status_code=409,
			detail={
				"error_code": "DOCUMENT_SCAN_INCOMPLETE",
				"message": "Document is not yet cleared by malware scanning",
				"scan_status": status,
			},
		)


async def get_document(filename: str, *, current_user: dict, db=None) -> Response:
	if not storage().exists(StorageBucket.DOCUMENT, filename):
		raise HTTPException(status_code=404, detail="Document not found")
	from contexts.documents.infrastructure.access_control import require_document_access
	await require_document_access(filename, current_user, db=db)
	await _enforce_scan_gate(filename, db=db)
	return storage().inline_response(
		StorageBucket.DOCUMENT,
		filename,
		media_type=content_type_for_doc(filename),
	)


async def download_document(filename: str, *, current_user: dict, db=None) -> Response:
	if not storage().exists(StorageBucket.DOCUMENT, filename):
		raise HTTPException(status_code=404, detail="Document not found")
	from contexts.documents.infrastructure.access_control import require_document_access
	from contexts.documents.infrastructure.event_publish import publish_document_event
	from contexts.documents.infrastructure.metadata_ops import read_document_metadata
	from app_platform.event_bus.types import EventName

	await require_document_access(filename, current_user, db=db)
	await _enforce_scan_gate(filename, db=db)

	# Emit a DOCUMENT_ACCESSED event for downloads. Inline views are
	# intentionally excluded to keep the audit timeline focused on actions
	# that exfiltrate a full copy.
	metadata = await read_document_metadata(filename, db=db) or {}
	await publish_document_event(
		name=EventName.DOCUMENT_ACCESSED.value,
		payload={
			"event_version": 1,
			"document_id": str(metadata.get("document_id") or filename),
			"filename": filename,
			"accessed_at": datetime.now(timezone.utc).isoformat(),
			"accessed_by_user_id": current_user.get("sub") or current_user.get("id"),
			"access_mode": "download",
			"uploaded_employee_id": metadata.get("uploaded_employee_id"),
			"subject_employee_id": metadata.get("subject_employee_id"),
		},
		db=db,
		actor_id=str(current_user.get("sub") or current_user.get("id") or "") or None,
	)

	return storage().download_response(
		StorageBucket.DOCUMENT,
		filename,
		media_type="application/octet-stream",
	)


async def get_subject_document(
	filename: str,
	*,
	employee_id: str,
	employee_code: str | None = None,
	db=None,
) -> Response:
	if not storage().exists(StorageBucket.DOCUMENT, filename):
		raise HTTPException(status_code=404, detail="Document not found")
	from contexts.documents.infrastructure.access_control import require_subject_document_access
	await require_subject_document_access(
		filename,
		employee_id=employee_id,
		employee_code=employee_code,
		db=db,
	)
	return storage().inline_response(
		StorageBucket.DOCUMENT,
		filename,
		media_type=content_type_for_doc(filename),
	)


async def download_subject_document(
	filename: str,
	*,
	employee_id: str,
	employee_code: str | None = None,
	db=None,
) -> Response:
	if not storage().exists(StorageBucket.DOCUMENT, filename):
		raise HTTPException(status_code=404, detail="Document not found")
	from contexts.documents.infrastructure.access_control import require_subject_document_access
	await require_subject_document_access(
		filename,
		employee_id=employee_id,
		employee_code=employee_code,
		db=db,
	)
	return storage().download_response(
		StorageBucket.DOCUMENT,
		filename,
		media_type="application/octet-stream",
	)


async def delete_document(filename: str, *, current_user: dict, db=None) -> dict:
	from contexts.documents.infrastructure.access_control import get_department_id, get_user_id
	from contexts.documents.infrastructure.event_publish import publish_document_event
	from contexts.documents.infrastructure.metadata_ops import (
		delete_document_metadata,
		metadata_repository,
		read_document_metadata,
	)
	from contexts.documents.domain.validation import (
		extract_filename_from_attachment,
		is_document_locked,
		is_legal_hold_active,
	)
	from app_platform.event_bus.types import EventName

	if not storage().exists(StorageBucket.DOCUMENT, filename):
		raise HTTPException(status_code=404, detail="Document not found")

	metadata = await read_document_metadata(filename, db=db)
	if is_legal_hold_active(metadata):
		meta = metadata or {}
		raise HTTPException(
			status_code=400,
			detail={
				"error_code": "DOCUMENT_LEGAL_HOLD",
				"message": "Documents under legal hold cannot be deleted",
				"document_id": str(meta.get("document_id") or filename),
				"filename": filename,
				"legal_hold_reason": meta.get("legal_hold_reason"),
			},
		)
	if is_document_locked(metadata):
		meta = metadata or {}
		raise HTTPException(
			status_code=400,
			detail={
				"error_code": "DOCUMENT_LOCKED",
				"message": "Locked documents are immutable and cannot be deleted",
				"document_id": str(meta.get("document_id") or filename),
				"filename": filename,
				"lock_reason": meta.get("lock_reason"),
				"locked_by_request_id": meta.get("locked_by_request_id"),
				"locked_status": meta.get("locked_status"),
			},
		)
	if metadata and await metadata_repository(db=db).has_successor(str(metadata.get("document_id") or filename)):
		raise HTTPException(
			status_code=409,
			detail={
				"error_code": "DOCUMENT_VERSION_HISTORY_PROTECTED",
				"message": "Documents that have been superseded by a newer version cannot be deleted",
				"document_id": str(metadata.get("document_id") or filename),
				"filename": filename,
			},
		)

	deleted_at = datetime.now(timezone.utc).isoformat()
	storage().delete(StorageBucket.DOCUMENT, filename)
	await delete_document_metadata(filename, db=db)
	await publish_document_event(
		name=EventName.DOCUMENT_DELETED.value,
		payload={
			"event_version": 1,
			"document_id": str((metadata or {}).get("document_id") or filename),
			"filename": filename,
			"original_name": (metadata or {}).get("original_name"),
			"deleted_at": deleted_at,
			"deleted_by_user_id": get_user_id(current_user) or None,
			"uploaded_employee_id": (metadata or {}).get("uploaded_employee_id"),
			"uploaded_employee_code": (metadata or {}).get("uploaded_employee_code"),
			"subject_employee_id": (metadata or {}).get("subject_employee_id"),
			"subject_employee_code": (metadata or {}).get("subject_employee_code"),
			"document_type": (metadata or {}).get("document_type"),
			"category": (metadata or {}).get("category"),
			"source_context": (metadata or {}).get("source_context"),
			"version_number": (metadata or {}).get("version_number") or 1,
			"is_current": bool((metadata or {}).get("is_current", True)),
			"supersedes_document_id": (metadata or {}).get("supersedes_document_id"),
		},
		db=db,
		actor_id=get_user_id(current_user) or None,
		department_id=get_department_id(current_user) or None,
	)
	return {
		"success": True,
		"message": "Document deleted successfully",
		"filename": filename,
		"deleted_by": current_user.get("sub", "unknown"),
		"deleted_at": deleted_at,
	}
