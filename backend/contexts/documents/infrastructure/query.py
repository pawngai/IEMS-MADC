"""Documents infrastructure — list, filter, and metadata query operations."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from contexts.documents.domain.validation import (
	normalize_document_category,
	normalize_document_entity_type,
	normalize_document_source_context,
	normalize_document_type,
)
from contexts.documents.infrastructure.access_control import (
	can_manage_all_documents,
	get_employee_code,
	get_employee_id,
	get_user_id,
	is_subject_document_owner,
	require_document_access,
)
from contexts.documents.infrastructure.metadata_ops import (
	file_metadata,
	metadata_repository,
	read_document_metadata,
)
from contexts.documents.infrastructure.storage_ops import storage, content_type_for_doc
from contexts.documents.infrastructure.storage import StorageBucket
from fastapi import HTTPException


def _require_in_memory_listing_allowed() -> None:
	"""Block the storage-walk fallback in production. The repository's Mongo
	path is the only supported list source there; if the caller arrives with
	``db is None`` it indicates a misconfigured wiring, not a normal mode."""
	from app_platform.config.settings import settings as _settings

	if _settings.is_production and not _settings.allow_document_in_memory_listing:
		raise HTTPException(
			status_code=503,
			detail={
				"error_code": "DOCUMENT_LISTING_UNAVAILABLE",
				"message": "Document listing requires a database connection",
			},
		)


def _document_filter_error(*, error_code: str, message: str, extra: dict | None = None) -> dict:
	detail = {
		"error_code": error_code,
		"message": message,
	}
	if extra:
		detail.update(extra)
	return detail


def _normalize_document_list_filters(
	*,
	entity_type: str | None,
	entity_id: str | None,
	document_type: str | None,
	category: str | None,
	source_context: str | None,
) -> tuple[str | None, str | None, str | None, str | None, str | None]:
	try:
		normalized_entity_type = normalize_document_entity_type(entity_type)
	except ValueError as exc:
		raise HTTPException(
			status_code=422,
			detail=_document_filter_error(
				error_code="DOCUMENT_ENTITY_TYPE_INVALID",
				message=str(exc),
				extra={"entity_type": entity_type},
			),
		) from exc

	normalized_entity_id = str(entity_id or "").strip() or None
	if normalized_entity_type and not normalized_entity_id:
		raise HTTPException(
			status_code=422,
			detail=_document_filter_error(
				error_code="DOCUMENT_ENTITY_ID_REQUIRED",
				message="entity_id is required when entity_type is provided",
				extra={"entity_type": normalized_entity_type},
			),
		)
	if normalized_entity_id and not normalized_entity_type:
		raise HTTPException(
			status_code=422,
			detail=_document_filter_error(
				error_code="DOCUMENT_ENTITY_TYPE_REQUIRED",
				message="entity_type is required when entity_id is provided",
				extra={"entity_id": normalized_entity_id},
			),
		)

	try:
		normalized_document_type = normalize_document_type(document_type)
	except ValueError as exc:
		raise HTTPException(
			status_code=422,
			detail=_document_filter_error(
				error_code="DOCUMENT_TYPE_INVALID",
				message=str(exc),
				extra={"document_type": document_type},
			),
		) from exc

	try:
		normalized_category = normalize_document_category(category)
	except ValueError as exc:
		raise HTTPException(
			status_code=422,
			detail=_document_filter_error(
				error_code="DOCUMENT_CATEGORY_INVALID",
				message=str(exc),
				extra={"category": category},
			),
		) from exc

	try:
		normalized_source_context = normalize_document_source_context(source_context)
	except ValueError as exc:
		raise HTTPException(
			status_code=422,
			detail=_document_filter_error(
				error_code="DOCUMENT_SOURCE_CONTEXT_INVALID",
				message=str(exc),
				extra={"source_context": source_context},
			),
		) from exc

	return (
		normalized_entity_type,
		normalized_entity_id,
		normalized_document_type,
		normalized_category,
		normalized_source_context,
	)


def _validate_date_filter(value: str | None, *, param_name: str) -> None:
	if not value:
		return
	try:
		datetime.fromisoformat(value.replace("Z", "+00:00"))
	except ValueError as exc:
		raise HTTPException(
			status_code=422,
			detail=_document_filter_error(
				error_code=f"DOCUMENT_{param_name.upper()}_INVALID",
				message=f"{param_name} must be a valid ISO-8601 datetime",
				extra={param_name: value},
			),
		) from exc


def _collect_available_filters_from_items(
	items: list[dict[str, Any]],
	*,
	document_type: str | None,
	source_context: str | None,
) -> dict[str, list[str]]:
	"""Compute available filter facets from the current result set — no extra query."""
	document_type_values = sorted(
		{
			str(item.get("document_type") or "")
			for item in items
			if str(item.get("document_type") or "")
			and (not source_context or str(item.get("source_context") or "") == source_context)
		}
	)
	source_context_values = sorted(
		{
			str(item.get("source_context") or "")
			for item in items
			if str(item.get("source_context") or "")
			and (not document_type or str(item.get("document_type") or "") == document_type)
		}
	)
	return {
		"document_types": document_type_values,
		"categories": sorted(
			{
				str(item.get("category") or "")
				for item in items
				if str(item.get("category") or "")
			}
		),
		"source_contexts": source_context_values,
	}


def _metadata_items_by_filename(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
	return {
		str(item.get("filename")): item
		for item in items
		if item.get("filename")
	}


def _existing_document_filenames(items: list[dict[str, Any]]) -> list[str]:
	return [
		str(item.get("filename"))
		for item in items
		if item.get("filename") and storage().exists(StorageBucket.DOCUMENT, str(item.get("filename")))
	]


async def _build_document_list_response(
	*,
	metadata_items: list[dict[str, Any]],
	total: int,
	limit: int,
	offset: int,
	document_type: str | None,
	source_context: str | None,
	db,
) -> dict:
	metadata_by_filename = _metadata_items_by_filename(metadata_items)
	filenames = _existing_document_filenames(metadata_items)
	available_filters = _collect_available_filters_from_items(
		metadata_items,
		document_type=document_type,
		source_context=source_context,
	)
	missing_count = len(metadata_items) - len(filenames)
	return {
		"success": True,
		"total": max(total - missing_count, 0),
		"limit": limit,
		"offset": offset,
		"available_filters": available_filters,
		"items": [await file_metadata(name, db=db, metadata=metadata_by_filename.get(name)) for name in filenames],
	}


def _metadata_text(metadata: dict[str, Any], key: str) -> str:
	return str((metadata or {}).get(key) or "")


def _filter_metadata_names(
	filenames: list[str],
	metadata_by_filename: dict[str, dict[str, Any]],
	*,
	entity_type: str | None,
	entity_id: str | None,
	query: str | None,
	uploader_query: str | None = None,
) -> list[str]:
	normalized_query = query.strip().lower() if query else ""
	normalized_uploader_query = uploader_query.strip().lower() if uploader_query else ""
	filtered: list[str] = []

	for name in filenames:
		metadata = metadata_by_filename.get(name) or {}
		if entity_type and _metadata_text(metadata, "entity_type") != entity_type:
			continue
		if entity_id and _metadata_text(metadata, "entity_id") != entity_id:
			continue
		if normalized_query and (
			normalized_query not in name.lower()
			and normalized_query not in _metadata_text(metadata, "original_name").lower()
		):
			continue
		if normalized_uploader_query and not any(
			normalized_uploader_query in _metadata_text(metadata, key).lower()
			for key in ("uploaded_employee_id", "uploaded_employee_code", "uploaded_by_user_id")
		):
			continue
		filtered.append(name)

	return filtered


def _filter_result_names(
	filenames: list[str],
	metadata_by_filename: dict[str, dict[str, Any]],
	*,
	document_type: str | None,
	category: str | None,
	source_context: str | None,
	is_locked: bool | None,
	date_from: str | None,
	date_to: str | None,
) -> list[str]:
	filtered: list[str] = []

	for name in filenames:
		metadata = metadata_by_filename.get(name) or {}
		if document_type and _metadata_text(metadata, "document_type") != document_type:
			continue
		if category and _metadata_text(metadata, "category") != category:
			continue
		if source_context and _metadata_text(metadata, "source_context") != source_context:
			continue
		if is_locked is not None and bool((metadata or {}).get("is_locked")) is not is_locked:
			continue
		if date_from and _metadata_text(metadata, "uploaded_at") < date_from:
			continue
		if date_to and _metadata_text(metadata, "uploaded_at") > date_to:
			continue
		filtered.append(name)

	return filtered


async def list_documents(
	*,
	current_user: dict,
	query: Optional[str] = None,
	uploader_query: str | None = None,
	entity_type: str | None = None,
	entity_id: str | None = None,
	document_type: str | None = None,
	category: str | None = None,
	source_context: str | None = None,
	is_locked: bool | None = None,
	date_from: str | None = None,
	date_to: str | None = None,
	tags_any: list[str] | None = None,
	tags_all: list[str] | None = None,
	text_query: str | None = None,
	limit: int = 50,
	offset: int = 0,
	db=None,
) -> dict:
	(
		normalized_entity_type,
		normalized_entity_id,
		normalized_document_type,
		normalized_category,
		normalized_source_context,
	) = _normalize_document_list_filters(
		entity_type=entity_type,
		entity_id=entity_id,
		document_type=document_type,
		category=category,
		source_context=source_context,
	)
	_validate_date_filter(date_from, param_name="date_from")
	_validate_date_filter(date_to, param_name="date_to")

	owner_field: str | None = None
	owner_value: str | None = None
	if not can_manage_all_documents(current_user):
		if get_employee_id(current_user):
			owner_field = "uploaded_employee_id"
			owner_value = get_employee_id(current_user)
		elif get_employee_code(current_user):
			owner_field = "uploaded_employee_code"
			owner_value = get_employee_code(current_user)
		else:
			owner_field = "uploaded_by_user_id"
			owner_value = get_user_id(current_user)

	if db is not None:
		metadata_items, total = await metadata_repository(db=db).list_documents(
			owner_field=owner_field,
			owner_value=owner_value,
			query=query.strip() if query else None,
			uploader_query=uploader_query.strip() if uploader_query else None,
			entity_type=normalized_entity_type,
			entity_id=normalized_entity_id,
			document_type=normalized_document_type,
			category=normalized_category,
			source_context=normalized_source_context,
			is_locked=is_locked,
			date_from=date_from,
			date_to=date_to,
			tags_any=tags_any,
			tags_all=tags_all,
			text_query=text_query,
			limit=limit,
			offset=offset,
		)
		return await _build_document_list_response(
			metadata_items=metadata_items,
			total=total,
			limit=limit,
			offset=offset,
			document_type=normalized_document_type,
			source_context=normalized_source_context,
			db=db,
		)

	_require_in_memory_listing_allowed()
	filenames = storage().list_names(StorageBucket.DOCUMENT)
	metadata_by_filename = await metadata_repository(db=db).get_many(filenames)
	filenames.sort(
		key=lambda name: str((metadata_by_filename.get(name) or {}).get("uploaded_at") or ""),
		reverse=True,
	)

	if owner_field and owner_value:
		filenames = [
			name
			for name in filenames
			if str((metadata_by_filename.get(name) or {}).get(owner_field) or "") == owner_value
		]

	filenames = _filter_metadata_names(
		filenames,
		metadata_by_filename,
		entity_type=normalized_entity_type,
		entity_id=normalized_entity_id,
		query=query,
		uploader_query=uploader_query,
	)

	# Compute filters from pre-narrowed set (before applying document_type/category/source_context)
	available_filters = _collect_available_filters_from_items(
		[metadata_by_filename.get(name) or {} for name in filenames],
		document_type=normalized_document_type,
		source_context=normalized_source_context,
	)

	filenames = _filter_result_names(
		filenames,
		metadata_by_filename,
		document_type=normalized_document_type,
		category=normalized_category,
		source_context=normalized_source_context,
		is_locked=is_locked,
		date_from=date_from,
		date_to=date_to,
	)

	total = len(filenames)
	sliced = filenames[offset : offset + limit]
	return {
		"success": True,
		"total": total,
		"limit": limit,
		"offset": offset,
		"available_filters": available_filters,
		"items": [await file_metadata(name, db=db, metadata=metadata_by_filename.get(name)) for name in sliced],
	}


async def list_subject_documents(
	*,
	employee_id: str,
	employee_code: str | None = None,
	query: Optional[str] = None,
	entity_type: str | None = None,
	entity_id: str | None = None,
	document_type: str | None = None,
	category: str | None = None,
	source_context: str | None = None,
	is_locked: bool | None = None,
	date_from: str | None = None,
	date_to: str | None = None,
	limit: int = 50,
	offset: int = 0,
	db=None,
) -> dict:
	(
		normalized_entity_type,
		normalized_entity_id,
		normalized_document_type,
		normalized_category,
		normalized_source_context,
	) = _normalize_document_list_filters(
		entity_type=entity_type,
		entity_id=entity_id,
		document_type=document_type,
		category=category,
		source_context=source_context,
	)
	_validate_date_filter(date_from, param_name="date_from")
	_validate_date_filter(date_to, param_name="date_to")

	normalized_employee_id = str(employee_id or "").strip()
	normalized_employee_code = str(employee_code or "").strip() or None
	owner_field = "subject_employee_id" if normalized_employee_id else "subject_employee_code"
	owner_value = normalized_employee_id or normalized_employee_code
	if not owner_value:
		raise HTTPException(status_code=400, detail="No employee profile linked to your account")

	if db is not None:
		metadata_items, total = await metadata_repository(db=db).list_documents(
			owner_field=owner_field,
			owner_value=owner_value,
			query=query.strip() if query else None,
			uploader_query=None,
			entity_type=normalized_entity_type,
			entity_id=normalized_entity_id,
			document_type=normalized_document_type,
			category=normalized_category,
			source_context=normalized_source_context,
			is_locked=is_locked,
			date_from=date_from,
			date_to=date_to,
			limit=limit,
			offset=offset,
		)
		return await _build_document_list_response(
			metadata_items=metadata_items,
			total=total,
			limit=limit,
			offset=offset,
			document_type=normalized_document_type,
			source_context=normalized_source_context,
			db=db,
		)

	_require_in_memory_listing_allowed()
	filenames = storage().list_names(StorageBucket.DOCUMENT)
	metadata_by_filename = await metadata_repository(db=db).get_many(filenames)
	filenames.sort(
		key=lambda name: str((metadata_by_filename.get(name) or {}).get("uploaded_at") or ""),
		reverse=True,
	)

	filenames = [
		name
		for name in filenames
		if is_subject_document_owner(
			metadata_by_filename.get(name),
			employee_id=normalized_employee_id,
			employee_code=normalized_employee_code,
		)
	]

	filenames = _filter_metadata_names(
		filenames,
		metadata_by_filename,
		entity_type=normalized_entity_type,
		entity_id=normalized_entity_id,
		query=query,
	)

	# Compute filters from pre-narrowed set
	available_filters = _collect_available_filters_from_items(
		[metadata_by_filename.get(name) or {} for name in filenames],
		document_type=normalized_document_type,
		source_context=normalized_source_context,
	)

	filenames = _filter_result_names(
		filenames,
		metadata_by_filename,
		document_type=normalized_document_type,
		category=normalized_category,
		source_context=normalized_source_context,
		is_locked=is_locked,
		date_from=date_from,
		date_to=date_to,
	)

	total = len(filenames)
	sliced = filenames[offset : offset + limit]
	return {
		"success": True,
		"total": total,
		"limit": limit,
		"offset": offset,
		"available_filters": available_filters,
		"items": [await file_metadata(name, db=db, metadata=metadata_by_filename.get(name)) for name in sliced],
	}


async def get_document_metadata(filename: str, *, current_user: dict, db=None) -> dict:
	if not storage().exists(StorageBucket.DOCUMENT, filename):
		raise HTTPException(status_code=404, detail="Document not found")
	await require_document_access(filename, current_user, db=db)
	return {
		"success": True,
		"item": await file_metadata(filename, db=db),
	}
