from __future__ import annotations

from contexts.employee_master.identity.schemas.field_policies import DATA_ENTRY_EDITABLE_FIELDS


def test_data_entry_editable_fields_exclude_aadhaar_number() -> None:
    assert "aadhaar_number" not in DATA_ENTRY_EDITABLE_FIELDS


def test_data_entry_editable_fields_exclude_profile_owned_assignment_fields() -> None:
    assert "employment_type" not in DATA_ENTRY_EDITABLE_FIELDS
    assert "date_of_initial_engagement" not in DATA_ENTRY_EDITABLE_FIELDS
    assert "current_department_id" not in DATA_ENTRY_EDITABLE_FIELDS