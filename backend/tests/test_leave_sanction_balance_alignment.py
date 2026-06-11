from __future__ import annotations

import os
import sys

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.leave_attendance.contracts.dto import LeaveActionDTO
from contexts.leave_attendance.infrastructure import gateway as leave_gateway
from contexts.leave_attendance.infrastructure.gateway import LeaveMongoGateway, _record_leave_debit


class _FakeDb:
    leave_applications = object()
    leave_ledger_entries = object()


class _FakeRepository:
    def __init__(self, *, leave_record=None, leave_account=None) -> None:
        self.leave_record = leave_record
        self.leave_account = leave_account
        self.leave_updates: list[tuple[str, dict]] = []
        self.inserted_accounts: list[dict] = []
        self.ledger_updates: list[tuple[str, dict, bool]] = []

    async def find_leave_application(self, leave_id: str):
        if not self.leave_record or self.leave_record.get("id") != leave_id:
            return None
        return dict(self.leave_record)

    async def update_leave_application(self, leave_id: str, update: dict) -> None:
        self.leave_updates.append((leave_id, dict(update)))
        if self.leave_record and self.leave_record.get("id") == leave_id:
            self.leave_record.update(update)

    async def find_leave_account(self, employee_id: str):
        if not self.leave_account or self.leave_account.get("employee_id") != employee_id:
            return None
        return dict(self.leave_account)

    async def insert_leave_account(self, account: dict) -> None:
        self.inserted_accounts.append(dict(account))
        self.leave_account = dict(account)

    async def update_leave_account(self, employee_id: str, update: dict, *, upsert: bool = False) -> None:
        self.ledger_updates.append((employee_id, update, upsert))


@pytest.mark.asyncio
async def test_sanction_leave_uses_available_cl_balance_when_ledger_row_is_empty(monkeypatch):
    gateway = LeaveMongoGateway(_FakeDb())
    repository = _FakeRepository(
        leave_record={
            "id": "L-1",
            "employee_id": "EMP-1",
            "leave_type_code": "CL",
            "from_date": "2026-04-21",
            "to_date": "2026-04-22",
            "days_applied": 2.0,
            "applied_by": "u-applicant",
            "status": "RECOMMENDED",
        },
        leave_account={
            "employee_id": "EMP-1",
            "casual_leave_balance": 0.0,
            "earned_leave_balance": 0.0,
            "half_pay_leave_balance": 0.0,
            "transactions": [],
            "yearly_summary": {},
        },
    )
    gateway._repository = repository

    revisions: list[dict] = []

    async def fake_find_employee_profile(_repo, _employee_id):
        return {
            "employee_id": "EMP-1",
            "employment_type": "REGULAR",
            "current_department_id": "ADMIN",
            "date_of_initial_engagement": "2020-01-01",
        }

    async def fake_fetch_leave_balances(*_args, **_kwargs):
        return {
            "CL": {
                "leave_code": "CL",
                "available_days": 8.0,
            }
        }

    async def fake_append_revision(_db, *, part_code, employee_id, payload, actor_user_id):
        revisions.append(
            {
                "part_code": part_code,
                "employee_id": employee_id,
                "payload": payload,
                "actor_user_id": actor_user_id,
            }
        )

    monkeypatch.setattr(leave_gateway, "_find_employee_profile", fake_find_employee_profile)
    monkeypatch.setattr(leave_gateway, "_fetch_leave_balances", fake_fetch_leave_balances)
    monkeypatch.setattr(leave_gateway, "append_revision", fake_append_revision)

    result = await gateway.sanction_leave(
        "L-1",
        LeaveActionDTO(
            remarks="Sanctioned",
            order_number="SB-1",
            order_date="2026-04-12",
        ),
        current_user={
            "sub": "u-sanction",
            "authorities": ["SYSTEM_ADMIN"],
            "permissions": ["LEAVE_SANCTION"],
        },
    )

    assert result["status"] == "SANCTIONED"
    assert repository.ledger_updates
    employee_id, update, upsert = repository.ledger_updates[0]
    assert employee_id == "EMP-1"
    assert upsert is True
    transaction = update["$push"]["transactions"]
    assert transaction["opening_balance"] == 8.0
    assert transaction["closing_balance"] == 6.0
    assert update["$set"]["casual_leave_balance"] == 6.0
    assert revisions
    assert revisions[0]["part_code"] == "SB_PART_VI"
    assert revisions[0]["employee_id"] == "EMP-1"
    assert revisions[0]["actor_user_id"] == "u-sanction"
    assert revisions[0]["payload"]["transaction"]["opening_balance"] == 8.0


