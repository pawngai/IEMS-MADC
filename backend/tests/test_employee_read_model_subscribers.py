from __future__ import annotations

import asyncio

from app_platform.event_bus.bus import EventBus
from app_platform.event_bus.types import BaseEvent, EventName
from contexts.employee_master.profile.contracts.subscribers import (
    register_employee_read_model_subscribers,
)


class _FakeCollection:
    def __init__(self) -> None:
        self.items: dict[str, dict] = {}

    async def update_one(self, query: dict, update: dict, upsert: bool = False):
        employee_id = query.get("employee_id")
        existing = self.items.get(employee_id) or {"employee_id": employee_id}
        existing.update(update.get("$set") or {})
        if upsert:
            existing.update(update.get("$setOnInsert") or {})
        self.items[employee_id] = existing

    async def find_one(self, query: dict, _projection: dict):
        employee_id = query.get("employee_id")
        item = self.items.get(employee_id)
        return dict(item) if item else None


class _FakeDB:
    def __init__(self) -> None:
        self.employee_profile_read_models = _FakeCollection()
        self.employee_identities = _FakeCollection()


def test_employee_read_model_projects_create_and_update_events() -> None:
    async def _run() -> None:
        db = _FakeDB()
        bus = EventBus()
        register_employee_read_model_subscribers(event_bus=bus, db_provider=lambda: db)

        await bus.publish(
            BaseEvent(
                name=EventName.EMPLOYEE_CREATED.value,
                payload={
                    "employee_id": "EMP-1",
                    "name": "Jane",
                    "dept_id": "FIN",
                    "designation_id": "DES-1",
                    "created_at": "2026-03-03T00:00:00Z",
                    "version": 1,
                },
            )
        )

        await bus.publish(
            BaseEvent(
                name=EventName.EMPLOYEE_UPDATED.value,
                payload={
                    "employee_id": "EMP-1",
                    "patch": {
                        "full_name": "Jane Doe",
                        "current_department_id": "EST",
                    },
                    "updated_at": "2026-03-03T01:00:00Z",
                    "version": 2,
                },
            )
        )

        projected = db.employee_profile_read_models.items["EMP-1"]
        assert projected["employee_id"] == "EMP-1"
        assert projected["full_name"] == "Jane Doe"
        assert projected["current_department_id"] == "EST"
        assert projected["workflow_status"] == "DRAFT"
        assert projected["version"] == 2

    asyncio.run(_run())


def test_employee_read_model_projects_identity_created_as_draft_profile() -> None:
    async def _run() -> None:
        db = _FakeDB()
        bus = EventBus()
        register_employee_read_model_subscribers(event_bus=bus, db_provider=lambda: db)

        await bus.publish(
            BaseEvent(
                name=EventName.EMPLOYEE_IDENTITY_CREATED.value,
                payload={
                    "employee_id": "EMP-DRAFT-1",
                    "employee_code": "MADC-2024-R0001",
                    "full_name": "Draft Identity User",
                    "current_department_id": "FIN",
                    "current_designation_id": "DES-1",
                    "date_of_birth": "1990-01-01",
                    "date_of_initial_engagement": "2024-04-01",
                    "employment_type": "REGULAR",
                    "employee_status": "ACTIVE",
                    "workflow_status": "DRAFT",
                    "identity_workflow_status": "DRAFT",
                    "created_at": "2026-03-03T00:00:00Z",
                    "created_by": "u1",
                    "version": 1,
                },
            )
        )

        projected = db.employee_profile_read_models.items["EMP-DRAFT-1"]
        assert projected["employee_id"] == "EMP-DRAFT-1"
        assert projected["employee_code"] == "MADC-2024-R0001"
        assert projected["full_name"] == "Draft Identity User"
        assert projected["current_department_id"] == "FIN"
        assert projected["workflow_status"] == "DRAFT"
        assert projected["identity_workflow_status"] == "DRAFT"

    asyncio.run(_run())
