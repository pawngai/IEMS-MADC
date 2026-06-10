from contexts.employee_profile.contracts.workflow_status_utils import (
    normalize_employee_workflow_status,
    normalize_workflow_status,
    workflow_status_filter_values,
)


def test_normalize_workflow_status_keeps_strict_values() -> None:
    assert normalize_workflow_status(" locked ") == "LOCKED"
    assert normalize_workflow_status("attested") == "ATTESTED"


def test_workflow_status_filter_values_no_compat_expansion() -> None:
    assert workflow_status_filter_values(None) == []
    assert workflow_status_filter_values("LOCKED") == ["LOCKED"]
    assert workflow_status_filter_values("ATTESTED") == ["ATTESTED"]


def test_normalize_employee_workflow_status_no_alias_rewrite() -> None:
    profile = {"employee_id": "E001", "workflow_status": "attested"}

    normalized = normalize_employee_workflow_status(profile)

    assert normalized["workflow_status"] == "ATTESTED"


def test_normalize_employee_workflow_status_maps_identity_active_to_profile_draft() -> None:
    profile = {"employee_id": "E002", "workflow_status": "ACTIVE"}

    normalized = normalize_employee_workflow_status(profile)

    assert normalized["workflow_status"] == "DRAFT"
