"""Public contract for employee domain service predicates and normalizers.

Other contexts should import from here, NOT from
``contexts.employee_master.identity.domain.identity_normalization`` directly.
"""

from __future__ import annotations

from contexts.employee_master.identity.domain.identity_normalization import (  # noqa: F401
    determineEmploymentType,
    isServiceBookEligible,
    normalizeEmployeeRecord,
    updateEmployeeStatus,
)

__all__ = [
    "determineEmploymentType",
    "isServiceBookEligible",
    "normalizeEmployeeRecord",
    "updateEmployeeStatus",
]
