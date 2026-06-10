from __future__ import annotations

from dataclasses import dataclass
from typing import Any


EDITABLE_STATES = {"DRAFT", "REJECTED"}
MANUAL_WORKFLOW_PART_KEYS = {"SB_PART_I", "SB_PART_II_A", "SB_PART_II_B", "SB_PART_III"}


class InvalidWorkflowTransition(ValueError):
    def __init__(self, *, action: str, current_state: str | None) -> None:
        self.action = action
        self.current_state = current_state or None
        super().__init__(f"Cannot {action} Service Book entry from state {current_state or 'UNKNOWN'}.")


class ManualWorkflowUnsupported(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class WorkflowTransition:
    allowed_states: set[str]
    next_state: str
    action: str
    actor_field: str
    at_field: str
    stamp_attestation: bool = False


def manual_workflow_scope_message() -> str:
    return "Manual workflow is currently enabled only for Part I, Part II-A, Part II-B, and Part III."


def ensure_manual_workflow_part(part_key: str) -> None:
    if str(part_key or "").upper() not in MANUAL_WORKFLOW_PART_KEYS:
        raise ManualWorkflowUnsupported(manual_workflow_scope_message())


def current_workflow_state(entry: dict[str, Any]) -> str:
    return str(entry.get("workflow_state") or entry.get("status") or "").upper()


def ensure_transition(entry: dict[str, Any], *, allowed_states: set[str], action: str) -> None:
    current_state = current_workflow_state(entry)
    if current_state in allowed_states:
        return
    raise InvalidWorkflowTransition(action=action, current_state=current_state)


def resolved_next_state(*, part_key: str, next_state: str) -> str:
    auto_lock_on_approval = str(part_key or "").upper() == "SB_PART_II_A" and next_state == "APPROVED"
    return "LOCKED" if auto_lock_on_approval else next_state
