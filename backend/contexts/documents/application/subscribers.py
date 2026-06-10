"""Documents application — projection subscribers.

Folds the four+ document events into the ``document_audit_timeline`` read
model. Idempotent: each entry is keyed by ``source_event_id`` so re-dispatched
events don't duplicate rows.
"""
from __future__ import annotations

from app_platform.event_bus.bus import EventBus
from app_platform.event_bus.types import BaseEvent, EventName
from contexts.documents.repository import DocumentAuditTimelineRepository


_TIMELINE_EVENT_NAMES: tuple[str, ...] = (
    EventName.DOCUMENT_UPLOADED.value,
    EventName.DOCUMENT_LOCKED.value,
    EventName.DOCUMENT_METADATA_UPDATED.value,
    EventName.DOCUMENT_DELETED.value,
    EventName.DOCUMENT_LEGAL_HOLD_APPLIED.value,
    EventName.DOCUMENT_LEGAL_HOLD_RELEASED.value,
    EventName.DOCUMENT_ACCESSED.value,
    EventName.DOCUMENT_ARCHIVED.value,
    EventName.DOCUMENT_SCAN_COMPLETED.value,
    EventName.DOCUMENT_EXPIRING_SOON.value,
    EventName.DOCUMENT_EXPIRED.value,
)


def register_documents_subscribers(*, event_bus: EventBus, db_provider) -> None:
    async def _on_event(event: BaseEvent) -> None:
        db = db_provider()
        if db is None:
            return
        payload = event.payload or {}
        document_id = str(payload.get("document_id") or "").strip()
        filename = str(payload.get("filename") or "").strip()
        if not document_id and not filename:
            return

        occurred_at = (
            payload.get("uploaded_at")
            or payload.get("locked_at")
            or payload.get("updated_at")
            or payload.get("deleted_at")
            or payload.get("applied_at")
            or payload.get("released_at")
            or payload.get("accessed_at")
            or payload.get("archived_at")
            or payload.get("scanned_at")
            or event.occurred_at
        )

        await DocumentAuditTimelineRepository(db=db).append(
            {
                "source_event_id": event.event_id,
                "event_name": event.name,
                "occurred_at": str(occurred_at or ""),
                "actor_id": event.actor_id,
                "department_id": event.department_id,
                "document_id": document_id or filename,
                "filename": filename or document_id,
                "payload": payload,
            }
        )

    for event_name in _TIMELINE_EVENT_NAMES:
        event_bus.subscribe(event_name, _on_event)
