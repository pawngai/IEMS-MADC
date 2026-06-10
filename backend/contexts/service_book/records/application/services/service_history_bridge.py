from __future__ import annotations

from typing import Any

from contexts.service_book.records.mappers.service_event_mapper import (
    map_change_request_to_service_event_payload,
)
from contexts.service_book.records.application.use_cases import (
    applyApprovedServiceEvent,
    recordServiceEvent,
)


async def apply_change_request_service_history(
    *,
    db,
    request_doc: dict[str, Any],
    actor_id: str | None,
) -> dict[str, Any]:
    employee_id = str(request_doc.get("employee_id") or "").strip()
    category = str(request_doc.get("category") or "GENERIC").strip().upper() or "GENERIC"

    payload = map_change_request_to_service_event_payload(
        request_type=str(request_doc.get("request_type") or "SERVICE_BOOK"),
        category=category,
        fields=list(request_doc.get("fields") or []),
        reason=str(request_doc.get("reason") or ""),
        entry_id=request_doc.get("entry_id"),
        entry_section=request_doc.get("entry_section"),
        entry_label=request_doc.get("entry_label"),
    )

    recorded = await recordServiceEvent(
        db=db,
        payload={
            "employee_id": employee_id,
            "category": category,
            "part_code": category,
            "payload": payload,
            "source_context": "change_requests.service_history",
            "source_reference_id": request_doc.get("request_id"),
        },
        actor_id=actor_id,
    )
    approved = await applyApprovedServiceEvent(
        db=db,
        service_event_id=recorded["service_event_id"],
        actor_id=actor_id,
    )
    return {
        "recorded": recorded,
        "approved": approved,
    }
