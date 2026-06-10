"""Documents infrastructure — metadata CRUD wrappers."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from contexts.documents.repository import DocumentMetadataRepository


def metadata_repository(*, db=None, metadata_dir: Path | None = None) -> DocumentMetadataRepository:
	if metadata_dir is None:
		from contexts.documents.infrastructure import paths
		metadata_dir = paths.DOCUMENT_META_DIR
	return DocumentMetadataRepository(db=db, metadata_dir=metadata_dir)


async def write_document_metadata(filename: str, metadata: dict, *, db=None, session=None) -> None:
	await metadata_repository(db=db).upsert(filename, metadata, session=session)


async def read_document_metadata(filename: str, *, db=None, session=None) -> dict | None:
	return await metadata_repository(db=db).get(filename, session=session)


async def read_document_metadata_by_document_id(document_id: str, *, db=None, session=None) -> dict | None:
	return await metadata_repository(db=db).get_by_document_id(document_id, session=session)


async def delete_document_metadata(filename: str, *, db=None, session=None) -> None:
	await metadata_repository(db=db).delete(filename, session=session)


async def file_metadata(filename: str, *, db=None, metadata: dict | None = None) -> dict:
	from contexts.documents.infrastructure.storage_ops import storage, content_type_for_doc
	from contexts.documents.infrastructure.storage import StorageBucket
	from contexts.documents.domain.validation import is_document_locked, is_legal_hold_active

	stat = storage().stat(StorageBucket.DOCUMENT, filename)
	meta = metadata if metadata is not None else (await read_document_metadata(filename, db=db) or {})
	return {
		"document_id": str(meta.get("document_id") or filename),
		"filename": filename,
		"url": f"/api/documents/files/{filename}",
		"file_size": meta.get("file_size") or stat.size,
		"content_type": content_type_for_doc(filename),
		"uploaded_at": str(meta.get("uploaded_at") or stat.modified_at.isoformat()),
		"original_name": meta.get("original_name") or filename,
		"uploaded_employee_id": meta.get("uploaded_employee_id"),
		"uploaded_employee_code": meta.get("uploaded_employee_code"),
		"subject_employee_id": meta.get("subject_employee_id"),
		"subject_employee_code": meta.get("subject_employee_code"),
		"entity_type": meta.get("entity_type"),
		"entity_id": meta.get("entity_id"),
		"document_type": meta.get("document_type"),
		"category": meta.get("category"),
		"source_context": meta.get("source_context"),
		"is_locked": is_document_locked(meta),
		"locked_at": meta.get("locked_at"),
		"lock_reason": meta.get("lock_reason"),
		"locked_by_request_id": meta.get("locked_by_request_id"),
		"legal_hold": is_legal_hold_active(meta),
		"legal_hold_reason": meta.get("legal_hold_reason"),
		"legal_hold_applied_at": meta.get("legal_hold_applied_at"),
		"scan_status": meta.get("scan_status"),
		"archived_at": meta.get("archived_at"),
		"tags": list(meta.get("tags") or []),
		"preview_filename": meta.get("preview_filename"),
		"preview_url": (
			f"/api/documents/files/{filename}/thumbnail"
			if meta.get("preview_filename")
			else None
		),
		"expires_at": meta.get("expires_at"),
		"version_number": int(meta.get("version_number") or 1),
		"is_current": bool(meta.get("is_current", True)),
		"supersedes_document_id": meta.get("supersedes_document_id"),
	}
