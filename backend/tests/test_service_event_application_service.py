from __future__ import annotations

import pytest

from app_platform.event_bus.types import EventName
from contexts.service_book.records.application.commands.attach_document import AttachDocumentCommand
from contexts.service_book.records.application.service import ServiceEventApplicationService


class _FakeRepository:
    def __init__(self) -> None:
        self.stream_doc = {
            "employee_id": "EMP-100",
            "events": [
                {
                    "service_event_id": "SE-1",
                    "event_type": "INCREMENT",
                    "payload": {"increment_type": "annual"},
                    "date_range": {"effective_from": None, "effective_to": None},
                    "part_code": "IV",
                    "source_ref": None,
                    "status": "DRAFT",
                    "is_voided": False,
                    "void_reason": None,
                    "created_at": "2026-04-10T10:00:00Z",
                    "created_by": "seed-user",
                    "submitted_at": None,
                    "submitted_by": None,
                    "verified_at": None,
                    "verified_by": None,
                    "approved_at": None,
                    "approved_by": None,
                    "locked_at": None,
                    "locked_by": None,
                    "updated_at": "2026-04-10T10:00:00Z",
                    "updated_by": "seed-user",
                    "documents": [],
                    "revisions": [],
                }
            ],
        }
        self.persisted_employee_id: str | None = None
        self.persisted_document: dict | None = None

    async def initialize_stream(self, *, employee_id: str) -> None:
        _ = employee_id

    async def get_stream(self, employee_id: str):
        _ = employee_id
        return self.stream_doc

    async def find_stream_by_event_id(self, *, service_event_id: str):
        if service_event_id == "SE-1":
            return self.stream_doc
        return None

    async def upsert_stream(self, *, employee_id: str, document: dict) -> None:
        self.persisted_employee_id = employee_id
        self.persisted_document = document
        self.stream_doc = document


class _FakeOutboxRepo:
    def __init__(self) -> None:
        self.events = []

    async def add_event(self, event) -> None:
        self.events.append(event)


@pytest.mark.asyncio
async def test_attach_document_persists_stream_and_emits_outbox_event() -> None:
    repository = _FakeRepository()
    outbox_repo = _FakeOutboxRepo()
    service = ServiceEventApplicationService(repository=repository, outbox_repo=outbox_repo)

    result = await service.attach_document(
        command=AttachDocumentCommand(
            service_event_id="SE-1",
            document_id="DOC-1",
            document_type="ORDER",
        ),
        actor_id="actor-1",
    )

    assert result == {
        "service_event_id": "SE-1",
        "employee_id": "EMP-100",
        "documents_count": 1,
        "status": "DRAFT",
    }

    assert repository.persisted_employee_id == "EMP-100"
    assert repository.persisted_document is not None
    persisted_event = repository.persisted_document["events"][0]
    assert persisted_event["documents"] == [
        {
            "document_id": "DOC-1",
            "document_type": "ORDER",
            "attached_at": persisted_event["updated_at"],
            "attached_by": "actor-1",
        }
    ]

    assert len(outbox_repo.events) == 1
    outbox_event = outbox_repo.events[0]
    assert outbox_event.name == EventName.SERVICE_EVENT_DOCUMENT_ATTACHED.value
    assert outbox_event.actor_id == "actor-1"
    assert outbox_event.payload == {
        "event_version": 1,
        "service_event_id": "SE-1",
        "employee_id": "EMP-100",
        "document_id": "DOC-1",
        "document_type": "ORDER",
        "status": "DRAFT",
    }
