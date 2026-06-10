"""Event contract registration.

This module wires bounded-context-owned event schemas into the platform event
registry. Schemas themselves are defined by their owning contexts:

- Employee identity events: ``contexts.employee_identity.contracts.events``
- Service-event payloads:    ``contexts.service_book.records.contracts.events``
- Document events:           ``contexts.documents.contracts.events``

Only domain-neutral primitives (e.g. ``LenientEventPayload``) live in
``app_platform.contracts.events.core_events``.
"""

from app_platform.contracts.events.core_events import LenientEventPayload
from app_platform.contracts.registry import register_event
from app_platform.event_bus.types import EventName
from contexts.documents.contracts.events import (
    DocumentAccessedPayload,
    DocumentArchivedPayload,
    DocumentDeletedPayload,
    DocumentExpiredPayload,
    DocumentExpiringSoonPayload,
    DocumentLegalHoldAppliedPayload,
    DocumentLegalHoldReleasedPayload,
    DocumentLockedPayload,
    DocumentMetadataUpdatedPayload,
    DocumentScanCompletedPayload,
    DocumentUploadedPayload,
)
from contexts.employee_identity.contracts.events import (
    EmployeeCreatedEvent,
    EmployeeIdentityCreatedEvent,
    EmployeePromotedEvent,
    EmployeeStatusChangedEvent,
    EmployeeUpdatedEvent,
)
from contexts.service_book.records.contracts.events import (
    ServiceEventCorrectedPayload,
    ServiceEventDocumentAttachedPayload,
    ServiceEventLifecyclePayload,
    ServiceEventRecordedPayload,
    ServiceEventVoidedPayload,
)


register_event(name=EventName.EMPLOYEE_CREATED.value, version="v1", schema=EmployeeCreatedEvent)
register_event(name=EventName.EMPLOYEE_IDENTITY_CREATED.value, version="v1", schema=EmployeeIdentityCreatedEvent)
register_event(name=EventName.EMPLOYEE_UPDATED.value, version="v1", schema=EmployeeUpdatedEvent)
register_event(
    name=EventName.EMPLOYEE_STATUS_CHANGED.value,
    version="v1",
    schema=EmployeeStatusChangedEvent,
)
register_event(name=EventName.EMPLOYEE_PROMOTED.value, version="v1", schema=EmployeePromotedEvent)
register_event(name=EventName.LEAVE_APPLIED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.LEAVE_RECOMMENDED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.LEAVE_APPROVED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.LEAVE_REJECTED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.CHANGE_REQUEST_SUBMITTED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.CHANGE_REQUEST_APPLIED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.CHANGE_REQUEST_REJECTED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.CHANGE_REQUEST_CANCELLED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.EMPLOYEE_PROFILE_SUBMITTED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.EMPLOYEE_PROFILE_VERIFIED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.EMPLOYEE_PROFILE_APPROVED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.EMPLOYEE_PROFILE_REJECTED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.EMPLOYEE_PROFILE_LOCKED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.SERVICE_BOOK_ENTRY_CREATED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.SERVICE_BOOK_ENTRY_SAVED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.SERVICE_BOOK_ENTRY_SUBMITTED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.SERVICE_BOOK_ENTRY_VERIFIED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.SERVICE_BOOK_ENTRY_APPROVED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.SERVICE_BOOK_ENTRY_SUPERSEDED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.SERVICE_BOOK_ENTRY_LOCKED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.SERVICE_EVENT_RECORDED.value, version="v1", schema=ServiceEventRecordedPayload)
register_event(name=EventName.SERVICE_EVENT_SUBMITTED.value, version="v1", schema=ServiceEventLifecyclePayload)
register_event(name=EventName.SERVICE_EVENT_VERIFIED.value, version="v1", schema=ServiceEventLifecyclePayload)
register_event(name=EventName.SERVICE_EVENT_APPROVED.value, version="v1", schema=ServiceEventLifecyclePayload)
register_event(name=EventName.SERVICE_EVENT_LOCKED.value, version="v1", schema=ServiceEventLifecyclePayload)
register_event(name=EventName.SERVICE_EVENT_CORRECTED.value, version="v1", schema=ServiceEventCorrectedPayload)
register_event(name=EventName.SERVICE_EVENT_VOIDED.value, version="v1", schema=ServiceEventVoidedPayload)
register_event(
    name=EventName.SERVICE_EVENT_DOCUMENT_ATTACHED.value,
    version="v1",
    schema=ServiceEventDocumentAttachedPayload,
)
register_event(name=EventName.LEAVE_CANCELLED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.PAY_REVISED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.ALLOWANCE_CHANGED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.DOCUMENT_UPLOADED.value, version="v1", schema=DocumentUploadedPayload)
register_event(name=EventName.DOCUMENT_LOCKED.value, version="v1", schema=DocumentLockedPayload)
register_event(name=EventName.DOCUMENT_METADATA_UPDATED.value, version="v1", schema=DocumentMetadataUpdatedPayload)
register_event(name=EventName.DOCUMENT_DELETED.value, version="v1", schema=DocumentDeletedPayload)
register_event(
    name=EventName.DOCUMENT_LEGAL_HOLD_APPLIED.value,
    version="v1",
    schema=DocumentLegalHoldAppliedPayload,
)
register_event(
    name=EventName.DOCUMENT_LEGAL_HOLD_RELEASED.value,
    version="v1",
    schema=DocumentLegalHoldReleasedPayload,
)
register_event(name=EventName.DOCUMENT_ACCESSED.value, version="v1", schema=DocumentAccessedPayload)
register_event(name=EventName.DOCUMENT_ARCHIVED.value, version="v1", schema=DocumentArchivedPayload)
register_event(name=EventName.DOCUMENT_SCAN_COMPLETED.value, version="v1", schema=DocumentScanCompletedPayload)
register_event(name=EventName.DOCUMENT_EXPIRING_SOON.value, version="v1", schema=DocumentExpiringSoonPayload)
register_event(name=EventName.DOCUMENT_EXPIRED.value, version="v1", schema=DocumentExpiredPayload)
register_event(name=EventName.EMPLOYEE_IDENTITY_SUBMITTED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.EMPLOYEE_IDENTITY_VERIFIED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.EMPLOYEE_IDENTITY_ACTIVATED.value, version="v1", schema=LenientEventPayload)
register_event(name=EventName.EMPLOYEE_IDENTITY_REJECTED.value, version="v1", schema=LenientEventPayload)

__all__ = ["LenientEventPayload"]
