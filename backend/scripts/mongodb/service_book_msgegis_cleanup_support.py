from __future__ import annotations

from typing import Any


MIGRATION_MARKER = "service-book-msgegis-cleanup-v1"

REMOVED_SCHEMA_KEYS = {
    "SB_IIB_MSGEGIS_NOMINATION_ROW",
    "SB_IIB_MSGEGIS_POLICY",
    "SB_VII_MSGEGIS_ROW",
    "SB_PART_IIB_MSGEGIS_NOMINATION_ROW",
    "SB_PART_IIB_MSGEGIS_POLICY",
    "SB_PART_VII_MSGEGIS_ROW",
}

REMOVED_FIELD_KEYS = {
    "msgegis_nomination",
    "msgegis_nomination_date",
    "msgegis_policy_number",
    "msgegis_records",
    "insurance_nominee_name",
    "insurance_nominee_relation",
    "insurance_nominee_share_percent",
    "insurance_nominations",
}


def _collection(db, name: str):
    return db[name] if hasattr(db, "__getitem__") else getattr(db, name)


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


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
    raise ValueError(f"Unsupported collection for MSGEGIS cleanup: {collection_name}")


def _describe_document(collection_name: str, document: dict[str, Any], *, action: str) -> dict[str, Any]:
    return {
        "collection": collection_name,
        "action": action,
        "employee_id": document.get("employee_id"),
        "id": document.get("entry_id") or document.get("id") or document.get("opening_id") or document.get("employee_id"),
        "schema_key": document.get("schema_key"),
    }


def _strip_removed_fields(values: Any) -> tuple[Any, bool]:
    if not isinstance(values, dict):
        return values, False

    next_values = dict(values)
    changed = False
    for key in REMOVED_FIELD_KEYS:
        if key in next_values:
            del next_values[key]
            changed = True
    return next_values, changed


def _strip_removed_strings(values: Any, *, removed_values: set[str]) -> tuple[Any, bool]:
    if not isinstance(values, list):
        return values, False

    next_values = [value for value in values if value not in removed_values]
    return next_values, len(next_values) != len(values)


def _cleanup_service_book_document(document: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    normalized_schema_key = _normalize_text(document.get("schema_key")).upper()
    if normalized_schema_key in REMOVED_SCHEMA_KEYS:
        return "delete", None

    next_document = dict(document)
    changed = False

    cleaned_document, document_changed = _strip_removed_fields(next_document)
    if document_changed:
        next_document = cleaned_document
        changed = True

    cleaned_payload, payload_changed = _strip_removed_fields(next_document.get("payload"))
    if payload_changed:
        next_document["payload"] = cleaned_payload
        changed = True

    cleaned_fields_changed, fields_changed = _strip_removed_strings(
        next_document.get("fields_changed"),
        removed_values=REMOVED_FIELD_KEYS,
    )
    if fields_changed:
        next_document["fields_changed"] = cleaned_fields_changed
        changed = True

    cleaned_schema_keys, schema_keys_changed = _strip_removed_strings(
        next_document.get("schema_keys"),
        removed_values=REMOVED_SCHEMA_KEYS,
    )
    if schema_keys_changed:
        next_document["schema_keys"] = cleaned_schema_keys
        changed = True

    if not changed:
        return "none", document
    return "replace", next_document


def _cleanup_opening_document(document: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    next_document = dict(document)
    changed = False

    cleaned_part_iib, part_iib_changed = _strip_removed_fields(next_document.get("part_iib"))
    if part_iib_changed:
        next_document["part_iib"] = cleaned_part_iib
        changed = True

    parts = next_document.get("parts")
    if isinstance(parts, dict):
        next_parts = dict(parts)
        cleaned_nested_part_iib, nested_changed = _strip_removed_fields(next_parts.get("part_iib"))
        if nested_changed:
            next_parts["part_iib"] = cleaned_nested_part_iib
            next_document["parts"] = next_parts
            changed = True

    if not changed:
        return "none", document
    return "replace", next_document


async def cleanup_service_book_msgegis_data(
    db,
    *,
    dry_run: bool = True,
    employee_id: str | None = None,
) -> dict[str, Any]:
    normalized_employee_id = _normalize_text(employee_id) or None
    base_query: dict[str, Any] = {"employee_id": normalized_employee_id} if normalized_employee_id else {}

    collection_transforms = (
        ("service_book_entries", _cleanup_service_book_document),
        ("service_book_workflow_entries", _cleanup_service_book_document),
        ("service_book_part_projections", _cleanup_service_book_document),
        ("service_book_openings", _cleanup_opening_document),
    )

    summary: dict[str, Any] = {
        "dry_run": dry_run,
        "migration_marker": MIGRATION_MARKER,
        "employee_filter": normalized_employee_id,
        "removed_schema_keys": sorted(REMOVED_SCHEMA_KEYS),
        "removed_field_keys": sorted(REMOVED_FIELD_KEYS),
        "collections": {},
        "documents": [],
    }

    for collection_name, transform in collection_transforms:
        collection = _collection(db, collection_name)
        cursor = collection.find(base_query)
        documents = [document async for document in cursor]

        collection_summary = {
            "scanned": len(documents),
            "would_delete": 0,
            "deleted": 0,
            "would_update": 0,
            "updated": 0,
        }

        for document in documents:
            action, next_document = transform(document)
            if action == "none":
                continue

            if action == "delete":
                collection_summary["would_delete"] += 1
                summary["documents"].append(_describe_document(collection_name, document, action="delete"))
                if not dry_run:
                    match_query = _match_query(collection_name, document)
                    result = await collection.delete_one(match_query)
                    collection_summary["deleted"] += int(getattr(result, "deleted_count", 0) or 0)
                continue

            collection_summary["would_update"] += 1
            summary["documents"].append(_describe_document(collection_name, document, action="update"))
            if dry_run:
                continue

            match_query = _match_query(collection_name, document)
            result = await collection.replace_one(match_query, next_document, upsert=False)
            collection_summary["updated"] += int(getattr(result, "modified_count", 0) or 0)

        summary["collections"][collection_name] = collection_summary

    return summary