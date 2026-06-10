from __future__ import annotations

from app_platform.policy_engine import Decision
from contexts.change_requests.domain.change_request_policy import ChangeRequestFacts


def evaluate_change_request(facts: ChangeRequestFacts) -> Decision:
    decision = Decision()
    if facts.is_locked:
        decision.deny("Change request cannot proceed while employee record is locked")
    return decision


__all__ = ["evaluate_change_request", "ChangeRequestFacts"]
