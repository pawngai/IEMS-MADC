from __future__ import annotations

from typing import Any


MIGRATION_MARKER = "service-book-truth-boundary-cleanup-v1"
APPROVED_SERVICE_EVENT_NAME = "ServiceEventLifecycleApproved"
MANUAL_SERVICE_BOOK_EVENT_NAMES = {"ServiceBookEntryApproved", "ServiceBookEntryLocked"}
NON_TRUTH_SERVICE_EVENT_NAMES = {
    "ServiceEventRecorded",
    "ServiceEventDocumentAttached",
    "ServiceEventLifecycleSubmitted",
    "ServiceEventLifecycleVerified",
}
DOCUMENT_TRUTH_KEYS = {
    "document",
    "documents",
    "document_id",
    "document_ids",
    "document_type",
    "document_types",
    "attachments",
    "attachment_ids",
}
WORKFLOW_TRUTH_KEYS = {
    "action",
    "approved_at",
    "approved_by",
    "locked_at",
    "locked_by",
    "rejected_at",
    "rejected_by",
    "status",
    "submitted_at",
    "submitted_by",
    "verified_at",
    "verified_by",
    "workflow",
    "workflow_payload",
    "workflow_state",
}
TRUTH_DENY_KEYS = DOCUMENT_TRUTH_KEYS | WORKFLOW_TRUTH_KEYS


def _collection(db, name: str):
    return db[name] if hasattr(db, "__getitem__") else getattr(db, name)


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _entry_id(entry: dict[str, Any]) -> str | None:
    return _normalize_text(entry.get("entry_id") or entry.get("id")) or None


def _entry_match_query(entry: dict[str, Any]) -> dict[str, str] | None:
    entry_id = _normalize_text(entry.get("entry_id"))
    if entry_id:
        return {"entry_id": entry_id}
    manual_id = _normalize_text(entry.get("id"))
    if manual_id:
        return {"id": manual_id}
    return None


def _payload_denied_paths(value: Any, *, prefix: str = "payload") -> list[str]:
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            normalized_key = _normalize_text(key).lower()
            path = f"{prefix}.{key}"
            if normalized_key in TRUTH_DENY_KEYS:
                paths.append(path)
                continue
            paths.extend(_payload_denied_paths(item, prefix=path))
        return paths
    if isinstance(value, list):
        paths: list[str] = []
        for index, item in enumerate(value):
            paths.extend(_payload_denied_paths(item, prefix=f"{prefix}[{index}]"))
        return paths
    return []


def classify_service_book_truth_boundary_entry(entry: dict[str, Any]) -> dict[str, Any] | None:
    event_name = _normalize_text(entry.get("event_name"))
    payload = entry.get("payload") if isinstance(entry.get("payload"), dict) else {}
    denied_paths = _payload_denied_paths(payload)

    if event_name in NON_TRUTH_SERVICE_EVENT_NAMES:
        return {
            "entry_id": _entry_id(entry),
            "employee_id": entry.get("employee_id"),
            "event_name": event_name,
            "action": "delete_non_truth_service_event_projection",
            "denied_payload_paths": denied_paths,
        }

    if event_name == APPROVED_SERVICE_EVENT_NAME and denied_paths:
        return {
            "entry_id": _entry_id(entry),
            "employee_id": entry.get("employee_id"),
            "event_name": event_name,
            "action": "sanitize_approved_service_event_payload",
            "denied_payload_paths": denied_paths,
        }

    if event_name in MANUAL_SERVICE_BOOK_EVENT_NAMES and denied_paths:
        return {
            "entry_id": _entry_id(entry),
            "employee_id": entry.get("employee_id"),
            "event_name": event_name,
            "action": "sanitize_manual_exception_payload",
            "denied_payload_paths": denied_paths,
        }

    return None


def sanitized_service_book_truth_payload(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    sanitized = {}
    for key, item in value.items():
        if _normalize_text(key).lower() in TRUTH_DENY_KEYS:
            continue
        if isinstance(item, dict):
            sanitized[key] = sanitized_service_book_truth_payload(item)
        elif isinstance(item, list):
            sanitized[key] = [
                sanitized_service_book_truth_payload(element) if isinstance(element, dict) else element
                for element in item
            ]
        else:
            sanitized[key] = item
    return sanitized


async def cleanup_service_book_truth_boundary(
    db,
    *,
    dry_run: bool = True,
    employee_id: str | None = None,
    delete_non_truth: bool = False,
    sanitize_payloads: bool = False,
) -> dict[str, Any]:
    normalized_employee_id = _normalize_text(employee_id) or None
    query: dict[str, Any] = {"employee_id": normalized_employee_id} if normalized_employee_id else {}
    cursor = _collection(db, "service_book_entries").find(query, {"_id": 0})
    entries = [entry async for entry in cursor]

    summary: dict[str, Any] = {
        "dry_run": dry_run,
        "migration_marker": MIGRATION_MARKER,
        "employee_filter": normalized_employee_id,
        "entries_scanned": len(entries),
        "candidate_entries": 0,
        "would_delete": 0,
        "would_sanitize": 0,
        "deleted": 0,
        "sanitized": 0,
        "entries": [],
    }
    collection = _collection(db, "service_book_entries")

    for entry in entries:
        classification = classify_service_book_truth_boundary_entry(entry)
        if classification is None:
            continue

        summary["candidate_entries"] += 1
        action = classification["action"]
        match_query = _entry_match_query(entry)
        summary["entries"].append(classification)

        if action == "delete_non_truth_service_event_projection":
            summary["would_delete"] += 1
            if not dry_run and delete_non_truth and match_query:
                result = await collection.delete_one(match_query)
                summary["deleted"] += int(getattr(result, "deleted_count", 0) or 0)
            continue

        summary["would_sanitize"] += 1
        if not dry_run and sanitize_payloads and match_query:
            result = await collection.update_one(
                match_query,
                {
                    "$set": {
                        "payload": sanitized_service_book_truth_payload(entry.get("payload")),
                        "truth_boundary_cleanup_marker": MIGRATION_MARKER,
                    }
                },
            )
            summary["sanitized"] += int(getattr(result, "modified_count", 0) or 0)

    return summary