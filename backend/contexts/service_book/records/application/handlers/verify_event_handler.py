from __future__ import annotations

from app_platform.event_bus.types import EventName
from contexts.service_book.records.application.commands.verify_event import VerifyServiceEventCommand
from contexts.service_book.records.application.handlers._shared import (
    ServiceEventsHandlerContext,
    validated_payload,
)
from contexts.service_book.records.application.services.event_publisher import (
    ServiceEventsEventPublisher,
)
from contexts.service_book.records.domain.value_objects import ServiceRecordStatus
from shared_kernel.events import utc_now_iso


class VerifyEventHandler:
    def __init__(
        self,
        *,
        context: ServiceEventsHandlerContext,
        event_publisher: ServiceEventsEventPublisher,
    ) -> None:
        self._context = context
        self._event_publisher = event_publisher

    async def handle(self, *, command: VerifyServiceEventCommand, actor_id: str | None) -> dict:
        payload = validated_payload(name="VerifyServiceEvent", command=command)
        stream = await self._context.load_stream_by_event_id(
            service_event_id=payload["service_event_id"]
        )
        now = utc_now_iso()
        service_event = stream.transition_event_status(
            service_event_id=payload["service_event_id"],
            target_status=ServiceRecordStatus.VERIFIED,
            actor_id=actor_id,
            timestamp=now,
        )
        result = {
            "service_event_id": service_event.service_event_id,
            "employee_id": stream.employee_id,
            "part_code": service_event.part_code,
            "status": service_event.status.value,
            "effective_date": (
                service_event.date_range.effective_from.isoformat()
                if service_event.date_range.effective_from
                else None
            ),
            "payload": service_event.payload,
        }
        async def _operation(session):
            await self._context.persist_stream(stream=stream, session=session)
            await self._event_publisher.publish(
                name=EventName.SERVICE_EVENT_VERIFIED.value,
                payload={"event_version": 1, **result},
                actor_id=actor_id,
                session=session,
            )
            return result

        return await self._context.run_atomic(_operation)
