from __future__ import annotations

from app_platform.policy_engine import Decision
from contexts.leave.domain.leave_request_policy import LEAVE_RULES, LeaveFacts


def evaluate_leave_request(facts: LeaveFacts) -> Decision:
    decision = Decision()
    for rule in LEAVE_RULES:
        rule(facts, decision)
    return decision


__all__ = ["evaluate_leave_request", "LeaveFacts"]
