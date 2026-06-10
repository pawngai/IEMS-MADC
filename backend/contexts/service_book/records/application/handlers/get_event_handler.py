from __future__ import annotations

from contexts.service_book.records.application.queries.get_event import GetServiceEventQuery
from contexts.service_book.records.repository.service_record_repository import ServiceRecordRepository


class GetEventHandler:
    def __init__(self, *, repository: ServiceRecordRepository) -> None:
        self._repository = repository

    async def handle(self, *, query: GetServiceEventQuery) -> dict | None:
        event = await self._repository.get_event(service_event_id=query.service_event_id)
        if event is None:
            return None
        if not query.include_employee_id:
            event.pop("employee_id", None)
        return event
