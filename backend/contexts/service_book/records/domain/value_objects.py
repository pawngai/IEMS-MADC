from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from shared_kernel.base import DomainError


class ServiceRecordType(str, Enum):
    APPOINTMENT_RECORDED = "APPOINTMENT_RECORDED"
    JOINING_RECORDED = "JOINING_RECORDED"
    POSTING_RECORDED = "POSTING_RECORDED"
    TRANSFER_RECORDED = "TRANSFER_RECORDED"
    PROMOTION_RECORDED = "PROMOTION_RECORDED"
    REGULARISATION_RECORDED = "REGULARISATION_RECORDED"
    CONFIRMATION_RECORDED = "CONFIRMATION_RECORDED"
    SUSPENSION_RECORDED = "SUSPENSION_RECORDED"
    REINSTATEMENT_RECORDED = "REINSTATEMENT_RECORDED"
    RETIREMENT_RECORDED = "RETIREMENT_RECORDED"
    RESIGNATION_RECORDED = "RESIGNATION_RECORDED"
    DEATH_RECORDED = "DEATH_RECORDED"
    TERMINATION_RECORDED = "TERMINATION_RECORDED"
    ENGAGEMENT_RECORDED = "ENGAGEMENT_RECORDED"
    ENGAGEMENT_RENEWED = "ENGAGEMENT_RENEWED"
    ENGAGEMENT_EXTENDED = "ENGAGEMENT_EXTENDED"
    ENGAGEMENT_TERMINATED = "ENGAGEMENT_TERMINATED"
    ENGAGEMENT_RATE_REVISED = "ENGAGEMENT_RATE_REVISED"
    CONTRACT_EXECUTED = "CONTRACT_EXECUTED"
    CONTRACT_RENEWED = "CONTRACT_RENEWED"
    CONTRACT_TERMINATED = "CONTRACT_TERMINATED"
    WAGES_RATE_REVISED = "WAGES_RATE_REVISED"
    APPOINTMENT = "APPOINTMENT"
    CONFIRMATION = "CONFIRMATION"
    PROMOTION = "PROMOTION"
    TRANSFER = "TRANSFER"
    DEPUTATION = "DEPUTATION"
    SUSPENSION = "SUSPENSION"
    REINSTATEMENT = "REINSTATEMENT"
    RETIREMENT = "RETIREMENT"
    PAY = "PAY"
    PAY_FIXATION = "PAY_FIXATION"
    INCREMENT = "INCREMENT"
    MACP = "MACP"
    LEAVE_AFFECTING = "LEAVE_AFFECTING"
    DISCIPLINARY = "DISCIPLINARY"
    GENERIC = "GENERIC"
    FINANCIAL_UPGRADATION = "FINANCIAL_UPGRADATION"
    CPC_PAY_FIXATION = "CPC_PAY_FIXATION"
    RESIGNATION = "RESIGNATION"
    DEATH = "DEATH"
    TERMINATION = "TERMINATION"


class ServiceRecordStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    VERIFIED = "VERIFIED"
    APPROVED = "APPROVED"
    LOCKED = "LOCKED"
    VOIDED = "VOIDED"

ALLOWED_STATUS_TRANSITIONS: dict[ServiceRecordStatus, set[ServiceRecordStatus]] = {
    ServiceRecordStatus.DRAFT: {ServiceRecordStatus.SUBMITTED},
    ServiceRecordStatus.SUBMITTED: {
        ServiceRecordStatus.VERIFIED,
        ServiceRecordStatus.DRAFT,
    },
    ServiceRecordStatus.VERIFIED: {
        ServiceRecordStatus.APPROVED,
        ServiceRecordStatus.SUBMITTED,
    },
    ServiceRecordStatus.APPROVED: {ServiceRecordStatus.LOCKED},
    ServiceRecordStatus.LOCKED: set(),
    ServiceRecordStatus.VOIDED: set(),
}


def can_transition_status(*, from_status: ServiceRecordStatus, to_status: ServiceRecordStatus) -> bool:
    return to_status in ALLOWED_STATUS_TRANSITIONS.get(from_status, set())


@dataclass(frozen=True, slots=True)
class SourceRef:
    context: str
    reference_id: str
    revision: int | None = None


@dataclass(frozen=True, slots=True)
class EffectiveDateRange:
    effective_from: date | None = None
    effective_to: date | None = None

    def __post_init__(self) -> None:
        if (
            self.effective_from is not None
            and self.effective_to is not None
            and self.effective_to < self.effective_from
        ):
            raise DomainError("effective_to cannot be earlier than effective_from")
