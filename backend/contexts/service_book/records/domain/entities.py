from __future__ import annotations

from dataclasses import dataclass, field

from contexts.service_book.records.domain.value_objects import (
    EffectiveDateRange,
    ServiceRecordType,
    ServiceRecordStatus,
    SourceRef,
)


@dataclass(slots=True)
class Revision:
    revision: int
    reason: str
    actor_id: str | None
    payload: dict
    corrected_at: str


@dataclass(slots=True)
class ServiceRecord:
    service_event_id: str
    employee_id: str
    event_type: ServiceRecordType
    payload: dict
    date_range: EffectiveDateRange
    aggregate_id: str | None = None
    occurred_at: str | None = None
    recorded_at: str | None = None
    recorded_by: str | None = None
    source_context: str | None = None
    correlation_id: str | None = None
    causation_id: str | None = None
    previous_hash: str | None = None
    event_hash: str | None = None
    event_version: int = 1
    order_number: str | None = None
    order_date: str | None = None
    issuing_authority: str | None = None
    part_code: str | None = None
    source_ref: SourceRef | None = None
    status: ServiceRecordStatus = ServiceRecordStatus.DRAFT
    is_voided: bool = False
    void_reason: str | None = None
    created_at: str | None = None
    created_by: str | None = None
    submitted_at: str | None = None
    submitted_by: str | None = None
    verified_at: str | None = None
    verified_by: str | None = None
    approved_at: str | None = None
    approved_by: str | None = None
    locked_at: str | None = None
    locked_by: str | None = None
    updated_at: str | None = None
    updated_by: str | None = None
    documents: list[dict] = field(default_factory=list)
    revisions: list[Revision] = field(default_factory=list)
    audit_metadata: dict = field(default_factory=dict)
    version: int = 1
