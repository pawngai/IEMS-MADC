from __future__ import annotations

from typing import Any

try:
    from backend.contexts.employee_identity.contracts.identity_directory import resolve_identity_ref
except ModuleNotFoundError:
    from contexts.employee_identity.contracts.identity_directory import resolve_identity_ref


MIGRATION_MARKER = "document-subject-employee-backfill-v1"


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _result_count(result: Any, *, default: int = 0) -> int:
    for key in ("modified_count", "matched_count"):
        value = getattr(result, key, None)
        if isinstance(value, int):
            return value
    return default


def _collection(db, name: str):
    return db[name] if hasattr(db, "__getitem__") else getattr(db, name)


async def _resolve_service_event_subject_identity(db, *, entity_id: str) -> tuple[dict[str, Any] | None, str]:
    stream = await _collection(db, "service_events").find_one(
        {"events.service_event_id": entity_id},
        {"_id": 0, "employee_id": 1},
    )
    employee_id = _normalize_text((stream or {}).get("employee_id"))
    if not employee_id:
        return None, "service_event_stream_missing"
    identity = await resolve_identity_ref(
        db,
        ref=employee_id,
        projection={"_id": 0, "employee_id": 1, "employee_code": 1},
    )
    return identity, "service_event_stream"


def _needs_subject_backfill(document: dict[str, Any]) -> bool:
    subject_employee_id = _normalize_text(document.get("subject_employee_id"))
    subject_employee_code = _normalize_text(document.get("subject_employee_code"))
    entity_type = _normalize_text(document.get("entity_type")).upper()
    entity_id = _normalize_text(document.get("entity_id"))

    if subject_employee_id and subject_employee_code:
        return False
    if subject_employee_id or subject_employee_code:
        return True
    return entity_type == "SERVICE_EVENT" and bool(entity_id)


async def _resolve_subject_identity_for_document(db, document: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    subject_employee_id = _normalize_text(document.get("subject_employee_id"))
    subject_employee_code = _normalize_text(document.get("subject_employee_code"))
    entity_type = _normalize_text(document.get("entity_type")).upper()
    entity_id = _normalize_text(document.get("entity_id"))

    direct_ref = subject_employee_id or subject_employee_code
    if direct_ref:
        identity = await resolve_identity_ref(
            db,
            ref=direct_ref,
            projection={"_id": 0, "employee_id": 1, "employee_code": 1},
        )
        if identity:
            return identity, "subject_reference"
        if entity_type == "SERVICE_EVENT" and entity_id:
            identity, source = await _resolve_service_event_subject_identity(db, entity_id=entity_id)
            if identity:
                return identity, "service_event_stream_fallback"
            return None, source
        return None, "subject_reference"

    if entity_type == "SERVICE_EVENT" and entity_id:
        return await _resolve_service_event_subject_identity(db, entity_id=entity_id)

    return None, "no_subject_reference"


async def backfill_document_subject_employee(
    db,
    *,
    dry_run: bool = False,
    document_id: str | None = None,
) -> dict[str, Any]:
    document_id = _normalize_text(document_id) or None
    projection = {
        "_id": 0,
        "document_id": 1,
        "filename": 1,
        "entity_type": 1,
        "entity_id": 1,
        "subject_employee_id": 1,
        "subject_employee_code": 1,
    }
    query = {"document_id": document_id} if document_id else {}
    cursor = _collection(db, "document_metadata").find(query, projection)
    documents = [document async for document in cursor]

    summary: dict[str, Any] = {
        "dry_run": dry_run,
        "migration_marker": MIGRATION_MARKER,
        "document_filter": document_id,
        "documents_scanned": len(documents),
        "candidate_documents": 0,
        "documents_updated": 0,
        "skipped_already_canonical": 0,
        "skipped_no_subject_reference": 0,
        "skipped_missing_service_event_stream": 0,
        "skipped_unresolved_identity": 0,
        "documents": [],
    }

    document_metadata = _collection(db, "document_metadata")

    for document in documents:
        doc_id = _normalize_text(document.get("document_id")) or _normalize_text(document.get("filename"))
        if not _needs_subject_backfill(document):
            summary["skipped_already_canonical"] += 1
            summary["documents"].append({"document_id": doc_id, "action": "skipped_already_canonical"})
            continue

        summary["candidate_documents"] += 1
        identity, source = await _resolve_subject_identity_for_document(db, document)
        if source == "no_subject_reference":
            summary["skipped_no_subject_reference"] += 1
            summary["documents"].append({"document_id": doc_id, "action": "skipped_no_subject_reference"})
            continue
        if source == "service_event_stream_missing":
            summary["skipped_missing_service_event_stream"] += 1
            summary["documents"].append({"document_id": doc_id, "action": "skipped_missing_service_event_stream"})
            continue

        subject_id = _normalize_text((identity or {}).get("employee_id"))
        subject_code = _normalize_text((identity or {}).get("employee_code"))
        if not subject_id or not subject_code:
            summary["skipped_unresolved_identity"] += 1
            summary["documents"].append({"document_id": doc_id, "action": "skipped_unresolved_identity", "source": source})
            continue

        update_fields = {
            "subject_employee_id": subject_id,
            "subject_employee_code": subject_code,
            "document_subject_employee_backfill_marker": MIGRATION_MARKER,
        }

        summary["documents"].append(
            {
                "document_id": doc_id,
                "action": "would_update" if dry_run else "updated",
                "source": source,
                "subject_employee_id": subject_id,
                "subject_employee_code": subject_code,
            }
        )
        if dry_run:
            summary["documents_updated"] += 1
            continue

        result = await document_metadata.update_one(
            {"document_id": doc_id},
            {"$set": update_fields},
        )
        summary["documents_updated"] += _result_count(result, default=1)

    return summary