@pytest.mark.asyncio
async def test_record_leave_debit_does_not_insert_empty_account_when_debit_fails() -> None:
    repository = _FakeRepository(leave_account=None)

    with pytest.raises(HTTPException) as exc:
        await _record_leave_debit(
            repository,
            db=None,
            employee_id="EMP-1",
            leave_type_code="CL",
            from_date="2026-04-21",
            to_date="2026-04-22",
            days=2.0,
            user_id="u-sanction",
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Insufficient leave balance at sanction time"
    assert repository.inserted_accounts == []
    assert repository.ledger_updates == []


@pytest.mark.asyncio
async def test_record_leave_debit_seeds_initial_account_from_computed_balances(monkeypatch) -> None:
    repository = _FakeRepository(leave_account=None)

    revisions: list[dict] = []

    async def fake_find_employee_profile(_repo, _employee_id):
        return {
            "employee_id": "EMP-1",
            "employment_type": "REGULAR",
            "date_of_initial_engagement": "2024-01-15",
        }

    async def fake_fetch_leave_balances(*_args, **_kwargs):
        return {
            "EL": {"available_days": 70.0},
            "HPL": {"available_days": 46.67},
            "CML": {"available_days": 23.335},
            "LND": {"available_days": 360.0},
            "CL": {"available_days": 8.0},
        }

    async def fake_append_revision(_db, *, part_code, employee_id, payload, actor_user_id):
        revisions.append(
            {
                "part_code": part_code,
                "employee_id": employee_id,
                "payload": payload,
                "actor_user_id": actor_user_id,
            }
        )

    monkeypatch.setattr(leave_gateway, "_find_employee_profile", fake_find_employee_profile)
    monkeypatch.setattr(leave_gateway, "_fetch_leave_balances", fake_fetch_leave_balances)
    monkeypatch.setattr(leave_gateway, "append_revision", fake_append_revision)

    await _record_leave_debit(
        repository,
        db=None,
        employee_id="EMP-1",
        leave_type_code="CL",
        from_date="2026-04-21",
        to_date="2026-04-22",
        days=2.0,
        user_id="u-sanction",
        available_days=8.0,
    )

    assert len(repository.inserted_accounts) == 1
    inserted_account = repository.inserted_accounts[0]
    assert inserted_account["earned_leave_balance"] == 70.0
    assert inserted_account["half_pay_leave_balance"] == 46.67
    assert inserted_account["commuted_leave_balance"] == 23.335
    assert inserted_account["leave_not_due_balance"] == 360.0
    assert inserted_account["casual_leave_balance"] == 8.0
    assert len(repository.ledger_updates) == 1
    update = repository.ledger_updates[0][1]
    assert update["$set"]["casual_leave_balance"] == 6.0
    assert revisions[0]["part_code"] == "SB_PART_VI"
    assert revisions[0]["payload"]["transaction"]["opening_balance"] == 8.0
    assert revisions[0]["payload"]["transaction"]["closing_balance"] == 6.0


@pytest.mark.asyncio
async def test_record_leave_debit_updates_hpl_and_commuted_cache_for_cml(monkeypatch) -> None:
    repository = _FakeRepository(
        leave_account={
            "employee_id": "EMP-1",
            "earned_leave_balance": 0.0,
            "half_pay_leave_balance": 24.0,
            "commuted_leave_balance": 12.0,
            "leave_not_due_balance": 360.0,
            "casual_leave_balance": 0.0,
            "transactions": [],
            "yearly_summary": {},
        }
    )

    revisions: list[dict] = []

    async def fake_append_revision(_db, *, part_code, employee_id, payload, actor_user_id):
        revisions.append(
            {
                "part_code": part_code,
                "employee_id": employee_id,
                "payload": payload,
                "actor_user_id": actor_user_id,
            }
        )

    monkeypatch.setattr(leave_gateway, "append_revision", fake_append_revision)

    await _record_leave_debit(
        repository,
        db=None,
        employee_id="EMP-1",
        leave_type_code="CML",
        from_date="2026-04-21",
        to_date="2026-04-22",
        days=2.0,
        user_id="u-sanction",
    )

    assert len(repository.ledger_updates) == 1
    cml_update = repository.ledger_updates[0][1]
    assert cml_update["$set"]["half_pay_leave_balance"] == 20.0
    assert cml_update["$set"]["commuted_leave_balance"] == 10.0
    assert revisions[0]["part_code"] == "SB_PART_VI"
    assert revisions[0]["payload"]["transaction"]["leave_type"] == "CML"
    assert revisions[0]["payload"]["transaction"]["days_debited"] == 4.0
    assert revisions[0]["payload"]["transaction"]["debit_source_leave_type"] == "HPL"


@pytest.mark.asyncio
async def test_record_leave_debit_updates_lnd_lifetime_tracker(monkeypatch) -> None:
    repository = _FakeRepository(
        leave_account={
            "employee_id": "EMP-1",
            "earned_leave_balance": 0.0,
            "half_pay_leave_balance": 24.0,
            "commuted_leave_balance": 12.0,
            "leave_not_due_balance": 360.0,
            "casual_leave_balance": 0.0,
            "transactions": [],
            "yearly_summary": {},
        }
    )

    revisions: list[dict] = []

    async def fake_append_revision(_db, *, part_code, employee_id, payload, actor_user_id):
        revisions.append(
            {
                "part_code": part_code,
                "employee_id": employee_id,
                "payload": payload,
                "actor_user_id": actor_user_id,
            }
        )

    monkeypatch.setattr(leave_gateway, "append_revision", fake_append_revision)

    await _record_leave_debit(
        repository,
        db=None,
        employee_id="EMP-1",
        leave_type_code="LND",
        from_date="2026-05-01",
        to_date="2026-05-01",
        days=1.0,
        user_id="u-sanction",
        available_days=360.0,
    )

    assert len(repository.ledger_updates) == 1
    lnd_update = repository.ledger_updates[0][1]
    assert lnd_update["$set"]["leave_not_due_balance"] == 359.0
    assert revisions[0]["part_code"] == "SB_PART_VI"
    assert revisions[0]["payload"]["transaction"]["leave_type"] == "LND"


@pytest.mark.asyncio
async def test_sanction_leave_skips_ledger_debit_for_non_debited_special_leave(monkeypatch) -> None:
    gateway = LeaveMongoGateway(_FakeDb())
    repository = _FakeRepository(
        leave_record={
            "id": "L-ML-1",
            "employee_id": "EMP-1",
            "leave_type_code": "ML",
            "from_date": "2026-04-21",
            "to_date": "2026-05-20",
            "days_applied": 30.0,
            "applied_by": "u-applicant",
            "status": "RECOMMENDED",
        },
        leave_account={
            "employee_id": "EMP-1",
            "casual_leave_balance": 0.0,
            "earned_leave_balance": 120.0,
            "half_pay_leave_balance": 60.0,
            "transactions": [],
            "yearly_summary": {},
        },
    )
    gateway._repository = repository

    async def fake_find_employee_profile(_repo, _employee_id):
        return {
            "employee_id": "EMP-1",
            "employment_type": "REGULAR",
            "current_department_id": "ADMIN",
            "date_of_initial_engagement": "2020-01-01",
        }

    async def fake_fetch_leave_balances(*_args, **_kwargs):
        return {
            "ML": {
                "leave_code": "ML",
                "available_days": None,
                "records_ledger_transaction": False,
            }
        }

    monkeypatch.setattr(leave_gateway, "_find_employee_profile", fake_find_employee_profile)
    monkeypatch.setattr(leave_gateway, "_fetch_leave_balances", fake_fetch_leave_balances)

    result = await gateway.sanction_leave(
        "L-ML-1",
        LeaveActionDTO(
            remarks="Sanctioned",
            order_number="SB-ML-1",
            order_date="2026-04-12",
        ),
        current_user={
            "sub": "u-sanction",
            "authorities": ["SYSTEM_ADMIN"],
            "permissions": ["LEAVE_SANCTION"],
        },
    )

    assert result["status"] == "SANCTIONED"
    assert repository.ledger_updates == []


@pytest.mark.asyncio
async def test_sanction_leave_locks_supporting_attachments(monkeypatch) -> None:
    gateway = LeaveMongoGateway(_FakeDb())
    repository = _FakeRepository(
        leave_record={
            "id": "L-LOCK-1",
            "employee_id": "EMP-1",
            "leave_type_code": "EL",
            "from_date": "2026-04-21",
            "to_date": "2026-04-22",
            "days_applied": 2.0,
            "applied_by": "u-applicant",
            "status": "RECOMMENDED",
            "attachments": [{"filename": "support.pdf"}],
        },
        leave_account={
            "employee_id": "EMP-1",
            "casual_leave_balance": 0.0,
            "earned_leave_balance": 120.0,
            "half_pay_leave_balance": 60.0,
            "transactions": [],
            "yearly_summary": {},
        },
    )
    gateway._repository = repository
    captured: list[dict] = []

    async def fake_find_employee_profile(_repo, _employee_id):
        return {
            "employee_id": "EMP-1",
            "employment_type": "REGULAR",
            "current_department_id": "ADMIN",
            "date_of_initial_engagement": "2020-01-01",
        }

    async def fake_fetch_leave_balances(*_args, **_kwargs):
        return {
            "EL": {
                "leave_code": "EL",
                "available_days": 12.0,
                "records_ledger_transaction": False,
            }
        }

    async def fake_lock(attachments, *, leave_id, status, db=None):
        captured.append(
            {
                "attachments": attachments,
                "leave_id": leave_id,
                "status": status,
                "db": db,
            }
        )

    monkeypatch.setattr(leave_gateway, "_find_employee_profile", fake_find_employee_profile)
    monkeypatch.setattr(leave_gateway, "_fetch_leave_balances", fake_fetch_leave_balances)
    monkeypatch.setattr(leave_gateway, "_lock_documents_for_finalized_leave", fake_lock)

    result = await gateway.sanction_leave(
        "L-LOCK-1",
        LeaveActionDTO(
            remarks="Sanctioned",
            order_number="SB-LOCK-1",
            order_date="2026-04-12",
        ),
        current_user={
            "sub": "u-sanction",
            "authorities": ["SYSTEM_ADMIN"],
            "permissions": ["LEAVE_SANCTION"],
        },
    )

    assert result["status"] == "SANCTIONED"
    assert len(captured) == 1
    assert captured[0]["attachments"] == [{"filename": "support.pdf"}]
    assert captured[0]["leave_id"] == "L-LOCK-1"
    assert captured[0]["status"] == "SANCTIONED"
    assert captured[0]["db"].leave_applications is _FakeDb.leave_applications


@pytest.mark.asyncio
async def test_reject_leave_locks_supporting_attachments(monkeypatch) -> None:
    gateway = LeaveMongoGateway(_FakeDb())
    repository = _FakeRepository(
        leave_record={
            "id": "L-LOCK-2",
            "employee_id": "EMP-1",
            "leave_type_code": "EL",
            "from_date": "2026-04-21",
            "to_date": "2026-04-22",
            "days_applied": 2.0,
            "applied_by": "u-applicant",
            "status": "SUBMITTED",
            "attachments": [{"filename": "rejection-note.pdf"}],
        }
    )
    gateway._repository = repository
    captured: list[dict] = []

    async def fake_lock(attachments, *, leave_id, status, db=None):
        captured.append(
            {
                "attachments": attachments,
                "leave_id": leave_id,
                "status": status,
                "db": db,
            }
        )

    monkeypatch.setattr(leave_gateway, "_lock_documents_for_finalized_leave", fake_lock)

    result = await gateway.reject_leave(
        "L-LOCK-2",
        LeaveActionDTO(remarks="Rejected"),
        current_user={
            "sub": "u-reviewer",
            "authorities": ["SYSTEM_ADMIN"],
            "permissions": ["LEAVE_RECOMMEND"],
        },
    )

    assert result["status"] == "REJECTED"
    assert len(captured) == 1
    assert captured[0]["attachments"] == [{"filename": "rejection-note.pdf"}]
    assert captured[0]["leave_id"] == "L-LOCK-2"
    assert captured[0]["status"] == "REJECTED"
