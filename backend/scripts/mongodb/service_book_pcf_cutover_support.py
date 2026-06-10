from __future__ import annotations

from typing import Any


MIGRATION_MARKER = "service-book-pcf-cutover-v1"

FIELD_RENAMES: dict[str, str] = {
    "gpf_account_number": "pcf_account_number",
    "gpf_nominee_name": "pcf_nominee_name",
    "gpf_nominee_relation": "pcf_nominee_relation",
    "gpf_nominee_share_percent": "pcf_nominee_share_percent",
    "gpf_nomination": "pcf_nomination",
    "gpf_nomination_date": "pcf_nomination_date",
    "gpf_nominations": "pcf_nominations",
}

SCHEMA_KEY_RENAMES: dict[str, str] = {
    "SB_IIB_GPF_NOMINATION_ROW": "SB_IIB_PCF_NOMINATION_ROW",
    "SB_PART_IIB_GPF_NOMINATION_ROW": "SB_PART_IIB_PCF_NOMINATION_ROW",
}


def _collection(db, name: str):
    return db[name] if hasattr(db, "__getitem__") else getattr(db, name)


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _rename_schema_key(value: Any) -> tuple[Any, bool]:
    normalized = _normalize_text(value)
    if not normalized:
        return value, False
    next_value = SCHEMA_KEY_RENAMES.get(normalized, value)
    return next_value, next_value != value


def _rename_string_list(values: Any) -> tuple[Any, bool]:
    if not isinstance(values, list):
        return values, False

    changed = False
    renamed: list[Any] = []
    seen: set[Any] = set()
    for value in values:
        next_value = FIELD_RENAMES.get(value, value)
        if next_value != value:
            changed = True
        if next_value in seen:
            changed = True
            continue
        seen.add(next_value)
        renamed.append(next_value)
    return renamed, changed


def _rename_mapping_fields(values: Any) -> tuple[Any, bool]:
    if not isinstance(values, dict):
        return values, False

    normalized = dict(values)
    changed = False
    for legacy_key, canonical_key in FIELD_RENAMES.items():
        if legacy_key not in normalized:
            continue
        if canonical_key not in normalized:
            normalized[canonical_key] = normalized[legacy_key]
        del normalized[legacy_key]
        changed = True
    return normalized, changed


def _match_query(collection_name: str, document: dict[str, Any]) -> dict[str, Any]:
    if document.get("_id") is not None:
        return {"_id": document["_id"]}
    if collection_name == "service_book_entries":
        if document.get("entry_id"):
            return {"entry_id": document["entry_id"]}
        if document.get("id"):
            return {"id": document["id"]}
    if collection_name == "service_book_workflow_entries":
        if document.get("id"):
            return {"id": document["id"]}
        if document.get("entry_id"):
            return {"entry_id": document["entry_id"]}
    if collection_name == "service_book_part_projections":
        return {
            "employee_id": document.get("employee_id"),
            "part_code": document.get("part_code"),
        }
    if collection_name == "service_book_openings":
        return {"employee_id": document.get("employee_id")}
    raise ValueError(f"Unsupported collection for PCF cutover: {collection_name}")


def _describe_document(collection_name: str, document: dict[str, Any]) -> dict[str, Any]:
    return {
        "collection": collection_name,
        "employee_id": document.get("employee_id"),
        "id": document.get("entry_id") or document.get("id") or document.get("opening_id") or document.get("employee_id"),
    }


def _migrate_service_book_document(document: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    next_document = dict(document)
    changed = False

    renamed_document, document_changed = _rename_mapping_fields(next_document)
    if document_changed:
        next_document = renamed_document
        changed = True

    next_schema_key, schema_changed = _rename_schema_key(next_document.get("schema_key"))
    if schema_changed:
        next_document["schema_key"] = next_schema_key
        changed = True

    next_payload, payload_changed = _rename_mapping_fields(next_document.get("payload"))
    if payload_changed:
        next_document["payload"] = next_payload
        changed = True

    next_fields_changed, fields_changed_changed = _rename_string_list(next_document.get("fields_changed"))
    if fields_changed_changed:
        next_document["fields_changed"] = next_fields_changed
        changed = True

    return next_document, changed


def _migrate_opening_document(document: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    next_document = dict(document)
    changed = False

    next_part_iib, part_iib_changed = _rename_mapping_fields(next_document.get("part_iib"))
    if part_iib_changed:
        next_document["part_iib"] = next_part_iib
        changed = True

    parts = next_document.get("parts")
    if isinstance(parts, dict):
        next_parts = dict(parts)
        next_nested_part_iib, nested_changed = _rename_mapping_fields(next_parts.get("part_iib"))
        if nested_changed:
            next_parts["part_iib"] = next_nested_part_iib
            next_document["parts"] = next_parts
            changed = True

    return next_document, changed


async def migrate_service_book_pcf_cutover(
    db,
    *,
    dry_run: bool = True,
    employee_id: str | None = None,
) -> dict[str, Any]:
    normalized_employee_id = _normalize_text(employee_id) or None
    base_query: dict[str, Any] = {"employee_id": normalized_employee_id} if normalized_employee_id else {}

    collection_transforms = (
        ("service_book_entries", _migrate_service_book_document),
        ("service_book_workflow_entries", _migrate_service_book_document),
        ("service_book_part_projections", _migrate_service_book_document),
        ("service_book_openings", _migrate_opening_document),
    )

    summary: dict[str, Any] = {
        "dry_run": dry_run,
        "migration_marker": MIGRATION_MARKER,
        "employee_filter": normalized_employee_id,
        "collections": {},
        "documents": [],
    }

    for collection_name, transform in collection_transforms:
        collection = _collection(db, collection_name)
        cursor = collection.find(base_query)
        documents = [document async for document in cursor]

        collection_summary = {
            "scanned": len(documents),
            "would_update": 0,
            "updated": 0,
        }

        for document in documents:
            next_document, changed = transform(document)
            if not changed:
                continue

            collection_summary["would_update"] += 1
            summary["documents"].append(_describe_document(collection_name, document))

            if dry_run:
                continue

            match_query = _match_query(collection_name, document)
            result = await collection.replace_one(match_query, next_document, upsert=False)
            collection_summary["updated"] += int(getattr(result, "modified_count", 0) or 0)

        summary["collections"][collection_name] = collection_summary

    return summary