from __future__ import annotations

import os
import sys

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.leave_attendance.infrastructure import gateway as leave_gateway
from contexts.leave_attendance.infrastructure import gateway_helpers as leave_gateway_helpers
from contexts.leave_attendance.infrastructure.gateway import LeaveMongoGateway
from contexts.leave_attendance.contracts.dto import LeaveApplicationCreateDTO


class _FakeDb:
    class _FakeCollection:
        async def find_one(self, *_args, **_kwargs):
            return None

        async def update_one(self, *_args, **_kwargs):
            return None

    leave_applications = object()
    leave_ledger_entries = _FakeCollection()
    service_book_part_ii_a = _FakeCollection()


class _FakeLeaveRepository:
    def __init__(self) -> None:
        self._db = object()
        self.account = None
        self.updated_account = None
        self.updated_employee_id = None
        self.updated_upsert = None

    async def find_leave_account(self, employee_id: str):
        assert employee_id == "EMP-1"
        return self.account

    async def update_leave_account(self, employee_id: str, update: dict, *, upsert: bool = False, session=None):
        assert session is None
        self.updated_employee_id = employee_id
        self.updated_account = update
        self.updated_upsert = upsert


@pytest.mark.asyncio
async def test_leave_balance_department_user_without_department_mapping_is_forbidden(
    monkeypatch,
):
    gateway = LeaveMongoGateway(_FakeDb())

    async def fake_find_employee_profile(_repo, _employee_id):
        return {
            "employee_id": "EMP-1",
            "employment_type": "REGULAR",
            "current_department_id": "FIN",
            "date_of_initial_engagement": "2020-01-01",
        }

    async def fake_compute_leave_balances(*_args, **_kwargs):
        return {"EL": {"available": 10}}

    monkeypatch.setattr(leave_gateway, "_find_employee_profile", fake_find_employee_profile)
    monkeypatch.setattr(leave_gateway, "_fetch_leave_balances", fake_compute_leave_balances)

    current_user = {
        "sub": "u-1",
        "authorities": ["HOD"],
        "permissions": ["LEAVE_READ_ALL"],
    }

    with pytest.raises(HTTPException) as exc:
        await gateway.get_leave_balances("EMP-1", current_user=current_user)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_leave_balance_self_user_with_read_own_is_allowed(monkeypatch):
    gateway = LeaveMongoGateway(_FakeDb())

    async def fake_find_employee_profile(_repo, employee_id):
        return {
            "employee_id": employee_id,
            "employment_type": "REGULAR",
            "current_department_id": "FIN",
            "date_of_initial_engagement": "2020-01-01",
        }

    async def fake_compute_leave_balances(*_args, **_kwargs):
        return {"EL": {"available_days": 10}}

    monkeypatch.setattr(leave_gateway, "_find_employee_profile", fake_find_employee_profile)
    monkeypatch.setattr(leave_gateway, "_fetch_leave_balances", fake_compute_leave_balances)

    current_user = {
        "sub": "u-ess-1",
        "employee_id": "EMP-1",
        "authorities": ["EMPLOYEE"],
        "permissions": ["LEAVE_READ_OWN"],
    }

    result = await gateway.get_leave_balances("EMP-1", current_user=current_user)

    assert result == {"employee_id": "EMP-1", "balances": {"EL": {"available_days": 10}}}


@pytest.mark.asyncio
async def test_ensure_initial_leave_account_persists_computed_opening_account(monkeypatch):
    repository = _FakeLeaveRepository()

    async def fake_build_initial_leave_account(_repository, *, employee_id: str, user_id: str, **_kwargs):
        assert employee_id == "EMP-1"
        assert user_id == "u-ess-1"
        return {
            "id": "ledger-1",
            "employee_id": employee_id,
            "earned_leave_balance": 42.5,
            "half_pay_leave_balance": 28.33,
            "casual_leave_balance": 8.0,
            "transactions": [],
            "yearly_summary": {},
        }

    monkeypatch.setattr(
        leave_gateway_helpers,
        "_build_initial_leave_account",
        fake_build_initial_leave_account,
    )

    account = await leave_gateway_helpers._ensure_initial_leave_account(
        repository,
        employee_id="EMP-1",
        user_id="u-ess-1",
        employment_type_code="REG",
        service_start_date="2025-01-15",
    )

    assert account is not None
    assert repository.updated_employee_id == "EMP-1"
    assert repository.updated_account == {"$set": account}
    assert repository.updated_upsert is True


@pytest.mark.asyncio
async def test_resolve_service_start_date_falls_back_to_service_book_appointment(monkeypatch):
    repository = _FakeLeaveRepository()

    async def fake_get_employee_initial_appointment_date(_db, *, employee_id: str):
        assert employee_id == "EMP-1"
        return "2024-04-01"

    monkeypatch.setattr(
        leave_gateway_helpers,
        "get_employee_initial_appointment_date",
        fake_get_employee_initial_appointment_date,
    )

    result = await leave_gateway_helpers._resolve_service_start_date(
        repository,
        employee_id="EMP-1",
        profile={"employee_id": "EMP-1", "employment_type": "REGULAR"},
    )

    assert result == "2024-04-01"


