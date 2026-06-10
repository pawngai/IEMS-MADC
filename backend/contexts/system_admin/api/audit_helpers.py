from __future__ import annotations

from datetime import datetime
from io import StringIO
import csv
from typing import Any

from fastapi import HTTPException

from contexts.audit.contracts.audit_directory import count_audit_logs, list_audit_logs

def _build_audit_query(
	*,
	action_filter: str | None = None,
	entity_type_filter: str | None = None,
	from_timestamp: str | None = None,
	to_timestamp: str | None = None,
) -> dict[str, Any]:
	def _normalize_timestamp(value: str | None, *, field_name: str) -> str | None:
		if not value:
			return None
		normalized = str(value).strip()
		if not normalized:
			return None
		candidate = normalized.replace("Z", "+00:00") if normalized.endswith("Z") else normalized
		try:
			return datetime.fromisoformat(candidate).isoformat()
		except ValueError as exc:
			raise HTTPException(status_code=400, detail=f"Invalid {field_name}. Expected ISO-8601 timestamp.") from exc

	normalized_from = _normalize_timestamp(from_timestamp, field_name="from_timestamp")
	normalized_to = _normalize_timestamp(to_timestamp, field_name="to_timestamp")
	if normalized_from and normalized_to and normalized_from > normalized_to:
		raise HTTPException(status_code=400, detail="from_timestamp must be less than or equal to to_timestamp.")

	query: dict[str, Any] = {}
	if action_filter:
		query["action"] = action_filter
	if entity_type_filter:
		query["resource_type"] = entity_type_filter
	if normalized_from or normalized_to:
		timestamp_query: dict[str, str] = {}
		if normalized_from:
			timestamp_query["$gte"] = normalized_from
		if normalized_to:
			timestamp_query["$lte"] = normalized_to
		query["timestamp"] = timestamp_query
	return query


async def _fetch_audit_logs(
	db,
	*,
	limit: int,
	offset: int,
	action_filter: str | None = None,
	entity_type_filter: str | None = None,
	from_timestamp: str | None = None,
	to_timestamp: str | None = None,
) -> dict[str, Any]:
	query = _build_audit_query(
		action_filter=action_filter,
		entity_type_filter=entity_type_filter,
		from_timestamp=from_timestamp,
		to_timestamp=to_timestamp,
	)
	total = await count_audit_logs(db, query=query)
	logs = await list_audit_logs(db, query=query, limit=limit, offset=offset)
	return {"logs": logs, "total": total, "limit": limit, "offset": offset}


def _normalize_audit_export_row(row: dict[str, Any]) -> dict[str, str]:
	return {
		"timestamp": str(row.get("timestamp") or ""),
		"action": str(row.get("action") or ""),
		"entity_type": str(row.get("resource_type") or ""),
		"entity_id": str(row.get("resource_id") or ""),
		"actor": str(row.get("user_name") or row.get("user_id") or ""),
	}


async def _stream_audit_export_csv(
	db,
	*,
	query: dict[str, Any],
	limit: int,
):
	headers = ["timestamp", "action", "entity_type", "entity_id", "actor"]
	buffer = StringIO()
	writer = csv.DictWriter(buffer, fieldnames=headers)
	writer.writeheader()
	yield buffer.getvalue()
	buffer.seek(0)
	buffer.truncate(0)

	rows = await list_audit_logs(
		db,
		query=query,
		limit=limit,
		projection={"_id": 0, "timestamp": 1, "action": 1, "resource_type": 1, "resource_id": 1, "user_name": 1, "user_id": 1},
	)

	for row in rows:
		writer.writerow(_normalize_audit_export_row(row))
		yield buffer.getvalue()
		buffer.seek(0)
		buffer.truncate(0)


