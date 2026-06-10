from __future__ import annotations

from pathlib import Path
import sys

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app_platform.forms.infrastructure.service import (
    RuleContext,
    RuleEvaluator,
    WorkflowStage,
    get_resolved_form,
    load_schema,
    validate_form_data,
)


def test_get_resolved_form_rejects_invalid_workflow_stage() -> None:
    with pytest.raises(ValueError, match="Invalid workflow_stage"):
        get_resolved_form(employment_type="REGULAR", workflow_stage="NOT_A_STAGE")


def test_validate_form_data_rejects_invalid_employment_type() -> None:
    with pytest.raises(ValueError, match="Invalid employment_type"):
        validate_form_data(
            data={"full_name": "Example"},
            employment_type="TEMP",
            workflow_stage="DRAFT",
        )


def test_department_code_is_readonly_at_locked_stage() -> None:
    schema = load_schema()
    evaluator = RuleEvaluator(schema, RuleContext(workflow_stage=WorkflowStage.LOCKED))
    assert evaluator._is_readonly("department_code") is True


def test_load_schema_returns_defensive_copy() -> None:
    baseline = load_schema()
    modified = load_schema()
    assert modified is not baseline

    original_version = baseline.get("_metadata", {}).get("version")
    modified.setdefault("_metadata", {})["version"] = "mutated"

    fresh = load_schema()
    assert fresh.get("_metadata", {}).get("version") == original_version


def test_validate_form_data_accepts_employee_profile_field_aliases() -> None:
    errors = validate_form_data(
        data={
            "full_name": "Alias Compatible Employee",
            "gender": "Male",
            "date_of_birth": "1990-01-15",
            "mobile_primary": "9999999999",
            "employment_type": "OUTSOURCED",
            "current_department_id": "HR",
            "current_designation_id": "ASO",
            "outsourcing_agency": "Agency-X",
        },
        employment_type="OUTSOURCED",
        workflow_stage="DRAFT",
    )

    missing_required_fields = {e["field_id"] for e in errors if e.get("error_type") == "required"}
    assert "mobile_number" not in missing_required_fields
    assert "department_code" not in missing_required_fields
    assert "designation_code" not in missing_required_fields


def test_validate_form_data_rejects_hidden_contractual_field_submission() -> None:
    errors = validate_form_data(
        data={
            "full_name": "Contractual Employee",
            "gender": "Male",
            "date_of_birth": "1990-01-15",
            "mobile_primary": "9999999999",
            "employment_type": "CONTRACTUAL",
            "current_department_id": "HR",
            "current_designation_id": "ASO",
            "pension_scheme": "NPS",
        },
        employment_type="CONTRACTUAL",
        workflow_stage="DRAFT",
    )

    forbidden_fields = {e["field_id"] for e in errors if e.get("error_type") == "forbidden"}
    assert "pension_scheme" in forbidden_fields


def test_validate_form_data_accepts_fixed_pay_employment_type() -> None:
    errors = validate_form_data(
        data={
            "full_name": "Fixed Pay Employee",
            "gender": "Female",
            "date_of_birth": "1992-05-12",
            "mobile_primary": "9862001432",
            "employment_type": "FIXED_PAY",
            "current_department_id": "GAD",
            "current_designation_id": "EXECUTIVE_SECRETARY",
            "engagement_order_no": "FP-TEST-2026-001",
            "engagement_order_date": "2026-05-12",
            "date_of_initial_engagement": "2026-05-12",
            "fixed_monthly_amount": 25000,
        },
        employment_type="FIXED_PAY",
        workflow_stage="DRAFT",
    )

    assert errors == []
