from __future__ import annotations

import os
import sys

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.leave_attendance.application.evaluate_leave_request import (
    evaluate_leave_request,
)
from contexts.leave_attendance.domain.leave_request_policy import LeaveFacts
from contexts.leave_attendance.application.service import LeaveApplicationService
from contexts.leave_attendance.contracts.dto import LeaveApplicationCreateDTO


class _FakeLeaveGateway:
    def __init__(self) -> None:
        self.apply_called = False
        self.policy_context_calls: list[tuple[str, dict]] = []
        self.policy_context = {
            "employee_id": "EMP-1",
            "employee_status": "ACTIVE",
            "leave_type_code": "EL",
            "leave_days": 3.0,
            "available_balance": 2.0,
            "min_days_per_spell": None,
            "max_days_per_spell": None,
            "employee_gender": None,
            "marital_status": None,
            "probation_period_months": None,
            "surviving_children_count": None,
            "is_single_mother": None,
            "leave_from_date": "2026-04-01",
            "leave_to_date": "2026-04-03",
            "medical_certificate_provided": None,
            "commuted_leave_basis": None,
            "expected_delivery_date": None,
            "childbirth_date": None,
            "adoption_date": None,
            "child_date_of_birth": None,
            "child_has_disability": None,
            "child_order": None,
        }

    async def get_leave_application_policy_context(
        self, payload: LeaveApplicationCreateDTO, *, current_user: dict
    ) -> dict:
        self.policy_context_calls.append((payload.leave_type_code, dict(current_user)))
        return {
            **self.policy_context,
            "leave_type_code": payload.leave_type_code,
            "leave_from_date": payload.from_date,
            "leave_to_date": payload.to_date,
        }

    async def get_leave_balances(self, employee_id: str, *, current_user: dict) -> dict:
        raise NotImplementedError

    async def apply_leave(self, payload: LeaveApplicationCreateDTO, *, current_user: dict) -> dict:
        self.apply_called = True
        return {
            "id": "LV-1",
            "employee_id": current_user.get("employee_id"),
            "status": "SUBMITTED",
            "leave_type_code": payload.leave_type_code,
            "days_applied": 3,
        }

    async def list_my_leaves(self, *, current_user: dict) -> list[dict]:
        raise NotImplementedError

    async def list_leaves(self, *, status, leave_type_code, employee_id, current_user: dict) -> list[dict]:
        raise NotImplementedError

    async def recommend_leave(self, leave_id: str, action, *, current_user: dict) -> dict:
        raise NotImplementedError

    async def sanction_leave(self, leave_id: str, action, *, current_user: dict) -> dict:
        raise NotImplementedError

    async def reject_leave(self, leave_id: str, action, *, current_user: dict) -> dict:
        raise NotImplementedError

    async def cancel_leave(self, leave_id: str, action, *, current_user: dict) -> dict:
        raise NotImplementedError


def _policy_evaluator(facts: dict) -> dict:
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


@pytest.mark.asyncio
async def test_leave_policy_evaluator_uses_real_days_and_balance() -> None:
    gateway = _FakeLeaveGateway()
    service = LeaveApplicationService(
        gateway=gateway,
        outbox_repo=None,
        leave_rules_evaluator=_policy_evaluator,
    )
    payload = LeaveApplicationCreateDTO(
        leave_type_code="EL",
        from_date="2026-04-01",
        to_date="2026-04-03",
        reason="Family event",
        contact_during_leave="9999999999",
    )
    current_user = {
        "sub": "u-1",
        "employee_id": "EMP-1",
        "employee_status": "ACTIVE",
    }

    with pytest.raises(HTTPException) as exc:
        await service.apply_leave(payload, current_user=current_user)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Leave days exceed available balance"
    assert gateway.policy_context_calls == [("EL", current_user)]
    assert gateway.apply_called is False


def test_leave_policy_denies_casual_leave_over_five_days_per_spell() -> None:
    decision = evaluate_leave_request(
        LeaveFacts(
            employee_id="EMP-1",
            employee_status="ACTIVE",
            leave_type_code="CL",
            leave_days=6,
            available_balance=8,
            min_days_per_spell=None,
            max_days_per_spell=5,
            employee_gender=None,
            marital_status=None,
            probation_period_months=None,
            surviving_children_count=None,
            is_single_mother=None,
            leave_from_date="2026-04-01",
            leave_to_date="2026-04-06",
            medical_certificate_provided=None,
            commuted_leave_basis=None,
            expected_delivery_date=None,
            childbirth_date=None,
            adoption_date=None,
            child_date_of_birth=None,
            child_has_disability=None,
            child_order=None,
        )
    )

    assert decision.allowed is False
    assert decision.reasons == ["CL cannot exceed 5 days in one spell"]


def test_leave_policy_denies_child_care_leave_shorter_than_five_days() -> None:
    decision = evaluate_leave_request(
        LeaveFacts(
            employee_id="EMP-1",
            employee_status="ACTIVE",
            leave_type_code="CCL",
            leave_days=3,
            available_balance=727,
            min_days_per_spell=5,
            max_days_per_spell=None,
            employee_gender=None,
            marital_status=None,
            probation_period_months=None,
            surviving_children_count=None,
            is_single_mother=None,
            leave_from_date="2026-04-01",
            leave_to_date="2026-04-03",
            medical_certificate_provided=None,
            commuted_leave_basis=None,
            expected_delivery_date=None,
            childbirth_date=None,
            adoption_date=None,
            child_date_of_birth="2015-06-01",
            child_has_disability=False,
            child_order=1,
        )
    )

    assert decision.allowed is False
    assert decision.reasons == ["CCL requires at least 5 days in one spell"]


