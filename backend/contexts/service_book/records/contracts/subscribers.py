"""Public contract for service-event subscriber registration.

Bootstrap/middleware code should import from here, NOT from
``application.subscribers`` directly.
"""

from __future__ import annotations

from contexts.service_book.records.application.subscribers import (  # noqa: F401
    register_service_event_subscribers,
)

__all__ = ["register_service_event_subscribers"]
