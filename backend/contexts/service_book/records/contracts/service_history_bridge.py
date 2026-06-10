"""Public contract for service-event history bridge.

The change_requests context should import from here, NOT from
``application.services.service_history_bridge`` directly.
"""

from __future__ import annotations

from contexts.service_book.records.application.services.service_history_bridge import (  # noqa: F401
    apply_change_request_service_history,
)

__all__ = ["apply_change_request_service_history"]
