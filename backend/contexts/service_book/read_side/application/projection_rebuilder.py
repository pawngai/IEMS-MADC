from __future__ import annotations

from typing import Any

from app_platform.event_bus.types import EventName
from contexts.service_book.read_side.application.projectors.project_approved_service_event import (
    project_approved_service_event,
)
from contexts.service_book.records.contracts.approved_event_records import (
    list_approved_service_event_records,
)


def _approved_record_to_projection_payload(record: dict[str, Any]) -> dict[str, Any]:
    date_range = record.get("date_range") or {}
    payload = dict(record.get("payload") or {})
    for field_name in ("order_number", "order_date", "issuing_authority"):
        value = record.get(field_name)
        if value is not None:
            payload.setdefault(field_name, value)
    return {
        "event_version": record.get("version") or record.get("event_version") or 1,
        "service_event_id": record.get("service_event_id"),
        "employee_id": record.get("employee_id"),
        "event_type": record.get("event_type"),
        "part_code": record.get("part_code"),
        "effective_date": (
            record.get("effective_date")
            or record.get("effective_from")
            or date_range.get("effective_from")
        ),
        "order_number": record.get("order_number"),
        "order_date": record.get("order_date"),
        "issuing_authority": record.get("issuing_authority"),
        "approved_at": record.get("approved_at"),
        "approved_by": record.get("approved_by"),
        "payload": payload,
        "status": "APPROVED",
        "version": record.get("version") or 1,
    }


async def rebuild_from_approved_service_events(
    *,
    db,
    repo,
    employee_id: str | None = None,
    limit: int = 10000,
) -> dict[str, Any]:
    records = await list_approved_service_event_records(
        db,
        employee_id=employee_id,
        limit=limit,
    )
    projected = 0
    skipped = 0
    last_event_id = None
    for record in records:
        service_event_id = record.get("service_event_id")
        if not service_event_id:
            skipped += 1
            continue
        try:
            await project_approved_service_event(
                repo=repo,
                payload=_approved_record_to_projection_payload(record),
                event_name=EventName.SERVICE_EVENT_APPROVED.value,
                source_event_id=str(service_event_id),
            )
            last_event_id = str(service_event_id)
            projected += 1
        except Exception as exc:
            if hasattr(repo, "update_projection_status"):
                await repo.update_projection_status(
                    projection_name="service_book.approved_service_events",
                    last_event_id=last_event_id,
                    version=1,
                    status="FAILED",
                    error_message=str(exc),
                )
            raise
    if hasattr(repo, "update_projection_status"):
        await repo.update_projection_status(
            projection_name="service_book.approved_service_events",
            last_event_id=last_event_id,
            version=1,
            status="OK",
            error_message=None,
        )
    return {
        "employee_id": employee_id,
        "approved_events_seen": len(records),
        "projected": projected,
        "skipped": skipped,
        "projection_version": 1,
    }
