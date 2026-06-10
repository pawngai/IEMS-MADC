from __future__ import annotations

from datetime import date

from contexts.service_book.records.domain.aggregate import ServiceRecordStream
from contexts.service_book.records.domain.entities import Revision, ServiceRecord
from contexts.service_book.records.domain.value_objects import (
    EffectiveDateRange,
    ServiceRecordType,
    ServiceRecordStatus,
    SourceRef,
)


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def serialize_date(value: date | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def status_from_value(value: str | None) -> ServiceRecordStatus:
    if not value:
        return ServiceRecordStatus.DRAFT
    return ServiceRecordStatus(str(value))


def event_type_from_value(value: str | None) -> ServiceRecordType:
    normalized = str(value or "").strip().upper()
    if not normalized:
        return ServiceRecordType.GENERIC
    if normalized == "ALLOWANCE":
        return ServiceRecordType.PROMOTION
    return ServiceRecordType(normalized)


def to_stream(record: dict | None, *, employee_id: str) -> ServiceRecordStream:
    if record is None:
        return ServiceRecordStream(employee_id=employee_id, events=[])

    events: list[ServiceRecord] = []
    for item in record.get("events") or []:
        events.append(
            ServiceRecord(
                service_event_id=item["service_event_id"],
                employee_id=record["employee_id"],
                event_type=event_type_from_value(item.get("event_type")),
                payload=item.get("payload") or {},
                date_range=EffectiveDateRange(
                    effective_from=parse_date(
                        (item.get("date_range") or {}).get("effective_from")
                        or item.get("effective_from")
                    ),
                    effective_to=parse_date(
                        (item.get("date_range") or {}).get("effective_to")
                        or item.get("effective_to")
                    ),
                ),
                aggregate_id=item.get("aggregate_id") or record["employee_id"],
                occurred_at=item.get("occurred_at") or item.get("created_at"),
                recorded_at=item.get("recorded_at") or item.get("created_at"),
                recorded_by=item.get("recorded_by") or item.get("created_by"),
                source_context=item.get("source_context")
                or ((item.get("source_ref") or {}).get("context") if isinstance(item.get("source_ref"), dict) else None)
                or "service_book.records",
                correlation_id=item.get("correlation_id"),
                causation_id=item.get("causation_id"),
                previous_hash=item.get("previous_hash"),
                event_hash=item.get("event_hash"),
                event_version=int(item.get("event_version") or item.get("version") or 1),
                order_number=item.get("order_number") or (item.get("payload") or {}).get("order_number"),
                order_date=item.get("order_date") or (item.get("payload") or {}).get("order_date"),
                issuing_authority=item.get("issuing_authority")
                or (item.get("payload") or {}).get("issuing_authority"),
                part_code=item.get("part_code"),
                source_ref=(
                    SourceRef(
                        context=item["source_ref"]["context"],
                        reference_id=item["source_ref"]["reference_id"],
                        revision=item["source_ref"].get("revision"),
                    )
                    if item.get("source_ref")
                    else None
                ),
                status=status_from_value(item.get("status")),
                is_voided=bool(item.get("is_voided")),
                void_reason=item.get("void_reason"),
                created_at=item.get("created_at"),
                created_by=item.get("created_by"),
                submitted_at=item.get("submitted_at"),
                submitted_by=item.get("submitted_by"),
                verified_at=item.get("verified_at"),
                verified_by=item.get("verified_by"),
                approved_at=item.get("approved_at"),
                approved_by=item.get("approved_by"),
                locked_at=item.get("locked_at"),
                locked_by=item.get("locked_by"),
                updated_at=item.get("updated_at"),
                updated_by=item.get("updated_by"),
                documents=item.get("documents") or [],
                revisions=[
                    Revision(
                        revision=int(revision.get("revision") or 1),
                        reason=revision.get("reason") or "",
                        actor_id=revision.get("actor_id"),
                        payload=revision.get("payload") or {},
                        corrected_at=revision.get("corrected_at") or "",
                    )
                    for revision in (item.get("revisions") or [])
                ],
                audit_metadata=item.get("audit_metadata") or {},
                version=int(item.get("version") or item.get("event_version") or 1),
            )
        )
    return ServiceRecordStream(employee_id=record["employee_id"], events=events)


def stream_to_document(stream: ServiceRecordStream) -> dict:
    items: list[dict] = []
    for service_event in stream.events:
        items.append(
            {
                "service_event_id": service_event.service_event_id,
                "event_type": service_event.event_type.value,
                "payload": service_event.payload,
                "aggregate_id": service_event.aggregate_id or stream.employee_id,
                "occurred_at": service_event.occurred_at or service_event.created_at,
                "recorded_at": service_event.recorded_at or service_event.created_at,
                "recorded_by": service_event.recorded_by or service_event.created_by,
                "source_context": service_event.source_context or (
                    service_event.source_ref.context if service_event.source_ref else "service_book.records"
                ),
                "correlation_id": service_event.correlation_id,
                "causation_id": service_event.causation_id,
                "previous_hash": service_event.previous_hash,
                "event_hash": service_event.event_hash,
                "event_version": service_event.event_version,
                "order_number": service_event.order_number,
                "order_date": service_event.order_date,
                "issuing_authority": service_event.issuing_authority,
                "date_range": {
                    "effective_from": serialize_date(service_event.date_range.effective_from),
                    "effective_to": serialize_date(service_event.date_range.effective_to),
                },
                "part_code": service_event.part_code,
                "source_ref": (
                    {
                        "context": service_event.source_ref.context,
                        "reference_id": service_event.source_ref.reference_id,
                        "revision": service_event.source_ref.revision,
                    }
                    if service_event.source_ref is not None
                    else None
                ),
                "status": service_event.status.value,
                "is_voided": service_event.is_voided,
                "void_reason": service_event.void_reason,
                "created_at": service_event.created_at,
                "created_by": service_event.created_by,
                "submitted_at": service_event.submitted_at,
                "submitted_by": service_event.submitted_by,
                "verified_at": service_event.verified_at,
                "verified_by": service_event.verified_by,
                "approved_at": service_event.approved_at,
                "approved_by": service_event.approved_by,
                "locked_at": service_event.locked_at,
                "locked_by": service_event.locked_by,
                "updated_at": service_event.updated_at,
                "updated_by": service_event.updated_by,
                "documents": service_event.documents,
                "revisions": [
                    {
                        "revision": revision.revision,
                        "reason": revision.reason,
                        "actor_id": revision.actor_id,
                        "payload": revision.payload,
                        "corrected_at": revision.corrected_at,
                    }
                    for revision in service_event.revisions
                ],
                "audit_metadata": service_event.audit_metadata,
                "version": service_event.version,
            }
        )
    return {"employee_id": stream.employee_id, "events": items}


def stream_to_api_document(stream: ServiceRecordStream) -> dict:
    document = stream_to_document(stream)
    api_events: list[dict] = []

    for item in document.get("events") or []:
        date_range = item.get("date_range") or {}
        source_ref = item.get("source_ref") or {}
        revisions = item.get("revisions") or []
        latest_revision = revisions[-1] if revisions else None
        api_events.append(
            {
                **item,
                "id": item.get("service_event_id"),
                "effective_from": date_range.get("effective_from"),
                "effective_to": date_range.get("effective_to"),
                "recorded_at": item.get("created_at"),
                "actor_id": item.get("created_by"),
                "source_context": source_ref.get("context"),
                "source_reference_id": source_ref.get("reference_id"),
                "source_revision": source_ref.get("revision"),
                "voided": bool(item.get("is_voided")),
                "corrected": bool(revisions),
                "correction_reason": (
                    latest_revision.get("reason")
                    if isinstance(latest_revision, dict)
                    else None
                ),
            }
        )

    return {"employee_id": document["employee_id"], "events": api_events}
