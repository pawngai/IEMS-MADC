"""Application-layer use-case orchestrators for service-events.

These are convenience facades that compose validation, recording, approval
and routing into single calls.  Cross-context consumers should import
from ``contracts.use_cases`` rather than reaching into this module directly.
"""

from __future__ import annotations

from typing import Any

from app_platform.event_bus.types import EventName
from contexts.service_book.records.application.commands.approve_event import (
    ApproveServiceEventCommand,
)
from contexts.service_book.records.application.commands.record_event import (
    RecordServiceEventCommand,
)
from contexts.service_book.records.application.factory import (
    build_service_event_application_service,
)
from contexts.service_book.records.mappers.service_event_mapper import category_to_event_type
from contexts.service_book.records.schemas.service_event_schemas import (
    ServiceEventCategory,
    _normalize_category_value,
    normalize_service_event_input,
)
from fastapi import HTTPException


def classifyServiceEvent(payload_or_type: dict[str, Any] | str | None) -> dict[str, Any]:
    """Classify a raw payload or type string into a canonical service-event category."""
    raw = payload_or_type if isinstance(payload_or_type, dict) else {"event_type": payload_or_type}
    category_raw = (
        raw.get("category")
        or raw.get("event_category")
        or raw.get("event_type")
        or raw.get("eventType")
        or raw.get("type")
        or raw.get("event_name")
        or raw.get("eventName")
        or "GENERIC"
    )
    canonical_category = ServiceEventCategory(_normalize_category_value(category_raw))
    event_type = category_to_event_type(canonical_category)
    return {
        "input": canonical_category.value,
        "category": canonical_category.value,
        "event_type": event_type,
        "classification": event_type.value,
        "can_route_to_service_book": True,
    }


def validateServiceEventPayload(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalise a raw service-event payload dict."""
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="Service event payload must be an object")
    try:
        canonical = normalize_service_event_input(payload)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    normalized = dict(payload)
    normalized["event_type"] = category_to_event_type(canonical.category)
    normalized["category"] = canonical.category.value
    normalized["payload"] = canonical.payload
    normalized["employee_id"] = canonical.employee_id
    normalized["effective_from"] = canonical.effective_from
    normalized["effective_to"] = canonical.effective_to
    if canonical.part_code:
        normalized["part_code"] = canonical.part_code
    return normalized


async def recordServiceEvent(
    *,
    db,
    payload: dict[str, Any] | RecordServiceEventCommand,
    actor_id: str | None,
    outbox_repo=None,
) -> dict[str, Any]:
    """Validate, normalise, and record a service event in one call."""
    payload_dict = payload.model_dump(mode="json") if hasattr(payload, "model_dump") else dict(payload)
    normalized = validateServiceEventPayload(payload_dict)
    command = RecordServiceEventCommand(**normalized)

    service = build_service_event_application_service(db=db, outbox_repo=outbox_repo)
    result = await service.record(command=command, actor_id=actor_id)
    result["service_book_is_authoritative"] = True
    return result


def routeServiceEventToServiceBook(*, approved_event: dict[str, Any]) -> dict[str, Any]:
    """Return routing metadata for an approved event's projection to the service book."""
    return {
        "routed": bool(approved_event.get("status") == "APPROVED"),
        "target": "service_book",
        "mode": "event_bus_projection",
        "event_name": EventName.SERVICE_EVENT_APPROVED.value,
        "service_book_remains_authoritative": True,
    }


async def applyApprovedServiceEvent(
    *,
    db,
    service_event_id: str,
    actor_id: str | None,
    outbox_repo=None,
) -> dict[str, Any]:
    """Record and auto-approve a service event, attaching routing metadata."""
    service = build_service_event_application_service(db=db, outbox_repo=outbox_repo)
    approved = await service.approve(
        command=ApproveServiceEventCommand(service_event_id=service_event_id),
        actor_id=actor_id,
    )
    approved["service_book_route"] = routeServiceEventToServiceBook(approved_event=approved)
    return approved
