from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

from app_platform.event_bus.bus import EventBus
from app_platform.outbox.dispatcher import OutboxDispatcher
from app_platform.outbox.repo import OutboxRepository
from contexts.leave_attendance.application.evaluate_leave_request import evaluate_leave_request
from contexts.leave_attendance.domain.leave_request_policy import LeaveFacts


@dataclass(slots=True)
class AppContainer:
    event_bus: EventBus
    outbox_repo: OutboxRepository | None
    outbox_dispatcher: OutboxDispatcher | None
    leave_rules_evaluator: Callable[[dict], dict]


def wire_app_container(app) -> AppContainer:
    db = getattr(app.state, "db", None)
    event_bus = EventBus()
    outbox_repo = OutboxRepository(db) if db is not None else None
    outbox_dispatcher = (
        OutboxDispatcher(outbox_repo=outbox_repo, event_bus=event_bus)
        if outbox_repo is not None
        else None
    )

    def _leave_rules_evaluator(facts: dict) -> dict:
        decision = evaluate_leave_request(
            LeaveFacts(
                employee_id=facts.get("employee_id") or "",
                employee_status=facts.get("employee_status") or "ACTIVE",
                leave_type_code=facts.get("leave_type_code") or "",
                leave_days=float(facts.get("leave_days") or 0.0),
                available_balance=facts.get("available_balance"),
                min_days_per_spell=facts.get("min_days_per_spell"),
                max_days_per_spell=facts.get("max_days_per_spell"),
                employee_gender=facts.get("employee_gender"),
                marital_status=facts.get("marital_status"),
                probation_period_months=facts.get("probation_period_months"),
                surviving_children_count=facts.get("surviving_children_count"),
                is_single_mother=facts.get("is_single_mother"),
                leave_from_date=facts.get("leave_from_date") or "",
                leave_to_date=facts.get("leave_to_date") or "",
                medical_certificate_provided=facts.get("medical_certificate_provided"),
                commuted_leave_basis=facts.get("commuted_leave_basis"),
                expected_delivery_date=facts.get("expected_delivery_date"),
                childbirth_date=facts.get("childbirth_date"),
                adoption_date=facts.get("adoption_date"),
                child_date_of_birth=facts.get("child_date_of_birth"),
                child_has_disability=facts.get("child_has_disability"),
                child_order=facts.get("child_order"),
            )
        )
        return {
            "allowed": decision.allowed,
            "reasons": decision.reasons,
            "required_approvals": decision.required_approvals,
        }

    container = AppContainer(
        event_bus=event_bus,
        outbox_repo=outbox_repo,
        outbox_dispatcher=outbox_dispatcher,
        leave_rules_evaluator=_leave_rules_evaluator,
    )
    app.state.container = container
    return container

