from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class InvalidWorkflowTransition(Exception):
    """Domain exception for illegal workflow state transitions."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ApprovalTaskStatus(str, Enum):
    QUEUED = "QUEUED"
    ASSIGNED = "ASSIGNED"
    IN_REVIEW = "IN_REVIEW"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


@dataclass(slots=True)
class WorkflowAggregate:
    current_state: ApprovalTaskStatus

    def assign(self) -> ApprovalTaskStatus:
        if self.current_state != ApprovalTaskStatus.QUEUED:
            raise InvalidWorkflowTransition(
                f"Cannot assign from {self.current_state.value}",
            )
        return ApprovalTaskStatus.ASSIGNED

    def start_review(self) -> ApprovalTaskStatus:
        if self.current_state not in {ApprovalTaskStatus.ASSIGNED, ApprovalTaskStatus.QUEUED}:
            raise InvalidWorkflowTransition(
                f"Cannot start review from {self.current_state.value}",
            )
        return ApprovalTaskStatus.IN_REVIEW

    def complete(self) -> ApprovalTaskStatus:
        if self.current_state not in {
            ApprovalTaskStatus.QUEUED,
            ApprovalTaskStatus.ASSIGNED,
            ApprovalTaskStatus.IN_REVIEW,
        }:
            raise InvalidWorkflowTransition(
                f"Cannot complete from {self.current_state.value}",
            )
        return ApprovalTaskStatus.COMPLETED

    def reject(self) -> ApprovalTaskStatus:
        if self.current_state in {
            ApprovalTaskStatus.COMPLETED,
            ApprovalTaskStatus.CANCELLED,
            ApprovalTaskStatus.REJECTED,
        }:
            raise InvalidWorkflowTransition(
                f"Cannot reject from {self.current_state.value}",
            )
        return ApprovalTaskStatus.REJECTED

    def cancel(self) -> ApprovalTaskStatus:
        if self.current_state in {
            ApprovalTaskStatus.COMPLETED,
            ApprovalTaskStatus.CANCELLED,
        }:
            raise InvalidWorkflowTransition(
                f"Cannot cancel from {self.current_state.value}",
            )
        return ApprovalTaskStatus.CANCELLED
