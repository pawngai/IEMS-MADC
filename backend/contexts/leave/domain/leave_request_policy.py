"""Leave-request approval policy (CCS Leave Rules).

Owned by the leave bounded context. The platform only supplies the technical
``Decision`` primitive — every business rule below is leave-domain logic and
must live here, not in app_platform.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app_platform.policy_engine import Decision


@dataclass(slots=True)
class LeaveFacts:
    employee_id: str
    employee_status: str
    leave_type_code: str
    leave_days: float
    available_balance: float | None
    min_days_per_spell: float | None
    max_days_per_spell: float | None
    employee_gender: str | None
    marital_status: str | None
    probation_period_months: int | None
    surviving_children_count: int | None
    is_single_mother: bool | None
    leave_from_date: str
    leave_to_date: str
    medical_certificate_provided: bool | None
    commuted_leave_basis: str | None
    expected_delivery_date: str | None
    childbirth_date: str | None
    adoption_date: str | None
    child_date_of_birth: str | None
    child_has_disability: bool | None
    child_order: int | None


def _normalize_text(value: str | None) -> str:
    return str(value or "").strip().upper()


def _parse_iso_date(value: str | None):
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def rule_deny_suspended_employee(facts: LeaveFacts, decision: Decision) -> None:
    if (facts.employee_status or "").upper() == "SUSPENDED":
        decision.deny("Employee is suspended; leave is not allowed")


def rule_deny_insufficient_balance(facts: LeaveFacts, decision: Decision) -> None:
    if facts.available_balance is not None and facts.leave_days > float(facts.available_balance):
        decision.deny("Leave days exceed available balance")


def rule_deny_shorter_than_minimum_spell(facts: LeaveFacts, decision: Decision) -> None:
    if facts.min_days_per_spell is None:
        return
    if facts.leave_days < float(facts.min_days_per_spell):
        decision.deny(
            f"{facts.leave_type_code} requires at least {int(facts.min_days_per_spell)} days in one spell"
        )


def rule_deny_longer_than_maximum_spell(facts: LeaveFacts, decision: Decision) -> None:
    if facts.max_days_per_spell is None:
        return
    if facts.leave_days > float(facts.max_days_per_spell):
        decision.deny(
            f"{facts.leave_type_code} cannot exceed {int(facts.max_days_per_spell)} days in one spell"
        )


def rule_deny_commuted_leave_without_eligible_basis(
    facts: LeaveFacts, decision: Decision
) -> None:
    if _normalize_text(facts.leave_type_code) != "CML":
        return
    if facts.medical_certificate_provided is True:
        return
    if _normalize_text(facts.commuted_leave_basis) == "STUDY_PUBLIC_INTEREST":
        return
    decision.deny(
        "CML requires a medical certificate or an approved public-interest study basis"
    )


def rule_deny_maternity_leave_without_supported_context(
    facts: LeaveFacts, decision: Decision
) -> None:
    if _normalize_text(facts.leave_type_code) != "ML":
        return
    if _normalize_text(facts.employee_gender) != "FEMALE":
        decision.deny("ML is only available to female employees under CCS rules")
    if not (facts.expected_delivery_date or facts.childbirth_date):
        decision.deny("ML requires an expected delivery date or childbirth date")


def rule_deny_paternity_leave_without_supported_context(
    facts: LeaveFacts, decision: Decision
) -> None:
    if _normalize_text(facts.leave_type_code) != "PL":
        return
    if _normalize_text(facts.employee_gender) != "MALE":
        decision.deny("PL is only available to male employees under CCS rules")

    event_date = _parse_iso_date(facts.childbirth_date or facts.adoption_date)
    if event_date is None:
        decision.deny("PL requires a childbirth date or adoption date")
        return

    leave_start = _parse_iso_date(facts.leave_from_date)
    if leave_start is None:
        return
    if leave_start > event_date + timedelta(days=180):
        decision.deny("PL must start within 180 days of childbirth or adoption")


def rule_deny_child_care_leave_without_supported_context(
    facts: LeaveFacts, decision: Decision
) -> None:
    if _normalize_text(facts.leave_type_code) != "CCL":
        return

    child_birth_date = _parse_iso_date(facts.child_date_of_birth)
    if child_birth_date is None:
        decision.deny("CCL requires the child's date of birth")
        return

    leave_start = _parse_iso_date(facts.leave_from_date)
    if leave_start is not None and facts.child_has_disability is not True:
        child_age_days = (leave_start - child_birth_date).days
        if child_age_days >= int(18 * 365.25):
            decision.deny(
                "CCL requires the child to be below 18 years unless the child has a disability"
            )

    if (
        facts.surviving_children_count is not None
        and int(facts.surviving_children_count) > 2
        and facts.is_single_mother is not True
    ):
        decision.deny(
            "CCL is limited to the two eldest surviving children unless the single-mother exception applies"
        )
        return

    if facts.child_order is not None and int(facts.child_order) > 2 and facts.is_single_mother is not True:
        decision.deny(
            "CCL is limited to the two eldest surviving children unless the single-mother exception applies"
        )


LEAVE_RULES = [
    rule_deny_suspended_employee,
    rule_deny_shorter_than_minimum_spell,
    rule_deny_longer_than_maximum_spell,
    rule_deny_commuted_leave_without_eligible_basis,
    rule_deny_maternity_leave_without_supported_context,
    rule_deny_paternity_leave_without_supported_context,
    rule_deny_child_care_leave_without_supported_context,
    rule_deny_insufficient_balance,
]


__all__ = [
    "LeaveFacts",
    "LEAVE_RULES",
    "rule_deny_suspended_employee",
    "rule_deny_insufficient_balance",
    "rule_deny_shorter_than_minimum_spell",
    "rule_deny_longer_than_maximum_spell",
    "rule_deny_commuted_leave_without_eligible_basis",
    "rule_deny_maternity_leave_without_supported_context",
    "rule_deny_paternity_leave_without_supported_context",
    "rule_deny_child_care_leave_without_supported_context",
]