@pytest.mark.asyncio
async def test_apply_leave_forbids_role_user_even_with_apply_permission(monkeypatch):
    gateway = LeaveMongoGateway(_FakeDb())

    async def fail_if_profile_lookup_runs(*_args, **_kwargs):
        raise AssertionError("role user should be rejected before profile lookup")

    monkeypatch.setattr(leave_gateway, "_find_employee_profile", fail_if_profile_lookup_runs)

    current_user = {
        "sub": "u-role-1",
        "employee_id": "EST-001",
        "authorities": ["APPROVING_AUTHORITY"],
        "permissions": ["LEAVE_APPLY_OWN"],
    }

    payload = LeaveApplicationCreateDTO(
        leave_type_code="EL",
        from_date="2026-03-20",
        to_date="2026-03-20",
        reason="Role user should not apply own leave",
        contact_during_leave="9999999999",
    )

    with pytest.raises(HTTPException) as exc:
        await gateway.apply_leave(payload, current_user=current_user)

    assert exc.value.status_code == 403
    assert exc.value.detail == "Leave can only be applied from employee self-service account"


@pytest.mark.asyncio
async def test_apply_leave_persists_supporting_attachments(monkeypatch):
    gateway = LeaveMongoGateway(_FakeDb())
    inserted: dict = {}

    async def fake_context(_repo, _payload, *, current_user):
        return {
            "employee_id": current_user["employee_id"],
            "days_applied": 2,
            "balance_info": {"available_days": 10},
        }

    async def fake_insert_leave_application(record):
        inserted.update(record)

    async def fake_normalize_leave_attachments(_attachments, *, current_user, db=None):
        return [
            {
                "url": "/api/documents/files/evidence.pdf",
                "filename": "evidence.pdf",
                "original_name": "medical-note.pdf",
                "file_size": 2048,
                "content_type": "application/pdf",
            }
        ]

    monkeypatch.setattr(leave_gateway, "_build_leave_application_context", fake_context)
    monkeypatch.setattr(leave_gateway, "_normalize_leave_attachments", fake_normalize_leave_attachments)
    monkeypatch.setattr(gateway._repository, "insert_leave_application", fake_insert_leave_application)

    payload = LeaveApplicationCreateDTO(
        leave_type_code="CML",
        from_date="2026-03-20",
        to_date="2026-03-21",
        reason="Supporting medical follow-up",
        contact_during_leave="9999999999",
        medical_certificate_provided=True,
        attachments=[
            {
                "url": "/api/documents/files/evidence.pdf",
                "filename": "evidence.pdf",
                "original_name": "medical-note.pdf",
                "file_size": 2048,
                "content_type": "application/pdf",
            }
        ],
    )

    result = await gateway.apply_leave(
        payload,
        current_user={
            "sub": "u-ess-1",
            "employee_id": "EMP-1",
            "authorities": ["EMPLOYEE"],
            "permissions": ["LEAVE_APPLY_OWN"],
        },
    )

    assert inserted["attachments"] == [
        {
            "url": "/api/documents/files/evidence.pdf",
            "filename": "evidence.pdf",
            "original_name": "medical-note.pdf",
            "file_size": 2048,
            "content_type": "application/pdf",
        }
    ]
    assert inserted["eligibility_context_version"] == 1
    assert result["attachments"][0]["filename"] == "evidence.pdf"


@pytest.mark.asyncio
async def test_apply_leave_requires_supporting_document_for_commuted_leave(monkeypatch):
    gateway = LeaveMongoGateway(_FakeDb())

    async def fake_context(_repo, _payload, *, current_user):
        return {
            "employee_id": current_user["employee_id"],
            "days_applied": 2,
            "balance_info": {"available_days": 10},
        }

    monkeypatch.setattr(leave_gateway, "_build_leave_application_context", fake_context)

    payload = LeaveApplicationCreateDTO(
        leave_type_code="CML",
        from_date="2026-03-20",
        to_date="2026-03-21",
        reason="Commuted leave with medical grounds",
        contact_during_leave="9999999999",
        medical_certificate_provided=True,
        attachments=[],
    )

    with pytest.raises(HTTPException) as exc:
        await gateway.apply_leave(
            payload,
            current_user={
                "sub": "u-ess-1",
                "employee_id": "EMP-1",
                "authorities": ["EMPLOYEE"],
                "permissions": ["LEAVE_APPLY_OWN"],
            },
        )

    assert exc.value.status_code == 422
    assert exc.value.detail == (
        "Commuted leave requires a supporting document. Upload the medical certificate."
    )
