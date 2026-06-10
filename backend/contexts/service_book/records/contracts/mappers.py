"""Public contract for service-event mapping utilities.

Cross-context consumers should import from here, NOT from
``mappers.service_event_mapper`` directly.
"""

from __future__ import annotations

from contexts.service_book.records.mappers.service_event_mapper import (  # noqa: F401
    normalize_service_book_part_code,
)

__all__ = ["normalize_service_book_part_code"]
