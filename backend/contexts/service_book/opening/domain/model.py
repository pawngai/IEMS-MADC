from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ServiceBookOpening:
    employee_id: str
    service_book_id: str
    opening_status: str
    part_i_snapshot: dict = field(default_factory=dict)
    part_ii_a_certificates: list[dict] = field(default_factory=list)
    part_ii_b_certificates: list[dict] = field(default_factory=list)
    initial_appointment_record_id: str | None = None
    verification_status: str | None = None
    opened_by: str | None = None
    opened_at: str | None = None
    approved_by: str | None = None
    approved_at: str | None = None


__all__ = ["ServiceBookOpening"]
