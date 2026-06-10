from __future__ import annotations

from contexts.service_book.contracts.servicebook.part_constants import SB_LEDGER_PART_KEY_BY_ROMAN
from contexts.service_book.contracts.servicebook.schema_assets import (
    SCHEMA_DEFINITIONS,
    SERVICEBOOK_FIELDS_BY_SCHEMA_KEY,
)


def normalize_part_code(part_value: str | None) -> str | None:
	normalized = str(part_value or "").strip().upper()
	if not normalized:
		return None
	if normalized in SB_LEDGER_PART_KEY_BY_ROMAN.values():
		return normalized
	return SB_LEDGER_PART_KEY_BY_ROMAN.get(normalized)


async def get_service_book(*, repo, employee_id: str) -> dict:
	return await repo.get_service_book(employee_id=employee_id)


async def get_service_book_part(*, repo, employee_id: str, part_code: str) -> dict | None:
	return await repo.get_part(employee_id=employee_id, part_code=part_code)


async def list_service_book_entries(*, repo, employee_id: str, filters: dict) -> list[dict]:
	return await repo.list_entries(employee_id=employee_id, filters=filters)


async def get_part_schema(*, part_key: str) -> dict:
	part_code = normalize_part_code(part_key)
	if not part_code:
		raise ValueError("Invalid service book part")

	schema_keys = [
		schema_key
		for schema_key, definition in SCHEMA_DEFINITIONS.items()
		if definition.part_key == part_code
	]
	canonical_fields = []
	seen = set()
	for schema_key in schema_keys:
		for field in SERVICEBOOK_FIELDS_BY_SCHEMA_KEY.get(schema_key, []):
			key = field.get("key")
			if key and key not in seen:
				seen.add(key)
				canonical_fields.append(key)
	return {
		"part_key": part_code,
		"schema_keys": schema_keys,
		"json_schema": {
			"canonical_fields": canonical_fields,
		},
	}
