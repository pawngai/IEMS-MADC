from __future__ import annotations

from app_platform.contracts.registry import validate_command_payload
from app_platform.event_bus.types import EventName
from contexts.service_book.records.application.commands.attach_document import AttachDocumentCommand
from contexts.service_book.records.application.commands.approve_event import (
    ApproveServiceEventCommand,
    LockServiceEventCommand,
)
from contexts.service_book.records.application.commands.record_event import (
    RecordServiceEventCommand,
)
from contexts.service_book.records.application.commands.revise_event import (
    ReviseServiceEventCommand,
)
from contexts.service_book.records.application.commands.submit_event import (
    SubmitServiceEventCommand,
)
from contexts.service_book.records.application.commands.verify_event import (
    VerifyServiceEventCommand,
)
from contexts.service_book.records.application.commands.void_event import VoidServiceEventCommand
from contexts.service_book.records.application.handlers._shared import ServiceEventsHandlerContext
from contexts.service_book.records.application.handlers.approve_event_handler import (
    ApproveEventHandler,
)
from contexts.service_book.records.application.handlers.get_event_handler import GetEventHandler
from contexts.service_book.records.application.handlers.get_stream_handler import (
    GetStreamHandler,
)
from contexts.service_book.records.application.handlers.record_event_handler import (
    RecordEventHandler,
)
from contexts.service_book.records.application.handlers.revise_event_handler import (
    ReviseEventHandler,
)
from contexts.service_book.records.application.handlers.submit_event_handler import (
    SubmitEventHandler,
)
from contexts.service_book.records.application.handlers.verify_event_handler import (
    VerifyEventHandler,
)
from contexts.service_book.records.application.handlers.void_event_handler import VoidEventHandler
from contexts.service_book.records.application.queries.get_stream import GetServiceEventStreamQuery
from contexts.service_book.records.application.services.event_publisher import (
    ServiceEventsEventPublisher,
)
from contexts.service_book.records.application.service_summary_projection import (
    EmployeeServiceSummaryProjectionService,
)
from contexts.service_book.records.repository.service_record_repository import ServiceRecordRepository
from shared_kernel.events import utc_now_iso


class ServiceEventApplicationService:
    def __init__(
        self,
        *,
        repository: ServiceRecordRepository,
        outbox_repo,
        service_summary_projection: EmployeeServiceSummaryProjectionService | None = None,
    ) -> None:
        self._repository = repository
        self._context = ServiceEventsHandlerContext(repository=repository)
        self._event_publisher = ServiceEventsEventPublisher(outbox_repo=outbox_repo)

        self._record_handler = RecordEventHandler(
            context=self._context,
            event_publisher=self._event_publisher,
        )
        self._submit_handler = SubmitEventHandler(
            context=self._context,
            event_publisher=self._event_publisher,
        )
        self._verify_handler = VerifyEventHandler(
            context=self._context,
            event_publisher=self._event_publisher,
        )
        self._approve_handler = ApproveEventHandler(
            context=self._context,
            event_publisher=self._event_publisher,
            service_summary_projection=service_summary_projection,
        )
        self._void_handler = VoidEventHandler(
            context=self._context,
            event_publisher=self._event_publisher,
        )
        self._revise_handler = ReviseEventHandler(
            context=self._context,
            event_publisher=self._event_publisher,
        )
        self._get_event_handler = GetEventHandler(repository=repository)
        self._get_stream_handler = GetStreamHandler(repository=repository)

    async def initialize_stream(self, *, employee_id: str) -> None:
        await self._repository.initialize_stream(employee_id=employee_id)

    async def get_stream(self, *, employee_id: str) -> dict:
        return await self._get_stream_handler.handle(
            query=GetServiceEventStreamQuery(employee_id=employee_id)
        )

    async def record(self, *, command: RecordServiceEventCommand, actor_id: str | None) -> dict:
        return await self._record_handler.handle(command=command, actor_id=actor_id)

    async def revise(self, *, command: ReviseServiceEventCommand, actor_id: str | None) -> dict:
        return await self._revise_handler.handle(command=command, actor_id=actor_id)

    async def void(self, *, command: VoidServiceEventCommand, actor_id: str | None) -> dict:
        return await self._void_handler.handle(command=command, actor_id=actor_id)

    async def submit(self, *, command: SubmitServiceEventCommand, actor_id: str | None) -> dict:
        return await self._submit_handler.handle(command=command, actor_id=actor_id)

    async def verify(self, *, command: VerifyServiceEventCommand, actor_id: str | None) -> dict:
        return await self._verify_handler.handle(command=command, actor_id=actor_id)

    async def approve(self, *, command: ApproveServiceEventCommand, actor_id: str | None) -> dict:
        return await self._approve_handler.handle(command=command, actor_id=actor_id)

    async def lock(self, *, command: LockServiceEventCommand, actor_id: str | None) -> dict:
        return await self._approve_handler.lock(command=command, actor_id=actor_id)

    async def attach_document(self, *, command: AttachDocumentCommand, actor_id: str | None) -> dict:
        payload = validate_command_payload(
            name="AttachServiceEventDocument",
            version="v1",
            payload=command.model_dump(mode="json"),
        )
        stream = await self._context.load_stream_by_event_id(
            service_event_id=payload["service_event_id"]
        )
        now = utc_now_iso()
        service_event = stream.attach_document(
            service_event_id=payload["service_event_id"],
            document_id=payload["document_id"],
            document_type=payload.get("document_type"),
            actor_id=actor_id,
            timestamp=now,
        )
        result = {
            "service_event_id": service_event.service_event_id,
            "employee_id": stream.employee_id,
            "documents_count": len(service_event.documents),
            "status": service_event.status.value,
        }

        async def _operation(session):
            await self._context.persist_stream(stream=stream, session=session)
            await self._event_publisher.publish(
                name=EventName.SERVICE_EVENT_DOCUMENT_ATTACHED.value,
                payload={
                    "event_version": 1,
                    "service_event_id": service_event.service_event_id,
                    "employee_id": stream.employee_id,
                    "document_id": payload["document_id"],
                    "document_type": payload.get("document_type"),
                    "status": service_event.status.value,
                },
                actor_id=actor_id,
                session=session,
            )
            return result

        return await self._context.run_atomic(_operation)

