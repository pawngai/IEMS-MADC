from __future__ import annotations

from typing import Any

from contexts.service_book.contracts.servicebook.schema_assets import (
    SERVICEBOOK_FIELDS_BY_SCHEMA_KEY,
)


def required_fields_for_schema(schema_key: str) -> list[str]:
    return [
        field["key"]
        for field in SERVICEBOOK_FIELDS_BY_SCHEMA_KEY.get(schema_key, [])
        if field.get("required")
    ]


def missing_required_fields(*, schema_key: str, payload: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for field_name in required_fields_for_schema(schema_key):
        value = payload.get(field_name)
        if value is None:
            missing.append(field_name)
            continue
        if isinstance(value, str) and not value.strip():
            missing.append(field_name)
            continue
        if isinstance(value, list) and not value:
            missing.append(field_name)
    return missing
