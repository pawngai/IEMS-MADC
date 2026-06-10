from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app_platform.event_bus.bus import EventBus
from app_platform.event_bus.types import BaseEvent, EventName
from contexts.notifications.application.subscribers import register_notification_subscribers


class _FakeNotificationsCollection:
    def __init__(self) -> None:
        self.inserted: list[dict] = []

    async def insert_one(self, document: dict):
        self.inserted.append(dict(document))

    async def update_one(self, query: dict, update: dict, *, upsert: bool = False):
        for document in self.inserted:
            if all(document.get(key) == value for key, value in query.items()):
                return None
        if upsert:
            self.inserted.append(dict(update.get("$setOnInsert") or {}))
        return None


class _FakeDB:
    def __init__(self) -> None:
        self.notifications = _FakeNotificationsCollection()


@pytest.mark.asyncio
async def test_leave_approved_event_creates_notification_record() -> None:
    db = _FakeDB()
    bus = EventBus()

    register_notification_subscribers(event_bus=bus, db_provider=lambda: db)

    event = BaseEvent(
        name=EventName.LEAVE_APPROVED.value,
        actor_id="approver-1",
        department_id="FIN",
        payload={
            "leave_id": "L-100",
            "employee_id": "EMP-100",
            "leave_type_code": "EL",
            "days_applied": 3,
        },
    )

    await bus.publish(event)

    assert len(db.notifications.inserted) == 1
    doc = db.notifications.inserted[0]
    assert doc["employee_id"] == "EMP-100"
    assert doc["type"] == "LEAVE_STATUS"
    assert doc["read"] is False
    assert doc["action_url"] == "/ess/leave"
    assert doc["id"] == doc["notification_id"]
    assert "approved" in doc["message"].lower()


@pytest.mark.asyncio
async def test_non_leave_approved_event_does_not_create_notification() -> None:
    db = _FakeDB()
    bus = EventBus()

    register_notification_subscribers(event_bus=bus, db_provider=lambda: db)

    event = BaseEvent(
        name=EventName.LEAVE_APPLIED.value,
        actor_id="employee-1",
        payload={"leave_id": "L-200", "employee_id": "EMP-200"},
    )

    await bus.publish(event)

    assert db.notifications.inserted == []


@pytest.mark.asyncio
async def test_change_request_applied_event_creates_notification_record() -> None:
    db = _FakeDB()
    bus = EventBus()

    register_notification_subscribers(event_bus=bus, db_provider=lambda: db)

    event = BaseEvent(
        name=EventName.CHANGE_REQUEST_APPLIED.value,
        actor_id="reviewer-1",
        department_id="FIN",
        payload={
            "request_id": "CR-100",
            "employee_id": "EMP-100",
            "request_type": "PROFILE",
            "category": "CONTACT",
            "status": "APPLIED",
        },
    )

    await bus.publish(event)

    assert len(db.notifications.inserted) == 1
    doc = db.notifications.inserted[0]
    assert doc["employee_id"] == "EMP-100"
    assert doc["type"] == "CHANGE_REQUEST"
    assert doc["action_url"] == "/ess/change-requests"
    assert "approved" in doc["message"].lower()


@pytest.mark.asyncio
async def test_change_request_rejected_event_creates_notification_record() -> None:
    db = _FakeDB()
    bus = EventBus()

    register_notification_subscribers(event_bus=bus, db_provider=lambda: db)

    event = BaseEvent(
        name=EventName.CHANGE_REQUEST_REJECTED.value,
        actor_id="reviewer-2",
        department_id="FIN",
        payload={
            "request_id": "CR-101",
            "employee_id": "EMP-101",
            "request_type": "SERVICE_BOOK",
            "category": "PART_IV",
            "status": "REJECTED",
        },
    )

    await bus.publish(event)

    assert len(db.notifications.inserted) == 1
    doc = db.notifications.inserted[0]
    assert doc["employee_id"] == "EMP-101"
    assert doc["type"] == "CHANGE_REQUEST"
    assert doc["level"] == "warning"
    assert "rejected" in doc["message"].lower()
