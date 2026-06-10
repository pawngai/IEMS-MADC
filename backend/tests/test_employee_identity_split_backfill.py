from __future__ import annotations

from scripts.mongodb.employee_identity_split_support import (
    MIGRATION_MARKER,
    build_split_documents,
)


def test_build_split_documents_splits_identity_extension_and_projection() -> None:
    identity, extension, projection = build_split_documents(
        {
            "employee_id": "EMP-1",
            "employee_code": "MADC-2020-0001",
            "full_name": "Asha Employee",
            "gender": "Female",
            "date_of_birth": "1991-01-10",
            "employment_type": "REGULAR",
            "date_of_initial_engagement": "2020-06-01",
            "current_department_id": "HR",
            "current_designation_id": "ASO",
            "employee_status": "ACTIVE",
            "father_name": "Parent",
            "contact": {
                "mobile_primary": "9876543210",
                "email_personal": "asha@example.com",
            },
            "identifiers": {
                "aadhaar_number": "123456789012",
            },
            "workflow_status": "DRAFT",
            "employee_section_completed": False,
            "data_entry_section_completed": True,
            "created_at": "2026-03-01T00:00:00+00:00",
            "updated_at": "2026-03-02T00:00:00+00:00",
            "version": 3,
        },
        migrated_at="2026-03-14T00:00:00+00:00",
    )

    assert identity["employee_id"] == "EMP-1"
    assert identity["full_name"] == "Asha Employee"
    assert identity["employee_status"] == "ACTIVE"
    assert identity["identity_migration_marker"] == MIGRATION_MARKER

    assert extension["employee_id"] == "EMP-1"
    assert extension["father_name"] == "Parent"
    assert extension["contact"]["mobile_primary"] == "9876543210"
    assert extension["identifiers"]["aadhaar_number"] == "123456789012"
    assert extension["profile_extension_migration_marker"] == MIGRATION_MARKER

    assert projection["employee_id"] == "EMP-1"
    assert projection["full_name"] == "Asha Employee"
    assert projection["contact"]["mobile_primary"] == "9876543210"
    assert projection["read_model_migration_marker"] == MIGRATION_MARKER
