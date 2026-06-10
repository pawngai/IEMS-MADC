"""Change-request gating policy.

Owned by the change_requests bounded context. The platform supplies only the
``Decision`` primitive.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ChangeRequestFacts:
    employee_id: str
    is_locked: bool


__all__ = ["ChangeRequestFacts"]
