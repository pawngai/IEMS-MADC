from __future__ import annotations

import pytest

from contexts.workflow.domain.aggregate import ApprovalTaskStatus, InvalidWorkflowTransition, WorkflowAggregate


def test_workflow_happy_path() -> None:
    aggregate = WorkflowAggregate(current_state=ApprovalTaskStatus.QUEUED)
    assert aggregate.assign() == ApprovalTaskStatus.ASSIGNED

    aggregate = WorkflowAggregate(current_state=ApprovalTaskStatus.ASSIGNED)
    assert aggregate.start_review() == ApprovalTaskStatus.IN_REVIEW

    aggregate = WorkflowAggregate(current_state=ApprovalTaskStatus.IN_REVIEW)
    assert aggregate.complete() == ApprovalTaskStatus.COMPLETED

    aggregate = WorkflowAggregate(current_state=ApprovalTaskStatus.ASSIGNED)
    assert aggregate.reject() == ApprovalTaskStatus.REJECTED


def test_workflow_invalid_transition_raises() -> None:
    aggregate = WorkflowAggregate(current_state=ApprovalTaskStatus.COMPLETED)
    with pytest.raises(InvalidWorkflowTransition):
        aggregate.assign()
