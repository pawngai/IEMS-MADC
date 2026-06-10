from __future__ import annotations

from typing import Optional

from contexts.documents.application import service
from contexts.documents.application.commands import attach_document_to_entity
from app_platform.db.runtime import get_db_optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from contexts.rbac.contracts.operational import (
	can_manage_documents,
	require_document_delete_permission,
	require_legal_hold_authority,
)
from pydantic import BaseModel, Field
from app_platform.auth.current_user import get_current_user

documents_router = APIRouter(prefix="/documents", tags=["Documents"])


def _register_routes(router: APIRouter) -> None:
	@router.post("/photo", response_model=dict)
	async def upload_photo(
		file: UploadFile = File(...),
		current_user: dict = Depends(get_current_user),
	):
		return await service.upload_photo(file, current_user=current_user)

	@router.post("/signature", response_model=dict)
	async def upload_signature(
		file: UploadFile = File(...),
		current_user: dict = Depends(get_current_user),
	):
		return await service.upload_signature(file, current_user=current_user)

	@router.get("/photos/{filename}")
	async def get_photo(
		filename: str,
		db=Depends(get_db_optional),
		current_user: dict = Depends(get_current_user),
	):
		return await service.get_photo(filename, current_user=current_user, db=db)

	@router.get("/signatures/{filename}")
	async def get_signature(
		filename: str,
		db=Depends(get_db_optional),
		current_user: dict = Depends(get_current_user),
	):
		return await service.get_signature(filename, current_user=current_user, db=db)

	@router.delete("/photos/{filename}", response_model=dict)
	async def delete_photo(
		filename: str,
		current_user: dict = Depends(get_current_user),
	):
		require_document_delete_permission(current_user)
		return service.delete_photo(filename, current_user=current_user)

	@router.delete("/signatures/{filename}", response_model=dict)
	async def delete_signature(
		filename: str,
		current_user: dict = Depends(get_current_user),
	):
		require_document_delete_permission(current_user)
		return service.delete_signature(filename, current_user=current_user)

	@router.post("/document", response_model=dict)
	async def upload_document(
		file: UploadFile = File(...),
		entity_type: str | None = Query(default=None),
		entity_id: str | None = Query(default=None),
		document_type: str | None = Query(default=None),
		category: str | None = Query(default=None),
		source_context: str | None = Query(default=None),
		supersedes_document_id: str | None = Query(default=None),
		owner_employee_code: str | None = Query(default=None),
		expires_at: str | None = Query(default=None),
		db=Depends(get_db_optional),
		current_user: dict = Depends(get_current_user),
	):
		if owner_employee_code:
			caller_code = current_user.get("employee_code") or ""
			if owner_employee_code != caller_code and not can_manage_documents(current_user):
				raise HTTPException(
					status_code=403,
					detail="Only administrators or data-entry officers may attach documents to another employee.",
				)
		return await attach_document_to_entity(
			file=file,
			current_user=current_user,
			db=db,
			metadata={
				"entity_type": entity_type,
				"entity_id": entity_id,
				"document_type": document_type,
				"category": category,
				"source_context": source_context,
				"supersedes_document_id": supersedes_document_id,
				"subject_employee_code": owner_employee_code,
				"expires_at": expires_at,
			},
		)

	@router.get("/document", include_in_schema=False)
	async def upload_document_method_hint():
		raise HTTPException(status_code=405, detail="Use POST /api/documents/document")

	@router.get("/files/{filename}")
	async def get_document(filename: str, db=Depends(get_db_optional), current_user: dict = Depends(get_current_user)):
		return await service.get_document(filename, current_user=current_user, db=db)

	@router.get("/files/{filename}/download")
	async def download_document(
		filename: str, db=Depends(get_db_optional), current_user: dict = Depends(get_current_user)
	):
		return await service.download_document(filename, current_user=current_user, db=db)

	@router.get("/files")
	async def list_documents(
		query: Optional[str] = Query(default=None),
		uploader_query: str | None = Query(default=None),
		entity_type: str | None = Query(default=None),
		entity_id: str | None = Query(default=None),
		document_type: str | None = Query(default=None),
		category: str | None = Query(default=None),
		source_context: str | None = Query(default=None),
		is_locked: bool | None = Query(default=None),
		date_from: str | None = Query(default=None),
		date_to: str | None = Query(default=None),
		tags_any: list[str] | None = Query(default=None),
		tags_all: list[str] | None = Query(default=None),
		text_query: str | None = Query(default=None),
		limit: int = Query(default=50, ge=1, le=200),
		offset: int = Query(default=0, ge=0),
		db=Depends(get_db_optional),
		current_user: dict = Depends(get_current_user),
	):
		return await service.list_documents(
			current_user=current_user,
			query=query,
			uploader_query=uploader_query,
			entity_type=entity_type,
			entity_id=entity_id,
			document_type=document_type,
			category=category,
			source_context=source_context,
			is_locked=is_locked,
			date_from=date_from,
			date_to=date_to,
			tags_any=tags_any,
			tags_all=tags_all,
			text_query=text_query,
			limit=limit,
			offset=offset,
			db=db,
		)

	@router.get("/files/{filename}/metadata")
	async def get_document_metadata(
		filename: str,
		db=Depends(get_db_optional),
		current_user: dict = Depends(get_current_user),
	):
		return await service.get_document_metadata(filename, current_user=current_user, db=db)

	@router.get("/files/{filename}/thumbnail")
	async def get_document_thumbnail(
		filename: str,
		db=Depends(get_db_optional),
		current_user: dict = Depends(get_current_user),
	):
		from contexts.documents.infrastructure.access_control import require_document_access
		from contexts.documents.infrastructure.metadata_ops import read_document_metadata
		from contexts.documents.infrastructure.storage import StorageBucket as _Bucket
		from contexts.documents.infrastructure.storage_ops import storage as _storage

		await require_document_access(filename, current_user, db=db)
		metadata = await read_document_metadata(filename, db=db) or {}
		preview_name = str(metadata.get("preview_filename") or "")
		if not preview_name or not _storage().exists(_Bucket.PREVIEW, preview_name):
			raise HTTPException(status_code=404, detail="Preview not available for this document")
		media_type = str(metadata.get("content_type") or "image/jpeg")
		return _storage().inline_response(_Bucket.PREVIEW, preview_name, media_type=media_type)

	@router.get("/files/{filename}/versions")
	async def get_document_versions(
		filename: str,
		db=Depends(get_db_optional),
		current_user: dict = Depends(get_current_user),
	):
		from contexts.documents.infrastructure.access_control import require_document_access
		from contexts.documents.infrastructure.metadata_ops import (
			metadata_repository,
			read_document_metadata,
		)

		await require_document_access(filename, current_user, db=db)
		metadata = await read_document_metadata(filename, db=db) or {}
		document_id = str(metadata.get("document_id") or filename)
		chain = await metadata_repository(db=db).list_version_chain(document_id)
		return {
			"success": True,
			"document_id": document_id,
			"filename": filename,
			"versions": chain,
			"total": len(chain),
		}

	@router.get("/files/{filename}/audit")
	async def get_document_audit_timeline(
		filename: str,
		limit: int = Query(default=100, ge=1, le=500),
		db=Depends(get_db_optional),
		current_user: dict = Depends(get_current_user),
	):
		# Reuse the document-access gate so non-managers can only see their
		# own document's audit trail.
		from contexts.documents.infrastructure.access_control import require_document_access
		from contexts.documents.contracts.audit_timeline import list_audit_timeline_for_document

		await require_document_access(filename, current_user, db=db)
		entries = await list_audit_timeline_for_document(db=db, filename=filename, limit=limit)
		return {"success": True, "filename": filename, "items": entries, "total": len(entries)}

	@router.delete("/files/{filename}", response_model=dict)
	async def delete_document(
		filename: str,
		db=Depends(get_db_optional),
		current_user: dict = Depends(get_current_user),
	):
		require_document_delete_permission(current_user)
		return await service.delete_document(filename, current_user=current_user, db=db)

	class _SignerInput(BaseModel):
		employee_id: str = Field(min_length=1, max_length=64)
		role: str = Field(default="signer", max_length=64)

	class _SignatureRequestCreateBody(BaseModel):
		signers: list[_SignerInput] = Field(min_length=1, max_length=16)
		deadline_at: str | None = None

	class _SignBody(BaseModel):
		signature_filename: str | None = None

	class _DeclineBody(BaseModel):
		reason: str = Field(default="", max_length=500)

	@router.post("/files/{filename}/signature-requests", response_model=dict)
	async def create_signature_request(
		filename: str,
		body: _SignatureRequestCreateBody,
		db=Depends(get_db_optional),
		current_user: dict = Depends(get_current_user),
	):
		from contexts.documents.application.signature_service import (
			create_signature_request as _create,
		)
		return await _create(
			filename=filename,
			signers_input=[s.model_dump() for s in body.signers],
			deadline_at=body.deadline_at,
			current_user=current_user,
			db=db,
		)

	@router.post("/signature-requests/{request_id}/sign", response_model=dict)
	async def sign_signature_request(
		request_id: str,
		body: _SignBody,
		db=Depends(get_db_optional),
		current_user: dict = Depends(get_current_user),
	):
		from contexts.documents.application.signature_service import (
			sign_signature_request as _sign,
		)
		return await _sign(
			request_id=request_id,
			signature_filename=body.signature_filename,
			current_user=current_user,
			db=db,
		)

	@router.post("/signature-requests/{request_id}/decline", response_model=dict)
	async def decline_signature_request(
		request_id: str,
		body: _DeclineBody,
		db=Depends(get_db_optional),
		current_user: dict = Depends(get_current_user),
	):
		from contexts.documents.application.signature_service import (
			decline_signature_request as _decline,
		)
		return await _decline(
			request_id=request_id,
			reason=body.reason,
			current_user=current_user,
			db=db,
		)

	@router.delete("/signature-requests/{request_id}", response_model=dict)
	async def cancel_signature_request(
		request_id: str,
		db=Depends(get_db_optional),
		current_user: dict = Depends(get_current_user),
	):
		from contexts.documents.application.signature_service import (
			cancel_signature_request as _cancel,
		)
		return await _cancel(request_id=request_id, current_user=current_user, db=db)

	@router.get("/signature-requests/pending", response_model=dict)
	async def list_pending_signatures(
		db=Depends(get_db_optional),
		current_user: dict = Depends(get_current_user),
	):
		from contexts.documents.application.signature_service import (
			list_pending_for_current_user,
		)
		items = await list_pending_for_current_user(current_user=current_user, db=db)
		return {"success": True, "items": items, "total": len(items)}

	class _TemplateRenderBody(BaseModel):
		values: dict[str, str] = Field(default_factory=dict)
		entity_type: str | None = None
		entity_id: str | None = None
		owner_employee_code: str | None = None

	@router.post("/templates/{template_id}/render", response_model=dict)
	async def render_template(
		template_id: str,
		body: _TemplateRenderBody,
		db=Depends(get_db_optional),
		current_user: dict = Depends(get_current_user),
	):
		from contexts.documents.application.template_service import render_template as _render
		return await _render(
			template_id=template_id,
			values=body.values,
			current_user=current_user,
			db=db,
			entity_type=body.entity_type,
			entity_id=body.entity_id,
			subject_employee_code=body.owner_employee_code,
		)

	class _BulkDownloadBody(BaseModel):
		filenames: list[str] = Field(min_length=1, max_length=50)

	class _BulkTagBody(BaseModel):
		filenames: list[str] = Field(min_length=1, max_length=50)
		tags: list[str] = Field(min_length=1, max_length=16)

	@router.post("/files/bulk-download")
	async def bulk_download_documents(
		body: _BulkDownloadBody,
		db=Depends(get_db_optional),
		current_user: dict = Depends(get_current_user),
	):
		from contexts.documents.infrastructure.bulk_ops import stream_bulk_download_zip
		from fastapi.responses import StreamingResponse
		generator = stream_bulk_download_zip(
			filenames=body.filenames,
			current_user=current_user,
			db=db,
		)
		return StreamingResponse(
			generator,
			media_type="application/zip",
			headers={"Content-Disposition": 'attachment; filename="documents.zip"'},
		)

	@router.post("/files/bulk-tags", response_model=dict)
	async def bulk_apply_tags(
		body: _BulkTagBody,
		db=Depends(get_db_optional),
		current_user: dict = Depends(get_current_user),
	):
		from contexts.documents.infrastructure.bulk_ops import bulk_apply_tags as _apply
		return await _apply(
			filenames=body.filenames,
			tags=body.tags,
			current_user=current_user,
			db=db,
		)

	@router.delete("/files/bulk-tags", response_model=dict)
	async def bulk_remove_tags(
		body: _BulkTagBody,
		db=Depends(get_db_optional),
		current_user: dict = Depends(get_current_user),
	):
		from contexts.documents.infrastructure.bulk_ops import bulk_remove_tags as _remove
		return await _remove(
			filenames=body.filenames,
			tags=body.tags,
			current_user=current_user,
			db=db,
		)

	class _ShareCreateBody(BaseModel):
		ttl_seconds: int = Field(default=3600, ge=60, le=7 * 24 * 3600)

	@router.post("/files/{filename}/shares", response_model=dict)
	async def create_share_link(
		filename: str,
		body: _ShareCreateBody,
		db=Depends(get_db_optional),
		current_user: dict = Depends(get_current_user),
	):
		from contexts.documents.application.share_service import create_document_share_link
		return await create_document_share_link(
			filename=filename,
			ttl_seconds=body.ttl_seconds,
			current_user=current_user,
			db=db,
		)

	@router.delete("/files/{filename}/shares/{nonce}", response_model=dict)
	async def revoke_share_link(
		filename: str,
		nonce: str,
		db=Depends(get_db_optional),
		current_user: dict = Depends(get_current_user),
	):
		from contexts.documents.application.share_service import revoke_document_share_link
		return await revoke_document_share_link(
			filename=filename,
			nonce=nonce,
			current_user=current_user,
			db=db,
		)

	class _LegalHoldApplyBody(BaseModel):
		reason: str = Field(min_length=1, max_length=500)

	class _LegalHoldReleaseBody(BaseModel):
		release_reason: str | None = Field(default=None, max_length=500)

	@router.post("/files/{filename}/legal-hold", response_model=dict)
	async def apply_legal_hold(
		filename: str,
		body: _LegalHoldApplyBody,
		db=Depends(get_db_optional),
		current_user: dict = Depends(get_current_user),
	):
		require_legal_hold_authority(current_user)
		actor_id = str(current_user.get("sub") or current_user.get("id") or "") or None
		return await service.apply_legal_hold(
			filename,
			reason=body.reason,
			applied_by_user_id=actor_id,
			db=db,
		)

	@router.delete("/files/{filename}/legal-hold", response_model=dict)
	async def release_legal_hold(
		filename: str,
		body: _LegalHoldReleaseBody | None = None,
		db=Depends(get_db_optional),
		current_user: dict = Depends(get_current_user),
	):
		require_legal_hold_authority(current_user)
		actor_id = str(current_user.get("sub") or current_user.get("id") or "") or None
		release_reason = (body.release_reason if body else None)
		return await service.release_legal_hold(
			filename,
			released_by_user_id=actor_id,
			release_reason=release_reason,
			db=db,
		)


_register_routes(documents_router)


@documents_router.get("/shares/{token}")
async def consume_share_link(token: str, db=Depends(get_db_optional)):
	"""Unauthenticated inline view via a signed share token. Read-only —
	never serves a download, never serves an INFECTED or legal-hold blob."""
	from contexts.documents.application.share_service import resolve_share_token
	return await resolve_share_token(token=token, db=db)


__all__ = ["documents_router"]
