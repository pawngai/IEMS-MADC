from datetime import date

from contexts.service_book.records.domain.aggregate import ServiceRecordStream
from contexts.service_book.records.domain.entities import ServiceRecord
from contexts.service_book.records.domain.value_objects import EffectiveDateRange, ServiceRecordType
from contexts.service_book.records.infrastructure.stream_mapper import stream_to_document, to_stream


def test_to_stream_maps_legacy_allowance_event_type_to_promotion() -> None:
    stream = to_stream(
        {
            "employee_id": "EMP-100",
            "events": [
                {
                    "service_event_id": "SE-1",
                    "event_type": "ALLOWANCE",
                    "payload": {"grant_date": "2026-03-14"},
                    "status": "DRAFT",
                }
            ],
        },
        employee_id="EMP-100",
    )

    assert stream.events[0].event_type.value == "PROMOTION"


def test_stream_to_document_serializes_effective_dates_to_iso_strings() -> None:
    stream = ServiceRecordStream(
        employee_id="EMP-100",
        events=[
            ServiceRecord(
                service_event_id="SE-1",
                employee_id="EMP-100",
                event_type=ServiceRecordType.SUSPENSION,
                payload={"reason": "test"},
                date_range=EffectiveDateRange(
                    effective_from=date(2026, 3, 15),
                    effective_to=date(2026, 3, 20),
                ),
                part_code="IV",
            )
        ],
    )

    document = stream_to_document(stream)

    assert document["events"][0]["date_range"] == {
        "effective_from": "2026-03-15",
        "effective_to": "2026-03-20",
    }


def test_stream_mapper_preserves_canonical_order_metadata() -> None:
    stream = ServiceRecordStream(employee_id="EMP-101")
    stream.record_event(
        service_event_id="SE-ORDER",
        event_type=ServiceRecordType.PAY_FIXATION,
        payload={"basic_pay": 56100},
        effective_from=date(2026, 4, 1),
        effective_to=None,
        part_code="IV",
        source_ref=None,
        actor_id="creator",
        timestamp="2026-04-01T10:00:00Z",
        order_number="PAY/2026/7",
        order_date="2026-03-30",
        issuing_authority="Commissioner",
    )

    document = stream_to_document(stream)
    event_doc = document["events"][0]

    assert event_doc["order_number"] == "PAY/2026/7"
    assert event_doc["order_date"] == "2026-03-30"
    assert event_doc["issuing_authority"] == "Commissioner"
    assert event_doc["version"] == 1

    restored = to_stream(document, employee_id="EMP-101")
    restored_event = restored.events[0]
    assert restored_event.order_number == "PAY/2026/7"
    assert restored_event.order_date == "2026-03-30"
    assert restored_event.issuing_authority == "Commissioner"


def test_stream_mapper_preserves_event_envelope_hash_fields() -> None:
    stream = ServiceRecordStream(employee_id="EMP-102")
    stream.record_event(
        service_event_id="SE-HASH",
        event_type=ServiceRecordType.TRANSFER_RECORDED,
        payload={"station": "Nagpur"},
        effective_from=date(2026, 5, 1),
        effective_to=None,
        part_code="IV",
        source_ref=None,
        actor_id="creator",
        timestamp="2026-04-20T10:00:00Z",
        correlation_id="corr-102",
        causation_id="cmd-102",
    )

    document = stream_to_document(stream)
    event_doc = document["events"][0]
    assert event_doc["aggregate_id"] == "EMP-102"
    assert event_doc["occurred_at"] == "2026-04-20T10:00:00Z"
    assert event_doc["recorded_by"] == "creator"
    assert event_doc["correlation_id"] == "corr-102"
    assert event_doc["causation_id"] == "cmd-102"
    assert event_doc["event_hash"]

    restored = to_stream(document, employee_id="EMP-102")
    assert restored.events[0].event_hash == event_doc["event_hash"]
    assert restored.events[0].event_version == 1
