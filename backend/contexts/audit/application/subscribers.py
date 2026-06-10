from __future__ import annotations

from app_platform.event_bus.bus import EventBus
from app_platform.event_bus.types import BaseEvent, EventName
from contexts.audit.infrastructure.gateway import write_audit_entry


def register_audit_subscribers(*, event_bus: EventBus, db_provider) -> None:
    async def _on_event(event: BaseEvent) -> None:
        db = db_provider()
        if db is None:
            return
        payload = event.payload or {}
        action = {
            EventName.LEAVE_APPLIED.value: "LEAVE_APPLIED",
            EventName.LEAVE_APPROVED.value: "LEAVE_APPROVED",
            EventName.LEAVE_REJECTED.value: "LEAVE_REJECTED",
            EventName.DOCUMENT_UPLOADED.value: "DOCUMENT_UPLOADED",
            EventName.DOCUMENT_LOCKED.value: "DOCUMENT_LOCKED",
            EventName.DOCUMENT_METADATA_UPDATED.value: "DOCUMENT_METADATA_UPDATED",
            EventName.DOCUMENT_DELETED.value: "DOCUMENT_DELETED",
            EventName.CHANGE_REQUEST_SUBMITTED.value: "CHANGE_REQUEST_SUBMITTED",
            EventName.CHANGE_REQUEST_APPLIED.value: "CHANGE_REQUEST_APPLIED",
            EventName.CHANGE_REQUEST_REJECTED.value: "CHANGE_REQUEST_REJECTED",
            EventName.CHANGE_REQUEST_CANCELLED.value: "CHANGE_REQUEST_CANCELLED",
            EventName.EMPLOYEE_PROFILE_SUBMITTED.value: "EMPLOYEE_PROFILE_SUBMITTED",
            EventName.EMPLOYEE_PROFILE_VERIFIED.value: "EMPLOYEE_PROFILE_VERIFIED",
            EventName.EMPLOYEE_PROFILE_APPROVED.value: "EMPLOYEE_PROFILE_APPROVED",
            EventName.EMPLOYEE_PROFILE_REJECTED.value: "EMPLOYEE_PROFILE_REJECTED",
            EventName.EMPLOYEE_PROFILE_LOCKED.value: "EMPLOYEE_PROFILE_LOCKED",
            EventName.SERVICE_BOOK_ENTRY_CREATED.value: "SERVICE_BOOK_ENTRY_CREATED",
            EventName.SERVICE_BOOK_ENTRY_SAVED.value: "SERVICE_BOOK_ENTRY_SAVED",
            EventName.SERVICE_BOOK_ENTRY_SUBMITTED.value: "SERVICE_BOOK_ENTRY_SUBMITTED",
            EventName.SERVICE_BOOK_ENTRY_VERIFIED.value: "SERVICE_BOOK_ENTRY_VERIFIED",
            EventName.SERVICE_BOOK_ENTRY_APPROVED.value: "SERVICE_BOOK_ENTRY_APPROVED",
            EventName.SERVICE_BOOK_ENTRY_LOCKED.value: "SERVICE_BOOK_ENTRY_LOCKED",
            EventName.SERVICE_BOOK_ENTRY_SUPERSEDED.value: "SERVICE_BOOK_ENTRY_SUPERSEDED",
        }.get(event.name, event.name)

        if event.name.startswith("Document"):
            resource_type = "document"
            resource_id = payload.get("document_id") or payload.get("filename") or "unknown"
        elif event.name.startswith("ChangeRequest"):
            resource_type = "change_request"
            resource_id = payload.get("request_id") or "unknown"
        elif event.name.startswith("EmployeeProfile"):
            resource_type = "employee_profile"
            resource_id = payload.get("employee_id") or "unknown"
        elif event.name.startswith("ServiceBook"):
            resource_type = "servicebook_entry"
            resource_id = (
                payload.get("entry_id") or payload.get("source_entry_id") or "unknown"
            )
        else:
            resource_type = "leave_application"
            resource_id = payload.get("leave_id") or "unknown"

        await write_audit_entry(
            db,
            user_id=event.actor_id or "system",
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details={
                "event_id": event.event_id,
                "department_id": event.department_id,
                "payload": payload,
            },
            source_event_id=event.event_id,
        )

    event_bus.subscribe(EventName.LEAVE_APPLIED.value, _on_event)
    event_bus.subscribe(EventName.LEAVE_APPROVED.value, _on_event)
    event_bus.subscribe(EventName.LEAVE_REJECTED.value, _on_event)
    event_bus.subscribe(EventName.DOCUMENT_UPLOADED.value, _on_event)
    event_bus.subscribe(EventName.DOCUMENT_LOCKED.value, _on_event)
    event_bus.subscribe(EventName.DOCUMENT_METADATA_UPDATED.value, _on_event)
    event_bus.subscribe(EventName.DOCUMENT_DELETED.value, _on_event)
    event_bus.subscribe(EventName.CHANGE_REQUEST_SUBMITTED.value, _on_event)
    event_bus.subscribe(EventName.CHANGE_REQUEST_APPLIED.value, _on_event)
    event_bus.subscribe(EventName.CHANGE_REQUEST_REJECTED.value, _on_event)
    event_bus.subscribe(EventName.CHANGE_REQUEST_CANCELLED.value, _on_event)
    event_bus.subscribe(EventName.EMPLOYEE_PROFILE_SUBMITTED.value, _on_event)
    event_bus.subscribe(EventName.EMPLOYEE_PROFILE_VERIFIED.value, _on_event)
    event_bus.subscribe(EventName.EMPLOYEE_PROFILE_APPROVED.value, _on_event)
    event_bus.subscribe(EventName.EMPLOYEE_PROFILE_REJECTED.value, _on_event)
    event_bus.subscribe(EventName.EMPLOYEE_PROFILE_LOCKED.value, _on_event)
    event_bus.subscribe(EventName.SERVICE_BOOK_ENTRY_CREATED.value, _on_event)
    event_bus.subscribe(EventName.SERVICE_BOOK_ENTRY_SAVED.value, _on_event)
    event_bus.subscribe(EventName.SERVICE_BOOK_ENTRY_SUBMITTED.value, _on_event)
    event_bus.subscribe(EventName.SERVICE_BOOK_ENTRY_VERIFIED.value, _on_event)
    event_bus.subscribe(EventName.SERVICE_BOOK_ENTRY_APPROVED.value, _on_event)
    event_bus.subscribe(EventName.SERVICE_BOOK_ENTRY_LOCKED.value, _on_event)
    event_bus.subscribe(EventName.SERVICE_BOOK_ENTRY_SUPERSEDED.value, _on_event)
