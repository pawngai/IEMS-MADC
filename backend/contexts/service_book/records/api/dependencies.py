from __future__ import annotations

from app_platform.db.runtime import get_db
from contexts.service_book.records.application.factory import (
    build_service_event_application_service,
)
from contexts.service_book.records.application.service import ServiceEventApplicationService
from fastapi import Depends, Request


def get_service_events_service(
    request: Request,
    db=Depends(get_db),
) -> ServiceEventApplicationService:
    container = getattr(request.app.state, "container", None)
    outbox_repo = container.outbox_repo if container is not None else None
    return build_service_event_application_service(db=db, outbox_repo=outbox_repo)


def actor_id_from_user(current_user: dict) -> str | None:
    return current_user.get("sub") or current_user.get("id")


def event_id_command(command_cls, service_event_id: str):
    return command_cls(service_event_id=service_event_id)
