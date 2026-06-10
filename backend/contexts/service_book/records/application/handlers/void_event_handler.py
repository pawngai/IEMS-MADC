from __future__ import annotations

from app_platform.event_bus.types import EventName
from contexts.service_book.records.application.commands.void_event import VoidServiceEventCommand
from contexts.service_book.records.application.handlers._shared import (
    ServiceEventsHandlerContext,
    validated_payload,
)
from contexts.service_book.records.application.services.event_publisher import (
    ServiceEventsEventPublisher,
)
from shared_kernel.events import utc_now_iso


class VoidEventHandler:
    def __init__(
        self,
        *,
        context: ServiceEventsHandlerContext,
        event_publisher: ServiceEventsEventPublisher,
    ) -> None:
        self._context = context
        self._event_publisher = event_publisher

    async def handle(self, *, command: VoidServiceEventCommand, actor_id: str | None) -> dict:
        payload = validated_payload(name="VoidServiceEvent", command=command)
        stream = await self._context.load_stream_by_event_id(
            service_event_id=payload["service_event_id"]
        )
        now = utc_now_iso()
        service_event = stream.void_event(
            service_event_id=payload["service_event_id"],
            reason=payload["reason"],
            actor_id=actor_id,
            timestamp=now,
        )
        result = {
            "service_event_id": service_event.service_event_id,
            "employee_id": stream.employee_id,
            "is_voided": True,
            "status": service_event.status.value,
            "reason": payload["reason"],
        }

        async def _operation(session):
            await self._context.persist_stream(stream=stream, session=session)
            await self._event_publisher.publish(
                name=EventName.SERVICE_EVENT_VOIDED.value,
                payload={
                    "event_version": 1,
                    "service_event_id": service_event.service_event_id,
                    "employee_id": stream.employee_id,
                    "reason": payload["reason"],
                    "status": service_event.status.value,
                },
                actor_id=actor_id,
                session=session,
            )
            return result

        return await self._context.run_atomic(_operation)
