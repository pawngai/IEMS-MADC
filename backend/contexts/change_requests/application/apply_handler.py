"""Application-layer handler for applying approved change requests.

Delegates actual mutations to owning contexts via their contracts.
"""

from __future__ import annotations

from datetime import datetime, timezone

from contexts.employee_master.contracts.immutability import validate_immutability
from contexts.employee_master.contracts.profile_directory import (
    find_profile,
)
from contexts.employee_master.contracts.profile_commands import (
    update_profile_fields,
)
from contexts.service_book.contracts.service_history_bridge import (
    apply_change_request_service_history,
)
from fastapi import HTTPException


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def apply_approved_changes(db, request_doc: dict, *, session=None) -> None:
    """Route an approved change request to the owning target context."""
    employee_id = request_doc["employee_id"]
    fields = request_doc["fields"]
    request_type = request_doc["request_type"]

    updates = {field["field_name"]: field["requested_value"] for field in fields}

    if request_type == "PROFILE":
        profile = await find_profile(
            db,
            employee_id=employee_id,
            projection={"_id": 0},
        )
        if profile:
            stage = (profile.get("workflow_status") or "DRAFT").upper()
            result = validate_immutability(stage, profile, updates)
            if not result.valid and result.blocked_fields:
                blocked = ", ".join(result.blocked_fields)
                raise HTTPException(
                    400,
                    f"Cannot modify immutable field(s) at stage '{stage}': {blocked}",
                )

        updates["updated_at"] = _now_iso()
        await update_profile_fields(
            db,
            employee_id=employee_id,
            updates=updates,
            session=session,
        )
        return

    if request_type == "SERVICE_BOOK":
        if session is not None:
            raise HTTPException(
                409,
                "Service history changes are event-driven and cannot be applied inside change-request transaction sessions",
            )
        await apply_change_request_service_history(
            db=db,
            actor_id=request_doc.get("reviewed_by"),
            request_doc=request_doc,
        )
        return

    raise HTTPException(400, f"Unknown request type: {request_type}")
