"""Platform-level event payload primitives.

This module hosts ONLY domain-neutral event payload base classes. Business
event schemas (employee identity events, service-event payloads, document
events, etc.) live in their owning bounded context's ``contracts/events``
module — never here. See ``ARCHITECTURE_RULES.md`` for the ownership rule.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LenientEventPayload(BaseModel):
    """Permissive event payload base for events whose schemas are still
    in transition or are intentionally schemaless."""

    model_config = ConfigDict(extra="allow")
    event_version: int = Field(default=1, ge=1)


__all__ = ["LenientEventPayload"]
