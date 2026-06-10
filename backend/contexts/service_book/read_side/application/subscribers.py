from __future__ import annotations

from app_platform.event_bus.bus import EventBus
from app_platform.event_bus.types import BaseEvent, EventName
from contexts.service_book.read_side.application.projectors.project_ledger_entry_approved import (
    project_ledger_entry_approved,
)
from contexts.service_book.read_side.application.projectors.project_service_event_corrected import (
    project_service_event_corrected,
)
from contexts.service_book.read_side.application.projectors.project_approved_service_event import (
    project_approved_service_event,
)
from contexts.service_book.repository.read_repository import ServiceBookReadRepository


def register_service_book_subscribers(*, event_bus: EventBus, db_provider) -> None:
    async def _dispatch(event: BaseEvent) -> None:
        db = db_provider()
        if db is None:
            return
        repo = ServiceBookReadRepository(db=db)
        payload = event.payload or {}
        source_event_id = getattr(event, "event_id", None)

        if event.name == EventName.SERVICE_EVENT_APPROVED.value:
            await project_approved_service_event(repo=repo, payload=payload, event_name=event.name, source_event_id=source_event_id)
        elif event.name in {
            EventName.SERVICE_EVENT_CORRECTED.value,
            EventName.SERVICE_EVENT_VOIDED.value,
            EventName.LEAVE_APPROVED.value,
            EventName.LEAVE_CANCELLED.value,
            EventName.PAY_REVISED.value,
            EventName.ALLOWANCE_CHANGED.value,
        }:
            await project_service_event_corrected(repo=repo, payload=payload, event_name=event.name, source_event_id=source_event_id)
        elif event.name in {EventName.SERVICE_BOOK_ENTRY_APPROVED.value, EventName.SERVICE_BOOK_ENTRY_LOCKED.value}:
            await project_ledger_entry_approved(repo=repo, payload=payload, event_name=event.name, source_event_id=source_event_id)

    event_bus.subscribe(EventName.SERVICE_EVENT_APPROVED.value, _dispatch)
    event_bus.subscribe(EventName.SERVICE_EVENT_CORRECTED.value, _dispatch)
    event_bus.subscribe(EventName.SERVICE_EVENT_VOIDED.value, _dispatch)
    event_bus.subscribe(EventName.LEAVE_APPROVED.value, _dispatch)
    event_bus.subscribe(EventName.LEAVE_CANCELLED.value, _dispatch)
    event_bus.subscribe(EventName.PAY_REVISED.value, _dispatch)
    event_bus.subscribe(EventName.ALLOWANCE_CHANGED.value, _dispatch)
    event_bus.subscribe(EventName.SERVICE_BOOK_ENTRY_APPROVED.value, _dispatch)
    event_bus.subscribe(EventName.SERVICE_BOOK_ENTRY_LOCKED.value, _dispatch)


