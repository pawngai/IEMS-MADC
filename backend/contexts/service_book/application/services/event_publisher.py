from __future__ import annotations

from typing import Any

from app_platform.db.atomic import call_with_optional_session
from app_platform.outbox.model import OutboxEvent
from app_platform.outbox.repo import OutboxRepository


class ServiceBookWorkflowEventPublisher:
    def __init__(self, *, outbox_repo: OutboxRepository | None) -> None:
        self._outbox_repo = outbox_repo

    async def publish(
        self,
        *,
        name: str,
        entry: dict[str, Any],
        actor_id: str | None,
        session=None,
    ) -> None:
        if self._outbox_repo is None:
            return
        entry_id = str(entry.get("id") or entry.get("entry_id") or "")
        workflow_state = str(entry.get("workflow_state") or entry.get("status") or "")
        payload = {
            "entry_id": entry_id,
            "employee_id": entry.get("employee_id"),
            "part_key": entry.get("part_key"),
            "part_code": entry.get("part_code") or entry.get("part_key"),
            "schema_key": entry.get("schema_key"),
            "schema_version": entry.get("schema_version"),
            "entry_kind": entry.get("entry_kind"),
            "payload": entry.get("payload") or {},
            "status": entry.get("status"),
            "workflow_state": workflow_state,
            "created_at": entry.get("created_at"),
            "updated_at": entry.get("updated_at"),
            "approved_at": entry.get("approved_at"),
            "locked_at": entry.get("locked_at"),
            "version": entry.get("version") or 1,
        }
        await call_with_optional_session(
            self._outbox_repo.add_event,
            OutboxEvent(
                name=name,
                payload=payload,
                actor_id=actor_id,
                department_id=entry.get("department_id"),
                idempotency_key=f"service-book:{name}:{entry_id}:{workflow_state}",
            ),
            session=session,
        )