from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app_platform.event_bus.bus import EventBus
from app_platform.event_bus.types import EventName
from app_platform.outbox.dispatcher import OutboxDispatcher
from contexts.audit.application.subscribers import register_audit_subscribers
from contexts.notifications.application.subscribers import register_notification_subscribers


class _FakeInsertCollection:
    def __init__(self) -> None:
        self.inserted: list[dict] = []

    async def insert_one(self, document: dict):
        self.inserted.append(document)

    async def update_one(self, query: dict, update: dict, upsert: bool = False):
        for item in self.inserted:
            if all(item.get(key) == value for key, value in query.items()):
                return None
        if upsert:
            self.inserted.append(dict((update or {}).get("$setOnInsert") or {}))
        return None


class _FakeDB:
    def __init__(self) -> None:
        self.audit_logs = _FakeInsertCollection()
        self.notifications = _FakeInsertCollection()


class _FakeOutboxRepo:
    def __init__(self, docs: list[dict]) -> None:
        self._docs = docs
        self.sent_ids: list[str] = []
        self.failed_ids: list[str] = []
        self.failed_errors: dict[str, str] = {}

    async def get_pending(self, batch_size: int = 100, **_kwargs) -> list[dict]:
        return self._docs[:batch_size]

    async def lock_for_processing(self, event_id: str, ttl_seconds: int = 30) -> bool:
        return True

    async def mark_sent(self, event_id: str) -> None:
        self.sent_ids.append(event_id)

    async def mark_failed(self, event_id: str, err: str, **_kwargs) -> None:
        self.failed_ids.append(event_id)
        self.failed_errors[event_id] = err


@pytest.mark.asyncio
async def test_outbox_dispatch_publishes_and_triggers_subscribers() -> None:
    db = _FakeDB()
    bus = EventBus()

    register_audit_subscribers(event_bus=bus, db_provider=lambda: db)
    register_notification_subscribers(event_bus=bus, db_provider=lambda: db)

    outbox_docs = [
        {
            "_id": "evt-1",
            "name": EventName.LEAVE_APPROVED.value,
            "payload": {
                "leave_id": "L-501",
                "employee_id": "EMP-501",
                "leave_type_code": "EL",
                "days_applied": 2,
                "status": "SANCTIONED",
            },
            "actor_id": "approver-501",
            "department_id": "FIN",
            "occurred_at": "2026-02-26T10:00:00+00:00",
        }
    ]
    repo = _FakeOutboxRepo(outbox_docs)
    dispatcher = OutboxDispatcher(outbox_repo=repo, event_bus=bus)

    await dispatcher._drain_once()

    assert repo.sent_ids == ["evt-1"]
    assert repo.failed_ids == []

    assert len(db.audit_logs.inserted) == 1
    audit_doc = db.audit_logs.inserted[0]
    assert audit_doc["resource_type"] == "leave_application"
    assert audit_doc["resource_id"] == "L-501"
    assert audit_doc["action"] == "LEAVE_APPROVED"

    assert len(db.notifications.inserted) == 1
    notification_doc = db.notifications.inserted[0]
    assert notification_doc["employee_id"] == "EMP-501"
    assert notification_doc["type"] == "LEAVE_STATUS"
    assert notification_doc["action_url"] == "/ess/leave"


@pytest.mark.asyncio
async def test_outbox_dispatch_change_request_applied_triggers_subscribers() -> None:
    db = _FakeDB()
    bus = EventBus()

    register_audit_subscribers(event_bus=bus, db_provider=lambda: db)
    register_notification_subscribers(event_bus=bus, db_provider=lambda: db)

    outbox_docs = [
        {
            "_id": "evt-2",
            "name": EventName.CHANGE_REQUEST_APPLIED.value,
            "payload": {
                "request_id": "CR-501",
                "employee_id": "EMP-777",
                "request_type": "PROFILE",
                "category": "CONTACT",
                "status": "APPLIED",
            },
            "actor_id": "reviewer-777",
            "department_id": "FIN",
            "occurred_at": "2026-02-26T11:00:00+00:00",
        }
    ]
    repo = _FakeOutboxRepo(outbox_docs)
    dispatcher = OutboxDispatcher(outbox_repo=repo, event_bus=bus)

    await dispatcher._drain_once()

    assert repo.sent_ids == ["evt-2"]
    assert repo.failed_ids == []

    assert len(db.audit_logs.inserted) == 1
    audit_doc = db.audit_logs.inserted[0]
    assert audit_doc["resource_type"] == "change_request"
    assert audit_doc["resource_id"] == "CR-501"
    assert audit_doc["action"] == "CHANGE_REQUEST_APPLIED"

    assert len(db.notifications.inserted) == 1
    notification_doc = db.notifications.inserted[0]
    assert notification_doc["employee_id"] == "EMP-777"
    assert notification_doc["type"] == "CHANGE_REQUEST"
    assert notification_doc["action_url"] == "/ess/change-requests"


