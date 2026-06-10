from __future__ import annotations

from app_platform.event_bus.types import EventName
from contexts.service_book.records.application.commands.approve_event import (
    ApproveServiceEventCommand,
    LockServiceEventCommand,
)
from contexts.service_book.records.application.handlers._shared import (
    ServiceEventsHandlerContext,
    validated_payload,
)
from contexts.service_book.records.application.services.event_publisher import (
    ServiceEventsEventPublisher,
)
from contexts.service_book.records.application.service_summary_projection import (
    EmployeeServiceSummaryProjectionService,
)
from contexts.service_book.records.domain.value_objects import ServiceRecordStatus
from shared_kernel.events import utc_now_iso


class ApproveEventHandler:
    def __init__(
        self,
        *,
        context: ServiceEventsHandlerContext,
        event_publisher: ServiceEventsEventPublisher,
        service_summary_projection: EmployeeServiceSummaryProjectionService | None = None,
    ) -> None:
        self._context = context
        self._event_publisher = event_publisher
        self._service_summary_projection = service_summary_projection

    async def handle(self, *, command: ApproveServiceEventCommand, actor_id: str | None) -> dict:
        payload = validated_payload(name="ApproveServiceEvent", command=command)
        result = await self._transition(
            service_event_id=payload["service_event_id"],
            target_status=ServiceRecordStatus.APPROVED,
            event_name=EventName.SERVICE_EVENT_APPROVED.value,
            actor_id=actor_id,
        )
        return result

    async def lock(self, *, command: LockServiceEventCommand, actor_id: str | None) -> dict:
        payload = validated_payload(name="LockServiceEvent", command=command)
        return await self._transition(
            service_event_id=payload["service_event_id"],
            target_status=ServiceRecordStatus.LOCKED,
            event_name=EventName.SERVICE_EVENT_LOCKED.value,
            actor_id=actor_id,
        )

    async def _transition(
        self,
        *,
        service_event_id: str,
        target_status: ServiceRecordStatus,
        event_name: str,
        actor_id: str | None,
    ) -> dict:
        stream = await self._context.load_stream_by_event_id(service_event_id=service_event_id)
        now = utc_now_iso()
        service_event = stream.transition_event_status(
            service_event_id=service_event_id,
            target_status=target_status,
            actor_id=actor_id,
            timestamp=now,
        )
        result = {
            "service_event_id": service_event.service_event_id,
            "employee_id": stream.employee_id,
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
            "effective_date": (
                service_event.date_range.effective_from.isoformat()
                if service_event.date_range.effective_from
                else None
            ),
            "order_number": service_event.order_number,
            "order_date": service_event.order_date,
            "issuing_authority": service_event.issuing_authority,
            "approved_at": service_event.approved_at,
            "approved_by": service_event.approved_by,
            "version": service_event.version,
            "payload": service_event.payload,
        }
        async def _operation(session):
            await self._context.persist_stream(stream=stream, session=session)
            await self._event_publisher.publish(
                name=event_name,
                payload={"event_version": 1, **result},
                actor_id=actor_id,
                session=session,
            )
            return result

        result = await self._context.run_atomic(_operation)
        if target_status == ServiceRecordStatus.LOCKED and self._service_summary_projection is not None:
            projected = await self._service_summary_projection.project_posted_record(
                service_record=result,
            )
            if projected is not None:
                result["employee_service_summary"] = projected
        return result
