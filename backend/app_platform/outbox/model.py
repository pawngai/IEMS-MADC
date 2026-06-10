from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from shared_kernel.events.request_context import get_idempotency_key, get_request_id
from shared_kernel.ids import new_id
from shared_kernel.events import utc_now_iso


class OutboxStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    DEAD_LETTER = "DEAD_LETTER"


@dataclass(slots=True)
class OutboxEvent:
    name: str
    payload: dict[str, Any]
    event_version: str = "v1"
    actor_id: str | None = None
    department_id: str | None = None
    correlation_id: str | None = field(default_factory=get_request_id)
    idempotency_key: str | None = field(default_factory=get_idempotency_key)
    occurred_at: str = field(default_factory=utc_now_iso)
    status: str = OutboxStatus.PENDING.value
    attempts: int = 0
    last_error: str | None = None
    locked_until: str | None = None
    next_attempt_at: str | None = None
    event_id: str = field(default_factory=new_id)

    def to_document(self) -> dict[str, Any]:
        return {
            "_id": self.event_id,
            "name": self.name,
            "payload": self.payload,
            "event_version": self.event_version,
            "actor_id": self.actor_id,
            "department_id": self.department_id,
            "correlation_id": self.correlation_id,
            "idempotency_key": self.idempotency_key,
            "occurred_at": self.occurred_at,
            "status": self.status,
            "attempts": self.attempts,
            "last_error": self.last_error,
            "locked_until": self.locked_until,
            "next_attempt_at": self.next_attempt_at,
        }
