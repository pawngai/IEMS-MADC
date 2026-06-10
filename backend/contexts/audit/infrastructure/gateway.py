from __future__ import annotations

from contexts.audit.repository import audit_repository as repo
from contexts.identity_access.contracts.models import AuditLog


async def write_audit_entry(
    db,
    *,
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    details: dict,
    source_event_id: str | None = None,
) -> None:
    if db is None:
        return

    audit = AuditLog(
        user_id=user_id,
        user_name="event-bus",
        authority="SYSTEM",
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
    )
    audit_doc = audit.model_dump()
    if source_event_id:
        audit_doc["source_event_id"] = source_event_id
    await repo.insert_audit_log(
        db,
        audit_doc,
        source_event_id=source_event_id,
    )