@pytest.mark.asyncio
async def test_outbox_dispatch_employee_profile_approved_triggers_audit() -> None:
    db = _FakeDB()
    bus = EventBus()

    register_audit_subscribers(event_bus=bus, db_provider=lambda: db)
    register_notification_subscribers(event_bus=bus, db_provider=lambda: db)

    outbox_docs = [
        {
            "_id": "evt-3",
            "name": EventName.EMPLOYEE_PROFILE_APPROVED.value,
            "payload": {
                "employee_id": "EMP-900",
                "status": "APPROVED",
                "remarks": "Validated",
            },
            "actor_id": "approver-900",
            "department_id": "HR",
            "occurred_at": "2026-02-26T12:00:00+00:00",
        }
    ]
    repo = _FakeOutboxRepo(outbox_docs)
    dispatcher = OutboxDispatcher(outbox_repo=repo, event_bus=bus)

    await dispatcher._drain_once()

    assert repo.sent_ids == ["evt-3"]
    assert repo.failed_ids == []

    assert len(db.audit_logs.inserted) == 1
    audit_doc = db.audit_logs.inserted[0]
    assert audit_doc["resource_type"] == "employee_profile"
    assert audit_doc["resource_id"] == "EMP-900"
    assert audit_doc["action"] == "EMPLOYEE_PROFILE_APPROVED"

    assert db.notifications.inserted == []


@pytest.mark.asyncio
async def test_outbox_dispatch_document_event_triggers_audit() -> None:
    db = _FakeDB()
    bus = EventBus()

    register_audit_subscribers(event_bus=bus, db_provider=lambda: db)
    register_notification_subscribers(event_bus=bus, db_provider=lambda: db)

    outbox_docs = [
        {
            "_id": "evt-4",
            "name": EventName.DOCUMENT_DELETED.value,
            "payload": {
                "document_id": "doc-900",
                "filename": "doc-900.pdf",
                "deleted_by_user_id": "auditor-1",
            },
            "actor_id": "auditor-1",
            "department_id": "HR",
            "occurred_at": "2026-02-26T13:00:00+00:00",
        }
    ]
    repo = _FakeOutboxRepo(outbox_docs)
    dispatcher = OutboxDispatcher(outbox_repo=repo, event_bus=bus)

    await dispatcher._drain_once()

    assert repo.sent_ids == ["evt-4"]
    assert repo.failed_ids == []

    assert len(db.audit_logs.inserted) == 1
    audit_doc = db.audit_logs.inserted[0]
    assert audit_doc["resource_type"] == "document"
    assert audit_doc["resource_id"] == "doc-900"
    assert audit_doc["action"] == "DOCUMENT_DELETED"

    assert db.notifications.inserted == []


@pytest.mark.asyncio
async def test_duplicate_dispatch_does_not_duplicate_audit_or_notifications() -> None:
    db = _FakeDB()
    bus = EventBus()

    register_audit_subscribers(event_bus=bus, db_provider=lambda: db)
    register_notification_subscribers(event_bus=bus, db_provider=lambda: db)

    outbox_docs = [
        {
            "_id": "evt-duplicate-side-effects",
            "name": EventName.LEAVE_APPROVED.value,
            "payload": {
                "leave_id": "L-777",
                "employee_id": "EMP-777",
                "leave_type_code": "EL",
                "days_applied": 1,
                "status": "SANCTIONED",
            },
            "actor_id": "approver-777",
            "department_id": "FIN",
            "occurred_at": "2026-02-26T14:00:00+00:00",
        }
    ]
    repo = _FakeOutboxRepo(outbox_docs)
    dispatcher = OutboxDispatcher(outbox_repo=repo, event_bus=bus)

    await dispatcher._drain_once()
    await dispatcher._drain_once()

    assert len(db.audit_logs.inserted) == 1
    assert db.audit_logs.inserted[0]["source_event_id"] == "evt-duplicate-side-effects"
    assert len(db.notifications.inserted) == 1
    assert db.notifications.inserted[0]["source_event_id"] == "evt-duplicate-side-effects"
