from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.leave_attendance.domain.leave_rules import compute_leave_balances, normalize_leave_type_record


def test_compute_leave_balances_uses_lifetime_cap_for_child_care_leave() -> None:
    leave_type = normalize_leave_type_record(
        {
            "code": "CCL",
            "description": "Child Care Leave",
            "leave_code": "CCL",
            "max_days_per_year": 730,
            "applicable_employment_types": ["REG"],
        }
    )

    balances = compute_leave_balances(
        leave_types=[leave_type],
        employment_type_code="REG",
        account=None,
        service_start_date="2020-01-01",
        year_used={"CCL": 12.0},
        total_used={"CCL": 400.0},
    )

    assert balances["CCL"]["max_days_lifetime"] == 730
    assert balances["CCL"]["used_days_year"] == 0.0
    assert balances["CCL"]["used_days_total"] == 400.0
    assert balances["CCL"]["available_days"] == 330.0


def test_compute_leave_balances_derives_commuted_leave_from_half_pay_leave() -> None:
    leave_types = [
        normalize_leave_type_record(
            {
                "code": "HPL",
                "description": "Half Pay Leave",
                "leave_code": "HPL",
                "max_days_per_year": 20,
                "is_accumulative": True,
                "applicable_employment_types": ["REG"],
            }
        ),
        normalize_leave_type_record(
            {
                "code": "CML",
                "description": "Commuted Leave",
                "leave_code": "CML",
                "applicable_employment_types": ["REG"],
            }
        ),
    ]

    balances = compute_leave_balances(
        leave_types=leave_types,
        employment_type_code="REG",
        account={"half_pay_leave_balance": 24.0},
        service_start_date="2020-01-01",
        year_used={},
        total_used={},
    )

    assert balances["HPL"]["available_days"] == 24.0
    assert balances["CML"]["available_days"] == 12.0
    assert balances["CML"]["balance_strategy"] == "hpl_half"


def test_compute_leave_balances_does_not_expose_fake_balance_for_maternity_leave() -> None:
    leave_type = normalize_leave_type_record(
        {
            "code": "ML",
            "description": "Maternity Leave",
            "leave_code": "ML",
            "max_days_per_year": 180,
            "applicable_employment_types": ["REG"],
        }
    )

    balances = compute_leave_balances(
        leave_types=[leave_type],
        employment_type_code="REG",
        account=None,
        service_start_date="2020-01-01",
        year_used={"ML": 0.0},
        total_used={"ML": 0.0},
    )

    assert balances["ML"]["balance_strategy"] == "non_debited_special"
    assert balances["ML"]["available_days"] is None


def test_compute_leave_balances_uses_annual_cl_cap_even_with_stale_or_missing_ledger() -> None:
    leave_type = normalize_leave_type_record(
        {
            "code": "CL",
            "description": "Casual Leave",
            "leave_code": "CL",
            "max_days_per_year": 8,
            "applicable_employment_types": ["REG"],
        }
    )

    missing_account_balances = compute_leave_balances(
        leave_types=[leave_type],
        employment_type_code="REG",
        account=None,
        service_start_date="2020-01-01",
        year_used={"CL": 2.0},
        total_used={},
    )
    stale_account_balances = compute_leave_balances(
        leave_types=[leave_type],
        employment_type_code="REG",
        account={"casual_leave_balance": 0.0},
        service_start_date="2020-01-01",
        year_used={"CL": 2.0},
        total_used={},
    )

    assert missing_account_balances["CL"]["balance_strategy"] == "ledger"
    assert missing_account_balances["CL"]["used_days_year"] == 2.0
    assert missing_account_balances["CL"]["available_days"] == 6.0
    assert stale_account_balances["CL"]["available_days"] == 6.0


def test_normalize_leave_type_record_applies_dopt_spell_defaults() -> None:
    casual_leave = normalize_leave_type_record(
        {
            "code": "CL",
            "description": "Casual Leave",
            "leave_code": "CL",
            "max_days_per_year": 8,
            "applicable_employment_types": ["REG"],
        }
    )
    child_care_leave = normalize_leave_type_record(
        {
            "code": "CCL",
            "description": "Child Care Leave",
            "leave_code": "CCL",
            "max_days_per_year": 730,
            "applicable_employment_types": ["REG"],
        }
    )

    assert casual_leave["max_days_per_spell"] == 5
    assert child_care_leave["min_days_per_spell"] == 5
    assert child_care_leave["max_days_lifetime"] == 730
    assert casual_leave["balance_strategy"] == "ledger"
    assert child_care_leave["balance_strategy"] == "lifetime_cap"