from __future__ import annotations

from app_platform.event_bus.bus import EventBus
from app_platform.event_bus.types import BaseEvent, EventName
from contexts.employee_master.profile.read_model.application.service import EmployeeProfileReadModelService
from contexts.employee_master.profile.read_model.infrastructure.repository import (
    EmployeeProfileReadModelRepository,
)


def register_employee_read_model_subscribers(*, event_bus: EventBus, db_provider) -> None:
    async def _dispatch(event: BaseEvent) -> None:
        db = db_provider()
        if db is None:
            return

        service = EmployeeProfileReadModelService(
            repo=EmployeeProfileReadModelRepository(db=db)
        )
        payload = event.payload or {}

        if event.name == EventName.EMPLOYEE_IDENTITY_CREATED.value:
            await service.project_employee_identity_created(payload)
        elif event.name == EventName.EMPLOYEE_CREATED.value:
            await service.project_employee_created(payload)
        elif event.name == EventName.EMPLOYEE_UPDATED.value:
            await service.project_employee_updated(payload)
        elif event.name == EventName.EMPLOYEE_STATUS_CHANGED.value:
            await service.project_employee_status_changed(payload)

    event_bus.subscribe(EventName.EMPLOYEE_IDENTITY_CREATED.value, _dispatch)
    event_bus.subscribe(EventName.EMPLOYEE_CREATED.value, _dispatch)
    event_bus.subscribe(EventName.EMPLOYEE_UPDATED.value, _dispatch)
    event_bus.subscribe(EventName.EMPLOYEE_STATUS_CHANGED.value, _dispatch)
