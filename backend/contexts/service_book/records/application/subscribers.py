from __future__ import annotations

from app_platform.event_bus.bus import EventBus
from app_platform.event_bus.types import BaseEvent, EventName
from contexts.service_book.records.application.factory import (
    build_service_event_application_service,
)


def register_service_event_subscribers(*, event_bus: EventBus, db_provider, outbox_provider=None) -> None:
    async def _on_employee_created(event: BaseEvent) -> None:
        db = db_provider()
        if db is None:
            return
        payload = event.payload or {}
        employee_id = payload.get("employee_id")
        if not employee_id:
            return
        service = build_service_event_application_service(
            db=db,
            outbox_repo=outbox_provider() if outbox_provider is not None else None,
        )
        await service.initialize_stream(employee_id=employee_id)

    event_bus.subscribe(EventName.EMPLOYEE_CREATED.value, _on_employee_created)
