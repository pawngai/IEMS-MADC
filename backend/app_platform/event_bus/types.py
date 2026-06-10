from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from shared_kernel.ids import new_id
from shared_kernel.events import utc_now_iso


class EventName(str, Enum):
    DOCUMENT_UPLOADED = "DocumentUploaded"
    DOCUMENT_LOCKED = "DocumentLocked"
    DOCUMENT_METADATA_UPDATED = "DocumentMetadataUpdated"
    DOCUMENT_DELETED = "DocumentDeleted"
    DOCUMENT_LEGAL_HOLD_APPLIED = "DocumentLegalHoldApplied"
    DOCUMENT_LEGAL_HOLD_RELEASED = "DocumentLegalHoldReleased"
    DOCUMENT_ACCESSED = "DocumentAccessed"
    DOCUMENT_ARCHIVED = "DocumentArchived"
    DOCUMENT_SCAN_COMPLETED = "DocumentScanCompleted"
    DOCUMENT_EXPIRING_SOON = "DocumentExpiringSoon"
    DOCUMENT_EXPIRED = "DocumentExpired"
    EMPLOYEE_CREATED = "EmployeeCreated"
    EMPLOYEE_UPDATED = "EmployeeUpdated"
    EMPLOYEE_STATUS_CHANGED = "EmployeeStatusChanged"
    EMPLOYEE_PROMOTED = "EmployeePromoted"
    LEAVE_APPLIED = "LeaveApplied"
    LEAVE_RECOMMENDED = "LeaveRecommended"
    LEAVE_APPROVED = "LeaveApproved"
    LEAVE_REJECTED = "LeaveRejected"
    CHANGE_REQUEST_SUBMITTED = "ChangeRequestSubmitted"
    CHANGE_REQUEST_APPLIED = "ChangeRequestApplied"
    CHANGE_REQUEST_REJECTED = "ChangeRequestRejected"
    CHANGE_REQUEST_CANCELLED = "ChangeRequestCancelled"
    EMPLOYEE_PROFILE_SUBMITTED = "EmployeeProfileSubmitted"
    EMPLOYEE_PROFILE_VERIFIED = "EmployeeProfileVerified"
    EMPLOYEE_PROFILE_APPROVED = "EmployeeProfileApproved"
    EMPLOYEE_PROFILE_REJECTED = "EmployeeProfileRejected"
    EMPLOYEE_PROFILE_LOCKED = "EmployeeProfileLocked"
    SERVICE_BOOK_ENTRY_CREATED = "ServiceBookEntryCreated"
    SERVICE_BOOK_ENTRY_SAVED = "ServiceBookEntrySaved"
    SERVICE_BOOK_ENTRY_SUBMITTED = "ServiceBookEntrySubmitted"
    SERVICE_BOOK_ENTRY_VERIFIED = "ServiceBookEntryVerified"
    SERVICE_BOOK_ENTRY_APPROVED = "ServiceBookEntryApproved"
    SERVICE_BOOK_ENTRY_SUPERSEDED = "ServiceBookEntrySuperseded"
    SERVICE_BOOK_ENTRY_LOCKED = "ServiceBookEntryLocked"
    LEAVE_CANCELLED = "LeaveCancelled"
    PAY_REVISED = "PayRevised"
    ALLOWANCE_CHANGED = "AllowanceChanged"
    SERVICE_EVENT_RECORDED = "ServiceEventRecorded"
    SERVICE_EVENT_SUBMITTED = "ServiceEventLifecycleSubmitted"
    SERVICE_EVENT_VERIFIED = "ServiceEventLifecycleVerified"
    SERVICE_EVENT_APPROVED = "ServiceEventLifecycleApproved"
    SERVICE_EVENT_LOCKED = "ServiceEventLifecycleLocked"
    SERVICE_EVENT_CORRECTED = "ServiceEventCorrected"
    SERVICE_EVENT_VOIDED = "ServiceEventVoided"
    SERVICE_EVENT_DOCUMENT_ATTACHED = "ServiceEventDocumentAttached"
    EMPLOYEE_IDENTITY_SUBMITTED = "EmployeeIdentitySubmitted"
    EMPLOYEE_IDENTITY_CREATED = "EmployeeIdentityCreated"
    EMPLOYEE_IDENTITY_VERIFIED = "EmployeeIdentityVerified"
    EMPLOYEE_IDENTITY_ACTIVATED = "EmployeeIdentityActivated"
    EMPLOYEE_IDENTITY_REJECTED = "EmployeeIdentityRejected"


@dataclass(slots=True)
class BaseEvent:
    name: str
    payload: dict[str, Any]
    event_version: str = "v1"
    actor_id: str | None = None
    department_id: str | None = None
    correlation_id: str | None = None
    idempotency_key: str | None = None
    occurred_at: str = field(default_factory=utc_now_iso)
    event_id: str = field(default_factory=new_id)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def serialize_event(event: BaseEvent) -> dict[str, Any]:
    return event.to_dict()


def deserialize_event(data: dict[str, Any]) -> BaseEvent:
    return BaseEvent(
        event_id=data.get("event_id") or new_id(),
        name=data["name"],
        event_version=data.get("event_version") or "v1",
        occurred_at=data.get("occurred_at") or utc_now_iso(),
        actor_id=data.get("actor_id"),
        department_id=data.get("department_id"),
        correlation_id=data.get("correlation_id"),
        idempotency_key=data.get("idempotency_key"),
        payload=data.get("payload") or {},
    )
