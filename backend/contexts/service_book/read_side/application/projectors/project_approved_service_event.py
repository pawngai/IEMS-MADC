from __future__ import annotations

from contexts.service_book.domain.services.truth_boundary import (
    approved_service_event_truth_payload,
    service_event_projects_service_truth,
)
from contexts.service_book.read_side.contracts.events import ServiceBookServiceEventProjection


async def project_approved_service_event(*, repo, payload: dict, event_name: str, source_event_id: str | None = None) -> None:
    if not service_event_projects_service_truth(event_name=event_name, payload=payload):
        return
    event = ServiceBookServiceEventProjection.model_validate(payload)
    part_code = event.part_code or event.part_key
    truth_payload = approved_service_event_truth_payload(payload)
    effective_date = (
        payload.get("effective_date")
        or payload.get("effective_from")
        or payload.get("updated_at")
    )
    await repo.append_entry(
        employee_id=event.employee_id,
        event_name=event_name,
        part_code=part_code,
        payload=truth_payload,
        effective_date=effective_date,
        fields_changed=sorted(list(truth_payload.keys())),
        source_event_id=source_event_id,
    )
    if part_code:
        await repo.upsert_part_projection(
            employee_id=event.employee_id,
            part_code=part_code,
            patch={
                "last_event_name": event_name,
                "last_effective_date": effective_date,
                "version": payload.get("version") or payload.get("event_version") or 1,
            },
        )