from __future__ import annotations

from contexts.service_book.records.infrastructure.stream_mapper import stream_to_api_document, to_stream
from contexts.service_book.records.application.queries.get_stream import GetServiceEventStreamQuery
from contexts.service_book.records.repository.service_record_repository import ServiceRecordRepository


class GetStreamHandler:
    def __init__(self, *, repository: ServiceRecordRepository) -> None:
        self._repository = repository

    async def handle(self, *, query: GetServiceEventStreamQuery) -> dict:
        stream_doc = await self._repository.get_stream(employee_id=query.employee_id)
        stream = to_stream(stream_doc, employee_id=query.employee_id)
        return stream_to_api_document(stream)
