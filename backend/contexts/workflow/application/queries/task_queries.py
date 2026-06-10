from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class InboxQuery:
    assignee_user_id: str
    statuses: list[str] | None = None
    limit: int = 200


@dataclass(slots=True)
class OutboxQuery:
    requested_by: str
    statuses: list[str] | None = None
    limit: int = 200
