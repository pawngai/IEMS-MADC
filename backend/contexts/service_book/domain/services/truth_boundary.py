from __future__ import annotations

from typing import Any

from app_platform.event_bus.types import EventName
from contexts.service_book.domain.policies.manual_entry_policy import policy_for_manual_entry


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
SERVICE_EVENT_TRUTH_METADATA_KEYS = {
    "effective_from",
    "effective_to",
    "event_type",
    "record_category",
    "record_type",
}
TRUTH_DENY_KEYS = DOCUMENT_TRUTH_KEYS | WORKFLOW_TRUTH_KEYS


def _strip_non_truth_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _strip_non_truth_fields(item)
            for key, item in value.items()
            if str(key).strip().lower() not in TRUTH_DENY_KEYS
        }
    if isinstance(value, list):
        return [_strip_non_truth_fields(item) for item in value]
    return value


def service_event_projects_service_truth(*, event_name: str, payload: dict[str, Any]) -> bool:
    if event_name != EventName.SERVICE_EVENT_APPROVED.value:
        return False
    return str(payload.get("status") or "").upper() == "APPROVED"


def approved_service_event_truth_payload(payload: dict[str, Any]) -> dict[str, Any]:
    nested_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
    truth_payload = _strip_non_truth_fields(nested_payload)
    if not isinstance(truth_payload, dict):
        truth_payload = {}
    for key in SERVICE_EVENT_TRUTH_METADATA_KEYS:
        value = payload.get(key)
        if value not in (None, "") and key not in truth_payload:
            truth_payload[key] = value
    return truth_payload


def manual_entry_projects_service_truth(*, event_name: str, payload: dict[str, Any]) -> bool:
    if event_name not in {
        EventName.SERVICE_BOOK_ENTRY_APPROVED.value,
        EventName.SERVICE_BOOK_ENTRY_LOCKED.value,
    }:
        return False
    schema_key = str(payload.get("schema_key") or "").strip().upper()
    part_key = str(payload.get("part_key") or payload.get("part_code") or "").strip().upper()
    return policy_for_manual_entry(schema_key=schema_key, part_key=part_key) is not None


def manual_entry_truth_payload(payload: dict[str, Any]) -> dict[str, Any]:
    nested_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
    truth_payload = _strip_non_truth_fields(nested_payload)
    return truth_payload if isinstance(truth_payload, dict) else {}