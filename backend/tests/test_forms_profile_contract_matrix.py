from __future__ import annotations

from pathlib import Path
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from contexts.employee_master.identity.schemas.commands import EmployeeIdentityCreate
from contexts.employee_master.profile.schemas.commands import EmployeeProfileExtensionUpsert
from app_platform.forms.infrastructure.service import (
    EmploymentType,
    FIELD_ALIASES,
    REQUIRED_RULES,
    RuleContext,
    RuleEvaluator,
    WorkflowStage,
    load_schema,
)


def _profile_create_field_names() -> set[str]:
    return set(EmployeeIdentityCreate.model_fields.keys())


def _profile_extension_field_names() -> set[str]:
    return set(EmployeeProfileExtensionUpsert.model_fields.keys())


def test_contract_matrix_core_required_fields_are_covered() -> None:
    profile_fields = _profile_create_field_names()

    core_forms_required_fields = {
        "full_name",
        "gender",
        "date_of_birth",
    }

    missing = sorted(field for field in core_forms_required_fields if field not in profile_fields)
    assert not missing, f"Core forms required fields missing in EmployeeIdentityCreate: {missing}"


def test_contract_matrix_identity_aliases_bridge_forms_and_identity_fields() -> None:
    profile_fields = _profile_create_field_names()

    critical_identity_aliases = {
        "designation_code",
    }

    for forms_field in critical_identity_aliases:
        assert forms_field in FIELD_ALIASES, f"Missing alias mapping for forms field '{forms_field}'"
        alias_targets = FIELD_ALIASES[forms_field]
        assert any(target in profile_fields for target in alias_targets), (
            f"Alias mapping for '{forms_field}' does not map to EmployeeIdentityCreate fields. "
            f"Candidates: {alias_targets}"
        )


def test_contract_matrix_extension_aliases_bridge_forms_and_extension_fields() -> None:
    extension_fields = _profile_extension_field_names()

    critical_extension_aliases = {
        "mobile_number",
        "department_code",
    }

    for forms_field in critical_extension_aliases:
        assert forms_field in FIELD_ALIASES, f"Missing alias mapping for forms field '{forms_field}'"
        alias_targets = FIELD_ALIASES[forms_field]
        assert any(target in extension_fields for target in alias_targets), (
            f"Alias mapping for '{forms_field}' does not map to EmployeeProfileExtensionUpsert fields. "
            f"Candidates: {alias_targets}"
        )


def test_contract_matrix_required_rules_include_critical_bridge_fields() -> None:
    for forms_field in ("mobile_number", "department_code", "designation_code", "service_group", "pension_scheme"):
        assert forms_field in REQUIRED_RULES, f"Expected REQUIRED_RULES to include '{forms_field}'"


def test_contract_matrix_service_history_fields_are_not_extension_fields() -> None:
    profile_fields = _profile_extension_field_names()
    for field_name in ("service", "pension_scheme"):
        assert field_name not in profile_fields, (
            f"Did not expect EmployeeProfileExtensionUpsert to contain service-history field '{field_name}'"
        )


def test_contract_matrix_leave_eligibility_family_fields_are_not_extension_fields() -> None:
    profile_fields = _profile_extension_field_names()
    for field_name in ("surviving_children_count", "is_single_mother"):
        assert field_name not in profile_fields, f"Did not expect EmployeeProfileExtensionUpsert to contain '{field_name}'"


def test_contract_matrix_outsourced_requires_outsourcing_agency() -> None:
    evaluator = RuleEvaluator(
        load_schema(),
        RuleContext(
            employment_type=EmploymentType.OUTSOURCED,
            workflow_stage=WorkflowStage.DRAFT,
        ),
    )
    assert "outsourcing_agency" in set(evaluator.get_required_fields())


def test_contract_matrix_regular_requires_service_group_and_pension_scheme() -> None:
    evaluator = RuleEvaluator(
        load_schema(),
        RuleContext(
            employment_type=EmploymentType.REGULAR,
            workflow_stage=WorkflowStage.DRAFT,
        ),
    )
    required = set(evaluator.get_required_fields())
    assert "service_group" in required
    assert "pension_scheme" in required
