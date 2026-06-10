from __future__ import annotations

import pytest

from contexts.service_book.records.domain.aggregate import ServiceRecordStream
from contexts.service_book.records.domain.value_objects import ServiceRecordType, ServiceRecordStatus


def test_service_event_stream_record_correct_void_and_attach() -> None:
    stream = ServiceRecordStream(employee_id="EMP-42")

    recorded = stream.record_event(
        service_event_id="SE-1",
        event_type=ServiceRecordType.PROMOTION,
        payload={"to_post": "Senior Clerk"},
        effective_from=None,
        effective_to=None,
        part_code="VI",
        source_ref=None,
        actor_id="user-1",
        timestamp="2026-03-04T10:00:00Z",
    )
    assert recorded.service_event_id == "SE-1"
    assert recorded.event_type is ServiceRecordType.PROMOTION

    corrected = stream.correct_event(
        service_event_id="SE-1",
        corrected_payload={"to_post": "Assistant"},
        reason="order-rectification",
        actor_id="user-2",
        timestamp="2026-03-04T10:10:00Z",
    )
    assert corrected.payload["to_post"] == "Assistant"
    assert len(corrected.revisions) == 1
    assert corrected.revisions[0].reason == "order-rectification"

    submitted = stream.transition_event_status(
        service_event_id="SE-1",
        target_status=ServiceRecordStatus.SUBMITTED,
        actor_id="user-2",
        timestamp="2026-03-04T10:11:00Z",
    )
    assert submitted.status is ServiceRecordStatus.SUBMITTED

    verified = stream.transition_event_status(
        service_event_id="SE-1",
        target_status=ServiceRecordStatus.VERIFIED,
        actor_id="user-3",
        timestamp="2026-03-04T10:12:00Z",
    )
    assert verified.status is ServiceRecordStatus.VERIFIED

    attached = stream.attach_document(
        service_event_id="SE-1",
        document_id="DOC-1",
        document_type="ORDER",
        actor_id="user-3",
        timestamp="2026-03-04T10:12:30Z",
    )
    assert len(attached.documents) == 1
    assert attached.documents[0]["document_id"] == "DOC-1"

    approved = stream.transition_event_status(
        service_event_id="SE-1",
        target_status=ServiceRecordStatus.APPROVED,
        actor_id="user-4",
        timestamp="2026-03-04T10:13:00Z",
    )
    assert approved.status is ServiceRecordStatus.APPROVED


def test_service_event_stream_can_void_preapproval_event() -> None:
    stream = ServiceRecordStream(employee_id="EMP-43")
    stream.record_event(
        service_event_id="SE-VOID-PREAPPROVAL",
        event_type=ServiceRecordType.PROMOTION,
        payload={"to_post": "Assistant"},
        effective_from=None,
        effective_to=None,
        part_code="VI",
        source_ref=None,
        actor_id="user-1",
        timestamp="2026-03-04T10:00:00Z",
    )

    voided = stream.void_event(
        service_event_id="SE-VOID-PREAPPROVAL",
        reason="superseded-order",
        actor_id="user-4",
        timestamp="2026-03-04T10:20:00Z",
    )
    assert voided.is_voided is True
    assert voided.void_reason == "superseded-order"
    assert voided.status is ServiceRecordStatus.VOIDED


def test_service_event_stream_cannot_correct_voided_event() -> None:
    stream = ServiceRecordStream(employee_id="EMP-99")
    stream.record_event(
        service_event_id="SE-VOID",
        event_type=ServiceRecordType.GENERIC,
        payload={"reason": "seed"},
        effective_from=None,
        effective_to=None,
        part_code=None,
        source_ref=None,
        actor_id="user-1",
        timestamp="2026-03-04T11:00:00Z",
    )
    stream.void_event(
        service_event_id="SE-VOID",
        reason="invalid",
        actor_id="user-1",
        timestamp="2026-03-04T11:05:00Z",
    )

    with pytest.raises(Exception):
        stream.correct_event(
            service_event_id="SE-VOID",
            corrected_payload={"x": 1},
            reason="retry",
            actor_id="user-1",
            timestamp="2026-03-04T11:06:00Z",
        )


