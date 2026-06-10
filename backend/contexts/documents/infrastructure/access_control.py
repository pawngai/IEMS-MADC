"""Documents infrastructure — access control helpers."""
from __future__ import annotations

from contexts.identity_access.contracts.operational import can_manage_documents
from fastapi import HTTPException


def get_user_id(current_user: dict) -> str:
	return str(current_user.get("sub") or current_user.get("id") or "")


def get_employee_id(current_user: dict) -> str:
	return str(current_user.get("employee_id") or "")


def get_employee_code(current_user: dict) -> str:
	return str(current_user.get("employee_code") or "")


def get_department_id(current_user: dict) -> str:
	return str(current_user.get("department_code") or current_user.get("department_id") or "")


def can_manage_all_documents(current_user: dict) -> bool:
	return can_manage_documents(current_user)


def is_subject_document_owner(
	metadata: dict | None,
	*,
	employee_id: str | None,
	employee_code: str | None,
) -> bool:
	meta = metadata or {}
	normalized_employee_id = str(employee_id or "").strip()
	normalized_employee_code = str(employee_code or "").strip()
	if normalized_employee_id and str(meta.get("subject_employee_id") or "").strip() == normalized_employee_id:
		return True
	if normalized_employee_code and str(meta.get("subject_employee_code") or "").strip() == normalized_employee_code:
		return True
	return False


async def require_document_access(filename: str, current_user: dict, *, db=None) -> None:
	from contexts.documents.infrastructure.metadata_ops import read_document_metadata
	from contexts.documents.domain.validation import is_document_owner

	if can_manage_all_documents(current_user):
		return
	metadata = await read_document_metadata(filename, db=db)
	if not is_document_owner(metadata, current_user):
		raise HTTPException(status_code=403, detail="You can only access your own documents")


async def require_subject_document_access(
	filename: str,
	*,
	employee_id: str | None,
	employee_code: str | None,
	db=None,
) -> dict:
	from contexts.documents.infrastructure.metadata_ops import read_document_metadata

	metadata = await read_document_metadata(filename, db=db)
	if not is_subject_document_owner(
		metadata,
		employee_id=employee_id,
		employee_code=employee_code,
	):
		raise HTTPException(status_code=403, detail="You can only access documents about yourself")
	return metadata or {}
