from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date

from contexts.service_book.records.domain.entities import Revision, ServiceRecord
from contexts.service_book.records.domain.value_objects import (
    EffectiveDateRange,
    ServiceRecordType,
    ServiceRecordStatus,
    SourceRef,
    can_transition_status,
)
from shared_kernel.base import DomainError


IMMUTABLE_STATUSES = {
    ServiceRecordStatus.APPROVED,
    ServiceRecordStatus.LOCKED,
}


@dataclass(slots=True)
class ServiceRecordStream:
    employee_id: str
    events: list[ServiceRecord] = field(default_factory=list)

    def _get_event(self, service_event_id: str) -> ServiceRecord:
        for service_event in self.events:
            if service_event.service_event_id == service_event_id:
                return service_event
        raise DomainError(f"Service event '{service_event_id}' not found")

    @staticmethod
    def _hash_event_payload(payload: dict) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _previous_event_hash(self) -> str | None:
        if not self.events:
            return None
        return self.events[-1].event_hash

    def record_event(
        self,
        *,
        service_event_id: str,
        event_type: ServiceRecordType,
        payload: dict,
        effective_from: date | None,
        effective_to: date | None,
        part_code: str | None,
        source_ref: SourceRef | None,
        actor_id: str | None,
        timestamp: str,
        order_number: str | None = None,
        order_date: str | None = None,
        issuing_authority: str | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> ServiceRecord:
        if any(item.service_event_id == service_event_id for item in self.events):
            raise DomainError(f"Service event '{service_event_id}' already exists")
        if not payload:
            raise DomainError("Service event payload is required")

        previous_hash = self._previous_event_hash()
        source_context = source_ref.context if source_ref else "service_book.records"
        event_version = 1
        envelope_for_hash = {
            "event_id": service_event_id,
            "event_type": event_type.value,
            "event_version": event_version,
            "employee_id": self.employee_id,
            "aggregate_id": self.employee_id,
            "occurred_at": timestamp,
            "effective_from": effective_from.isoformat() if effective_from else None,
            "recorded_at": timestamp,
            "recorded_by": actor_id,
            "source_context": source_context,
            "correlation_id": correlation_id,
            "causation_id": causation_id,
            "payload": payload or {},
            "previous_hash": previous_hash,
        }

        service_event = ServiceRecord(
            service_event_id=service_event_id,
            employee_id=self.employee_id,
            event_type=event_type,
            payload=payload or {},
            date_range=EffectiveDateRange(
                effective_from=effective_from,
                effective_to=effective_to,
            ),
            aggregate_id=self.employee_id,
            occurred_at=timestamp,
            recorded_at=timestamp,
            recorded_by=actor_id,
            source_context=source_context,
            correlation_id=correlation_id,
            causation_id=causation_id,
            previous_hash=previous_hash,
            event_hash=self._hash_event_payload(envelope_for_hash),
            event_version=event_version,
            order_number=order_number,
            order_date=order_date,
            issuing_authority=issuing_authority,
            part_code=part_code,
            source_ref=source_ref,
            created_at=timestamp,
            created_by=actor_id,
            updated_at=timestamp,
            updated_by=actor_id,
            audit_metadata={
                "recorded_by": actor_id,
                "recorded_at": timestamp,
                "correlation_id": correlation_id,
                "causation_id": causation_id,
            },
            version=event_version,
        )
        self.events.append(service_event)
        return service_event

    def correct_event(
        self,
        *,
        service_event_id: str,
        corrected_payload: dict,
        reason: str,
        actor_id: str | None,
        timestamp: str,
    ) -> ServiceRecord:
        service_event = self._get_event(service_event_id)
        if service_event.is_voided:
            raise DomainError("Cannot correct a voided service event")
        if service_event.status in IMMUTABLE_STATUSES:
            raise DomainError(
                "Approved service records are immutable; record a correction or supersession record"
            )

        next_revision = len(service_event.revisions) + 1
        service_event.payload = corrected_payload or {}
        service_event.updated_at = timestamp
        service_event.updated_by = actor_id
        service_event.revisions.append(
            Revision(
                revision=next_revision,
                reason=reason,
                actor_id=actor_id,
                payload=service_event.payload,
                corrected_at=timestamp,
            )
        )
        return service_event

    def void_event(
        self,
        *,
        service_event_id: str,
        reason: str,
        actor_id: str | None,
        timestamp: str,
    ) -> ServiceRecord:
        service_event = self._get_event(service_event_id)
        if service_event.status in IMMUTABLE_STATUSES:
            raise DomainError(
                "Approved service records are immutable; record a correction or supersession record"
            )
        service_event.is_voided = True
        service_event.status = ServiceRecordStatus.VOIDED
        service_event.void_reason = reason
        service_event.updated_at = timestamp
        service_event.updated_by = actor_id
        return service_event

    def transition_event_status(
        self,
        *,
        service_event_id: str,
        target_status: ServiceRecordStatus,
        actor_id: str | None,
        timestamp: str,
    ) -> ServiceRecord:
        service_event = self._get_event(service_event_id)
        if service_event.is_voided or service_event.status == ServiceRecordStatus.VOIDED:
            raise DomainError("Cannot transition a voided service event")
        if not can_transition_status(from_status=service_event.status, to_status=target_status):
            raise DomainError(
                f"Invalid transition from {service_event.status.value} to {target_status.value}"
            )
        if (
            target_status == ServiceRecordStatus.APPROVED
            and actor_id is not None
            and service_event.verified_by == actor_id
        ):
            raise DomainError("Verifier and approving authority must be different actors")

        service_event.status = target_status
        service_event.updated_at = timestamp
        service_event.updated_by = actor_id

        if target_status == ServiceRecordStatus.SUBMITTED:
            service_event.submitted_at = timestamp
            service_event.submitted_by = actor_id
        elif target_status == ServiceRecordStatus.VERIFIED:
            service_event.verified_at = timestamp
            service_event.verified_by = actor_id
        elif target_status == ServiceRecordStatus.APPROVED:
            service_event.approved_at = timestamp
            service_event.approved_by = actor_id
        elif target_status == ServiceRecordStatus.LOCKED:
            service_event.locked_at = timestamp
            service_event.locked_by = actor_id

        return service_event

    def attach_document(
        self,
        *,
        service_event_id: str,
        document_id: str,
        document_type: str | None,
        actor_id: str | None,
        timestamp: str,
    ) -> ServiceRecord:
        service_event = self._get_event(service_event_id)
        if service_event.status in IMMUTABLE_STATUSES:
            raise DomainError("Approved service event payload and documents are locked")
        service_event.documents.append(
            {
                "document_id": document_id,
                "document_type": document_type,
                "attached_at": timestamp,
                "attached_by": actor_id,
            }
        )
        service_event.updated_at = timestamp
        service_event.updated_by = actor_id
        return service_event
