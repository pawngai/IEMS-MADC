"""Documents domain — metadata validation and normalization rules."""
from __future__ import annotations

from typing import Any

from contexts.documents.domain.validation import (
	normalize_document_category,
	normalize_document_entity_type,
	normalize_document_source_context,
	normalize_document_type,
	normalize_tags,
)


def validate_document_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
	"""Validate and normalize document metadata.

	Raises ValueError for invalid inputs (caller converts to HTTP errors).
	"""
	normalized = dict(metadata or {})

	entity_type = normalize_document_entity_type(normalized.get("entity_type"))
	document_type = normalize_document_type(normalized.get("document_type"))
	source_context = normalize_document_source_context(normalized.get("source_context"))
	category = normalize_document_category(normalized.get("category"))
	tags = normalize_tags(normalized.get("tags")) if "tags" in normalized else None

	expires_at = normalized.get("expires_at")
	if expires_at is not None:
		text = str(expires_at).strip()
		if text:
			try:
				from datetime import datetime as _datetime
				_datetime.fromisoformat(text.replace("Z", "+00:00"))
			except ValueError as exc:
				raise ValueError("expires_at must be a valid ISO-8601 datetime") from exc
			normalized["expires_at"] = text
		else:
			normalized.pop("expires_at", None)

	entity_id = str(normalized.get("entity_id") or "").strip()
	supersedes_document_id = str(normalized.get("supersedes_document_id") or "").strip()
	subject_employee_id = str(normalized.get("subject_employee_id") or "").strip()
	subject_employee_code = str(normalized.get("subject_employee_code") or "").strip()

	# Documents context stores file and metadata only; service-history truth
	# must stay in service-book/event contexts.
	prohibited = {"service_history", "service_book_truth", "official_history"}
	bad_keys = sorted(
		key
		for key in normalized.keys()
		if str(key).strip().lower() in prohibited
	)
	if bad_keys:
		raise ValueError(
			f"Document metadata cannot define service-history truth: {bad_keys}"
		)

	if entity_type and not entity_id:
		raise ValueError("entity_id is required when entity_type is provided")
	if entity_id and not entity_type:
		raise ValueError("entity_type is required when entity_id is provided")

	if entity_type:
		normalized["entity_type"] = entity_type
	if entity_id:
		normalized["entity_id"] = entity_id
	if document_type:
		normalized["document_type"] = document_type
	if category:
		normalized["category"] = category
	if source_context:
		normalized["source_context"] = source_context
	if supersedes_document_id:
		normalized["supersedes_document_id"] = supersedes_document_id
	if subject_employee_id:
		normalized["subject_employee_id"] = subject_employee_id
	if subject_employee_code:
		normalized["subject_employee_code"] = subject_employee_code
	if tags is not None:
		normalized["tags"] = tags
	return normalized
