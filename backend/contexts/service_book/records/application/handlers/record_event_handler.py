from __future__ import annotations

from app_platform.event_bus.types import EventName
from contexts.service_book.records.application.commands.record_event import (
    RecordServiceEventCommand,
)
from contexts.service_book.records.application.handlers._shared import (
    ServiceEventsHandlerContext,
    parse_date,
    validated_payload,
)
from contexts.service_book.records.application.service_summary_projection import (
    normalize_record_type,
    validate_service_record_payload,
)
from contexts.service_book.records.application.services.event_publisher import (
    ServiceEventsEventPublisher,
)
from contexts.service_book.records.domain.value_objects import ServiceRecordType, SourceRef
from shared_kernel.ids import new_id
from shared_kernel.events import get_request_id, utc_now_iso


class RecordEventHandler:
    def __init__(
        self,
        *,
        context: ServiceEventsHandlerContext,
        event_publisher: ServiceEventsEventPublisher,
    ) -> None:
        self._context = context
        self._event_publisher = event_publisher

    async def handle(
        self, *, command: RecordServiceEventCommand, actor_id: str | None
    ) -> dict:
        payload = validated_payload(name="RecordServiceEvent", command=command)
        record_type = normalize_record_type(
            payload.get("record_type"),
            event_type=payload.get("event_type"),
        )
        service_record_payload = dict(payload.get("payload") or {})
        for field_name in ("order_number", "order_date", "issuing_authority"):
            if payload.get(field_name) is not None:
                service_record_payload[field_name] = payload.get(field_name)
        if record_type:
            service_record_payload["record_type"] = record_type
        if payload.get("record_category"):
            service_record_payload["record_category"] = payload.get("record_category")
        if payload.get("document_ids"):
            service_record_payload["document_ids"] = payload.get("document_ids")
        service_record_payload = validate_service_record_payload(
            record_type=record_type,
            payload=service_record_payload,
        )
        stream = await self._context.load_stream_by_employee(
            employee_id=payload["employee_id"]
        )

        source_ref = None
        if payload.get("source_context") and payload.get("source_reference_id"):
            source_ref = SourceRef(
                context=payload["source_context"],
                reference_id=payload["source_reference_id"],
                revision=payload.get("source_revision"),
            )

        now = utc_now_iso()
        correlation_id = payload.get("correlation_id") or get_request_id()
        service_event = stream.record_event(
            service_event_id=new_id(),
            event_type=ServiceRecordType(payload["event_type"]),
            payload=service_record_payload,
            effective_from=parse_date(payload.get("effective_from")),
            effective_to=parse_date(payload.get("effective_to")),
            part_code=payload.get("part_code"),
            source_ref=source_ref,
            actor_id=actor_id,
            timestamp=now,
            order_number=payload.get("order_number"),
            order_date=payload.get("order_date"),
            issuing_authority=payload.get("issuing_authority"),
            correlation_id=correlation_id,
            causation_id=payload.get("causation_id"),
        )
        result = {
            "employee_id": stream.employee_id,
            "service_event_id": service_event.service_event_id,
            "aggregate_id": service_event.aggregate_id,
            "event_type": service_event.event_type.value,
            "event_version": service_event.event_version,
            "part_code": service_event.part_code,
            "status": service_event.status.value,
            "occurred_at": service_event.occurred_at,
            "recorded_at": service_event.recorded_at,
            "recorded_by": service_event.recorded_by,
            "source_context": service_event.source_context,
            "correlation_id": service_event.correlation_id,
            "causation_id": service_event.causation_id,
            "previous_hash": service_event.previous_hash,
            "event_hash": service_event.event_hash,
            "order_number": service_event.order_number,
            "order_date": service_event.order_date,
            "issuing_authority": service_event.issuing_authority,
            "version": service_event.version,
            "payload": service_event.payload,
            "effective_from": payload.get("effective_from"),
            "effective_to": payload.get("effective_to"),
        }

        async def _operation(session):
            await self._context.persist_stream(stream=stream, session=session)
            await self._event_publisher.publish(
                name=EventName.SERVICE_EVENT_RECORDED.value,
                payload={
                    "event_version": 1,
                    "service_event_id": service_event.service_event_id,
                    "employee_id": stream.employee_id,
                    "aggregate_id": service_event.aggregate_id,
                    "event_type": service_event.event_type.value,
                    "part_code": service_event.part_code,
                    "occurred_at": service_event.occurred_at,
                    "recorded_at": service_event.recorded_at,
                    "recorded_by": service_event.recorded_by,
                    "source_context": service_event.source_context,
                    "correlation_id": service_event.correlation_id,
                    "causation_id": service_event.causation_id,
                    "previous_hash": service_event.previous_hash,
                    "event_hash": service_event.event_hash,
                    "order_number": service_event.order_number,
                    "order_date": service_event.order_date,
                    "issuing_authority": service_event.issuing_authority,
                    "effective_from": payload.get("effective_from"),
                    "effective_to": payload.get("effective_to"),
                    "payload": service_event.payload,
                    "status": service_event.status.value,
                    "version": service_event.version,
                    "source_ref": (
                        {
                            "context": source_ref.context,
                            "reference_id": source_ref.reference_id,
                            "revision": source_ref.revision,
                        }
                        if source_ref is not None
                        else None
                    ),
                },
                actor_id=actor_id,
                session=session,
            )
            return result

        return await self._context.run_atomic(_operation)
