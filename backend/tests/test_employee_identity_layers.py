from __future__ import annotations

import pytest

from contexts.employee_identity.application import identity_interface
from contexts.employee_profile.domain.identity_layers import (
    compose_employee_record_view,
    extract_identity_patch,
    extract_extension_patch,
)
from contexts.employee_profile.infrastructure.gateway import _refresh_profile_projection


class _FakeCollection:
    def __init__(self, document=None) -> None:
        self.document = document
        self.update_calls: list[dict] = []
        self.deleted_queries: list[dict] = []

    async def find_one(self, _query, _projection):
        return self.document

    async def update_one(self, query, update, upsert=False):
        self.update_calls.append({"query": query, "update": update, "upsert": upsert})

    async def delete_one(self, query):
        self.deleted_queries.append(query)


class _FakeIdentityRepo:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows

    async def list_identities(self, *, query, skip=0, limit=20):
        rows = self.rows
        if "current_department_id" in query:
            rows = [
                row
                for row in rows
                if row.get("current_department_id") == query["current_department_id"]
            ]
        if "employment_type" in query:
            rows = [
                row
                for row in rows
                if row.get("employment_type") == query["employment_type"]
            ]
        return rows[skip : skip + limit]


@pytest.mark.asyncio
async def test_list_employee_ids_by_department_unions_summary_and_profile_rows(monkeypatch) -> None:
    async def _summary_ids(_db, *, employment_type=None, department_code=None, limit=5000):
        _ = (employment_type, department_code, limit)
        return ["EMP-SUMMARY", "EMP-DUPLICATE"]

    async def _profiles(_db, *, employment_type=None, department_code=None, limit=500, **_kwargs):
        _ = (employment_type, department_code, limit)
        return [
            {"employee_id": "EMP-PROFILE"},
            {"employee_id": "EMP-DUPLICATE"},
        ]

    monkeypatch.setattr(identity_interface, "list_employee_ids_by_service_summary", _summary_ids)
    monkeypatch.setattr(identity_interface, "list_profiles", _profiles)
    monkeypatch.setattr(identity_interface, "_repo", lambda _db: _FakeIdentityRepo([]))

    ids = await identity_interface.list_employee_ids_by_department(
        object(),
        department_code="PWD",
    )

    assert ids == ["EMP-SUMMARY", "EMP-DUPLICATE", "EMP-PROFILE"]


def test_extract_extension_patch_preserves_namespaced_contact_and_identifier_updates() -> None:
    patch = extract_extension_patch(
        {
            "father_name": "Parent Name",
            "contact.mobile_primary": "9876543210",
            "identifiers.pan_number": "ABCDE1234F",
        }
    )

    assert patch["father_name"] == "Parent Name"
    assert patch["contact.mobile_primary"] == "9876543210"
    assert patch["identifiers.pan_number"] == "ABCDE1234F"


def test_extract_extension_patch_keeps_non_regular_setup_fields_in_profile_extension() -> None:
    patch = extract_extension_patch(
        {
            "employment_type": "FIXED_PAY",
            "current_department_id": "GAD",
            "current_designation_id": "EXECUTIVE_SECRETARY",
            "date_of_initial_engagement": "2026-05-12",
            "engagement_order_no": "FP-TEST-2026-001",
            "fixed_monthly_amount": 25000,
        }
    )

    assert patch["employment_type"] == "FIXED_PAY"
    assert patch["current_department_id"] == "GAD"
    assert "current_designation_id" not in patch
    assert patch["date_of_initial_engagement"] == "2026-05-12"
    assert patch["engagement_order_no"] == "FP-TEST-2026-001"
    assert patch["fixed_monthly_amount"] == 25000


def test_extract_identity_patch_keeps_only_identity_owned_assignment_fields() -> None:
    patch = extract_identity_patch(
        {
            "employment_type": "FIXED_PAY",
            "current_department_id": "GAD",
            "current_designation_id": "EXECUTIVE_SECRETARY",
            "date_of_initial_engagement": "2026-05-12",
            "engagement_order_no": "FP-TEST-2026-001",
            "fixed_monthly_amount": 25000,
        }
    )

    assert "employment_type" not in patch
    assert "current_department_id" not in patch
    assert patch["current_designation_id"] == "EXECUTIVE_SECRETARY"
    assert "date_of_initial_engagement" not in patch
    assert "engagement_order_no" not in patch
    assert "fixed_monthly_amount" not in patch


def test_compose_employee_record_view_defaults_missing_workflow_status_to_draft() -> None:
    composed = compose_employee_record_view(
        {"employee_id": "EMP-1", "full_name": "Demo Employee"},
        {"employee_id": "EMP-1", "contact": {"mobile_primary": "9876543210"}},
    )

    assert composed["workflow_status"] == "DRAFT"


def test_compose_employee_record_view_does_not_leak_identity_workflow_status() -> None:
    composed = compose_employee_record_view(
        {
            "employee_id": "EMP-1",
            "full_name": "Demo Employee",
            "workflow_status": "ACTIVE",
        },
        {"employee_id": "EMP-1"},
    )

    assert composed["workflow_status"] == "DRAFT"
    assert composed["identity_workflow_status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_refresh_profile_projection_keeps_created_at_out_of_set_clause() -> None:
    db = type("_FakeDb", (), {})()
    db.employee_identities = _FakeCollection(
        {
            "employee_id": "EMP-1",
            "full_name": "Demo Employee",
            "created_at": "2025-01-01T00:00:00+00:00",
        }
    )
    db.employee_profile_extensions = _FakeCollection(
        {
            "employee_id": "EMP-1",
            "workflow_status": "DRAFT",
            "created_at": "2025-01-01T00:00:00+00:00",
        }
    )
    db.employee_profile_read_models = _FakeCollection()

    await _refresh_profile_projection(db, "EMP-1")

    assert not db.employee_profile_read_models.deleted_queries
    update_call = db.employee_profile_read_models.update_calls[0]
    assert update_call["upsert"] is True
    assert "created_at" not in update_call["update"]["$set"]
    assert update_call["update"]["$setOnInsert"]["created_at"] == "2025-01-01T00:00:00+00:00"
