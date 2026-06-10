from __future__ import annotations

from app_platform.contracts.registry import validate_command_payload
from app_platform.db.atomic import call_with_optional_session, run_atomic
from contexts.service_book.records.infrastructure.stream_mapper import (
    parse_date,
    stream_to_document,
    to_stream,
)
from contexts.service_book.records.repository.service_record_repository import ServiceRecordRepository


class ServiceEventsHandlerContext:
    def __init__(self, *, repository: ServiceRecordRepository) -> None:
        self.repository = repository

    async def load_stream_by_employee(self, *, employee_id: str):
        return to_stream(
            await self.repository.get_stream(employee_id),
            employee_id=employee_id,
        )

    async def load_stream_by_event_id(self, *, service_event_id: str):
        stream_doc = await self.repository.find_stream_by_event_id(
            service_event_id=service_event_id
        )
        if stream_doc is None:
            raise ValueError("Service event not found")
        return to_stream(stream_doc, employee_id=stream_doc["employee_id"])

    async def persist_stream(self, *, stream, session=None) -> None:
        await call_with_optional_session(
            self.repository.upsert_stream,
            employee_id=stream.employee_id,
            document=stream_to_document(stream),
            session=session,
        )

    async def run_atomic(self, operation):
        db = getattr(self.repository, "_db", None)
        return await run_atomic(db, operation)


def validated_payload(*, name: str, command) -> dict:
    return validate_command_payload(
        name=name,
        version="v1",
        payload=command.model_dump(mode="json"),
    )
