from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class NotificationMessage:
    id: str
    employee_id: str
    type: str
    title: str
    message: str
    level: str
    timestamp: str
    read: bool = False
    action_url: str | None = None
    source_event_id: str | None = None
