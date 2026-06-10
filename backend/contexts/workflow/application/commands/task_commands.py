from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CreateApprovalTask:
    subject_type: str
    subject_id: str
    transition_name: str
    requested_by: str
    current_user: dict
    from_state: str | None = None
    to_state: str | None = None
    assignee_user_id: str | None = None
    assignee_role: str | None = None
    payload: dict | None = None


@dataclass(slots=True)
class AssignApprovalTask:
    task_id: str
    actor_id: str
    current_user: dict
    assignee_user_id: str | None = None
    assignee_role: str | None = None
    remarks: str | None = None


@dataclass(slots=True)
class TransitionApprovalTask:
    task_id: str
    action: str
    actor_id: str
    current_user: dict
    remarks: str | None = None
