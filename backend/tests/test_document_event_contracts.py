from __future__ import annotations

import app_platform.contracts.events  # noqa: F401

from app_platform.contracts.registry import validate_event_payload
from app_platform.event_bus.types import EventName


def test_document_uploaded_contract_validates_payload() -> None:
    payload = validate_event_payload(
        name=EventName.DOCUMENT_UPLOADED.value,
        version="v1",
        payload={
            "event_version": 1,
            "document_id": "doc-1",
            "filename": "doc-1.pdf",
            "original_name": "appointment-order.pdf",
            "content_type": "application/pdf",
            "file_size": 1024,
            "uploaded_at": "2026-04-09T10:00:00+00:00",
            "uploaded_by_user_id": "user-1",
            "uploaded_employee_id": "EMP-001",
            "uploaded_employee_code": "MADC-2024-0001",
            "subject_employee_id": "EMP-002",
            "subject_employee_code": "MADC-2024-0002",
            "entity_type": "CHANGE_REQUEST",
            "entity_id": "CR-1",
            "document_type": "ORDER",
            "category": "APPOINTMENT_ORDER",
            "source_context": "change_requests.upload",
            "version_number": 2,
            "is_current": True,
            "supersedes_document_id": "doc-0",
        },
    )

    assert payload["document_id"] == "doc-1"
    assert payload["entity_type"] == "CHANGE_REQUEST"
    assert payload["document_type"] == "ORDER"
    assert payload["category"] == "APPOINTMENT_ORDER"
    assert payload["version_number"] == 2


def test_document_locked_contract_validates_payload() -> None:
    payload = validate_event_payload(
        name=EventName.DOCUMENT_LOCKED.value,
        version="v1",
        payload={
            "event_version": 1,
            "document_id": "doc-1",
            "filename": "doc-1.pdf",
            "locked_at": "2026-04-09T10:05:00+00:00",
            "lock_reason": "APPROVED_CHANGE_REQUEST",
            "locked_by_request_id": "CR-1",
            "locked_status": "APPROVED",
            "uploaded_employee_id": "EMP-001",
            "uploaded_employee_code": "MADC-2024-0001",
            "subject_employee_id": "EMP-002",
            "subject_employee_code": "MADC-2024-0002",
            "document_type": "ORDER",
            "category": "APPOINTMENT_ORDER",
            "source_context": "change_requests.review",
            "version_number": 2,
            "is_current": True,
            "supersedes_document_id": "doc-0",
        },
    )

    assert payload["lock_reason"] == "APPROVED_CHANGE_REQUEST"
    assert payload["locked_by_request_id"] == "CR-1"
    assert payload["source_context"] == "change_requests.review"
    assert payload["category"] == "APPOINTMENT_ORDER"


def test_document_metadata_updated_contract_validates_payload() -> None:
    payload = validate_event_payload(
        name=EventName.DOCUMENT_METADATA_UPDATED.value,
        version="v1",
        payload={
            "event_version": 1,
            "document_id": "doc-1",
            "filename": "doc-1.pdf",
            "updated_at": "2026-04-09T10:02:00+00:00",
            "updated_by_user_id": "user-1",
            "uploaded_employee_id": "EMP-001",
            "uploaded_employee_code": "MADC-2024-0001",
            "subject_employee_id": "EMP-002",
            "subject_employee_code": "MADC-2024-0002",
            "entity_type": "CHANGE_REQUEST",
            "entity_id": "CR-1",
            "document_type": "ORDER",
            "category": "APPOINTMENT_ORDER",
            "source_context": "change_requests.upload",
            "updated_fields": ["document_type", "entity_id", "entity_type", "source_context"],
            "version_number": 2,
            "is_current": False,
            "supersedes_document_id": "doc-0",
        },
    )

    assert payload["document_id"] == "doc-1"
    assert payload["updated_fields"] == ["document_type", "entity_id", "entity_type", "source_context"]
    assert payload["is_current"] is False


def test_document_deleted_contract_validates_payload() -> None:
    payload = validate_event_payload(
        name=EventName.DOCUMENT_DELETED.value,
        version="v1",
        payload={
            "event_version": 1,
            "document_id": "doc-1",
            "filename": "doc-1.pdf",
            "original_name": "appointment-order.pdf",
            "deleted_at": "2026-04-09T10:06:00+00:00",
            "deleted_by_user_id": "user-2",
            "uploaded_employee_id": "EMP-001",
            "uploaded_employee_code": "MADC-2024-0001",
            "subject_employee_id": "EMP-002",
            "subject_employee_code": "MADC-2024-0002",
            "document_type": "ORDER",
            "category": "APPOINTMENT_ORDER",
            "source_context": "change_requests.review",
            "version_number": 2,
            "is_current": False,
            "supersedes_document_id": "doc-0",
        },
    )

    assert payload["document_id"] == "doc-1"
    assert payload["deleted_by_user_id"] == "user-2"
    assert payload["document_type"] == "ORDER"
    assert payload["category"] == "APPOINTMENT_ORDER"