def test_leave_policy_denies_commuted_leave_without_medical_or_study_basis() -> None:
    decision = evaluate_leave_request(
        LeaveFacts(
            employee_id="EMP-1",
            employee_status="ACTIVE",
            leave_type_code="CML",
            leave_days=5,
            available_balance=10,
            min_days_per_spell=None,
            max_days_per_spell=None,
            employee_gender=None,
            marital_status=None,
            probation_period_months=None,
            surviving_children_count=None,
            is_single_mother=None,
            leave_from_date="2026-04-01",
            leave_to_date="2026-04-05",
            medical_certificate_provided=False,
            commuted_leave_basis=None,
            expected_delivery_date=None,
            childbirth_date=None,
            adoption_date=None,
            child_date_of_birth=None,
            child_has_disability=None,
            child_order=None,
        )
    )

    assert decision.allowed is False
    assert decision.reasons == [
        "CML requires a medical certificate or an approved public-interest study basis"
    ]


def test_leave_policy_denies_maternity_leave_without_female_profile_or_event_date() -> None:
    decision = evaluate_leave_request(
        LeaveFacts(
            employee_id="EMP-1",
            employee_status="ACTIVE",
            leave_type_code="ML",
            leave_days=30,
            available_balance=None,
            min_days_per_spell=None,
            max_days_per_spell=180,
            employee_gender="Male",
            marital_status=None,
            probation_period_months=None,
            surviving_children_count=None,
            is_single_mother=None,
            leave_from_date="2026-04-01",
            leave_to_date="2026-04-30",
            medical_certificate_provided=None,
            commuted_leave_basis=None,
            expected_delivery_date=None,
            childbirth_date=None,
            adoption_date=None,
            child_date_of_birth=None,
            child_has_disability=None,
            child_order=None,
        )
    )

    assert decision.allowed is False
    assert decision.reasons == [
        "ML is only available to female employees under CCS rules",
        "ML requires an expected delivery date or childbirth date",
    ]


def test_leave_policy_denies_paternity_leave_outside_event_window() -> None:
    decision = evaluate_leave_request(
        LeaveFacts(
            employee_id="EMP-1",
            employee_status="ACTIVE",
            leave_type_code="PL",
            leave_days=10,
            available_balance=None,
            min_days_per_spell=None,
            max_days_per_spell=15,
            employee_gender="Male",
            marital_status=None,
            probation_period_months=None,
            surviving_children_count=None,
            is_single_mother=None,
            leave_from_date="2026-09-01",
            leave_to_date="2026-09-10",
            medical_certificate_provided=None,
            commuted_leave_basis=None,
            expected_delivery_date=None,
            childbirth_date="2026-01-01",
            adoption_date=None,
            child_date_of_birth=None,
            child_has_disability=None,
            child_order=None,
        )
    )

    assert decision.allowed is False
    assert decision.reasons == ["PL must start within 180 days of childbirth or adoption"]


def test_leave_policy_denies_child_care_leave_for_third_child_without_exception() -> None:
    decision = evaluate_leave_request(
        LeaveFacts(
            employee_id="EMP-1",
            employee_status="ACTIVE",
            leave_type_code="CCL",
            leave_days=5,
            available_balance=725,
            min_days_per_spell=5,
            max_days_per_spell=None,
            employee_gender="Female",
            marital_status=None,
            probation_period_months=None,
            surviving_children_count=3,
            is_single_mother=False,
            leave_from_date="2026-04-01",
            leave_to_date="2026-04-05",
            medical_certificate_provided=None,
            commuted_leave_basis=None,
            expected_delivery_date=None,
            childbirth_date=None,
            adoption_date=None,
            child_date_of_birth="2018-04-01",
            child_has_disability=False,
            child_order=3,
        )
    )

    assert decision.allowed is False
    assert decision.reasons == [
        "CCL is limited to the two eldest surviving children unless the single-mother exception applies"
    ]


def test_leave_policy_denies_child_care_leave_for_large_family_even_when_request_claims_first_child() -> None:
    decision = evaluate_leave_request(
        LeaveFacts(
            employee_id="EMP-1",
            employee_status="ACTIVE",
            leave_type_code="CCL",
            leave_days=5,
            available_balance=725,
            min_days_per_spell=5,
            max_days_per_spell=None,
            employee_gender="Female",
            marital_status=None,
            probation_period_months=None,
            surviving_children_count=3,
            is_single_mother=False,
            leave_from_date="2026-04-01",
            leave_to_date="2026-04-05",
            medical_certificate_provided=None,
            commuted_leave_basis=None,
            expected_delivery_date=None,
            childbirth_date=None,
            adoption_date=None,
            child_date_of_birth="2012-04-01",
            child_has_disability=False,
            child_order=1,
        )
    )

    assert decision.allowed is False
    assert decision.reasons == [
        "CCL is limited to the two eldest surviving children unless the single-mother exception applies"
    ]