def test_approved_service_event_payload_is_immutable() -> None:
    stream = ServiceRecordStream(employee_id="EMP-101")
    stream.record_event(
        service_event_id="SE-APPROVED",
        event_type=ServiceRecordType.TRANSFER,
        payload={"order_number": "ORD-1"},
        effective_from=None,
        effective_to=None,
        part_code="IV",
        source_ref=None,
        actor_id="creator",
        timestamp="2026-03-04T12:00:00Z",
    )
    stream.transition_event_status(
        service_event_id="SE-APPROVED",
        target_status=ServiceRecordStatus.SUBMITTED,
        actor_id="creator",
        timestamp="2026-03-04T12:01:00Z",
    )
    stream.transition_event_status(
        service_event_id="SE-APPROVED",
        target_status=ServiceRecordStatus.VERIFIED,
        actor_id="verifier",
        timestamp="2026-03-04T12:02:00Z",
    )
    stream.transition_event_status(
        service_event_id="SE-APPROVED",
        target_status=ServiceRecordStatus.APPROVED,
        actor_id="approver",
        timestamp="2026-03-04T12:03:00Z",
    )

    with pytest.raises(Exception, match="immutable"):
        stream.correct_event(
            service_event_id="SE-APPROVED",
            corrected_payload={"order_number": "ORD-2"},
            reason="late correction",
            actor_id="approver",
            timestamp="2026-03-04T12:04:00Z",
        )

    with pytest.raises(Exception, match="immutable"):
        stream.void_event(
            service_event_id="SE-APPROVED",
            reason="replace event",
            actor_id="approver",
            timestamp="2026-03-04T12:05:00Z",
        )

    with pytest.raises(Exception, match="locked"):
        stream.attach_document(
            service_event_id="SE-APPROVED",
            document_id="DOC-2",
            document_type="ORDER",
            actor_id="approver",
            timestamp="2026-03-04T12:06:00Z",
        )


def test_verifier_cannot_approve_same_service_event() -> None:
    stream = ServiceRecordStream(employee_id="EMP-102")
    stream.record_event(
        service_event_id="SE-VERIFY",
        event_type=ServiceRecordType.CONFIRMATION,
        payload={"order_number": "ORD-2"},
        effective_from=None,
        effective_to=None,
        part_code="IV",
        source_ref=None,
        actor_id="creator",
        timestamp="2026-03-04T13:00:00Z",
    )
    stream.transition_event_status(
        service_event_id="SE-VERIFY",
        target_status=ServiceRecordStatus.SUBMITTED,
        actor_id="creator",
        timestamp="2026-03-04T13:01:00Z",
    )
    stream.transition_event_status(
        service_event_id="SE-VERIFY",
        target_status=ServiceRecordStatus.VERIFIED,
        actor_id="same-user",
        timestamp="2026-03-04T13:02:00Z",
    )

    with pytest.raises(Exception, match="Verifier and approving authority"):
        stream.transition_event_status(
            service_event_id="SE-VERIFY",
            target_status=ServiceRecordStatus.APPROVED,
            actor_id="same-user",
            timestamp="2026-03-04T13:03:00Z",
        )


def test_recorded_service_events_have_hash_chain_and_envelope_metadata() -> None:
    stream = ServiceRecordStream(employee_id="EMP-HASH")
    first = stream.record_event(
        service_event_id="SE-HASH-1",
        event_type=ServiceRecordType.APPOINTMENT_RECORDED,
        payload={"order_number": "ORD-1"},
        effective_from=None,
        effective_to=None,
        part_code="II-A",
        source_ref=None,
        actor_id="creator",
        timestamp="2026-03-04T14:00:00Z",
        correlation_id="corr-1",
        causation_id="cmd-1",
    )
    second = stream.record_event(
        service_event_id="SE-HASH-2",
        event_type=ServiceRecordType.JOINING_RECORDED,
        payload={"joining_report": "JR-1"},
        effective_from=None,
        effective_to=None,
        part_code="II-A",
        source_ref=None,
        actor_id="creator",
        timestamp="2026-03-04T14:05:00Z",
        correlation_id="corr-1",
        causation_id="SE-HASH-1",
    )

    assert first.aggregate_id == "EMP-HASH"
    assert first.recorded_at == "2026-03-04T14:00:00Z"
    assert first.recorded_by == "creator"
    assert first.source_context == "service_book.records"
    assert first.correlation_id == "corr-1"
    assert first.causation_id == "cmd-1"
    assert first.previous_hash is None
    assert first.event_hash
    assert second.previous_hash == first.event_hash
    assert second.event_hash != first.event_hash


def test_service_event_payload_is_required() -> None:
    stream = ServiceRecordStream(employee_id="EMP-EMPTY")

    with pytest.raises(Exception, match="payload is required"):
        stream.record_event(
            service_event_id="SE-EMPTY",
            event_type=ServiceRecordType.GENERIC,
            payload={},
            effective_from=None,
            effective_to=None,
            part_code=None,
            source_ref=None,
            actor_id="creator",
            timestamp="2026-03-04T15:00:00Z",
        )
