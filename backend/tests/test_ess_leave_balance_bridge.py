from __future__ import annotations

import os
import sys

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.ess.infrastructure import service as ess_service
from contexts.ess.infrastructure import repo as ess_repo


@pytest.mark.asyncio
async def test_ess_leave_balances_reads_from_ess_repo(monkeypatch):
    captured: dict = {}

    async def fake_ensure_initial_leave_account(db, *, employee_id: str, user_id: str | None):
        captured["seed_db"] = db
        captured["seed_employee_id"] = employee_id
        captured["seed_user_id"] = user_id
        return None

    async def fake_get_leave_balances(db, employee_id: str) -> dict:
        captured["db"] = db
        captured["employee_id"] = employee_id
        return {
            "employee_id": employee_id,
            "balances": {"EL": {"available_days": 10}},
        }

    monkeypatch.setattr(
        ess_service,
        "ensure_initial_leave_account",
        fake_ensure_initial_leave_account,
    )
    monkeypatch.setattr(ess_service.repo, "get_leave_balances", fake_get_leave_balances)

    db = object()
    current_user = {
        "sub": "u-1",
        "employee_id": "EMP-100",
        "permissions": ["LEAVE_READ_OWN"],
    }

    result = await ess_service.get_my_leave_balances(db, current_user=current_user)

    assert result["employee_id"] == "EMP-100"
    assert captured["seed_db"] is db
    assert captured["seed_employee_id"] == "EMP-100"
    assert captured["seed_user_id"] == "u-1"
    assert captured["db"] is db
    assert captured["employee_id"] == "EMP-100"


@pytest.mark.asyncio
async def test_ess_leave_balances_requires_employee_link() -> None:
    with pytest.raises(HTTPException) as exc:
        await ess_service.get_my_leave_balances(
            object(),
            current_user={"sub": "u-2", "permissions": ["LEAVE_READ_OWN"]},
        )

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_ess_documents_reads_from_ess_repo(monkeypatch):
    captured: dict = {}

    async def fake_list_subject_documents(
        db,
        *,
        employee_id: str,
        employee_code: str | None = None,
        query: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        document_type: str | None = None,
        category: str | None = None,
        source_context: str | None = None,
        is_locked: bool | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        captured.update(
            {
                "db": db,
                "employee_id": employee_id,
                "employee_code": employee_code,
                "query": query,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "document_type": document_type,
                "category": category,
                "source_context": source_context,
                "is_locked": is_locked,
                "date_from": date_from,
                "date_to": date_to,
                "limit": limit,
                "offset": offset,
            }
        )
        return {"success": True, "items": [{"filename": "subject-file.pdf"}], "total": 1, "limit": limit, "offset": offset}

    monkeypatch.setattr(ess_service.repo, "list_subject_documents", fake_list_subject_documents)

    db = object()
    current_user = {
        "sub": "u-1",
        "employee_id": "EMP-100",
        "employee_code": "MADC-2024-0100",
        "permissions": ["DOCUMENT_READ_OWN"],
    }

    result = await ess_service.get_my_documents(
        db,
        current_user=current_user,
        query="certificate",
        entity_type="SERVICE_EVENT",
        entity_id="SE-1",
        document_type="ORDER",
        category="APPOINTMENT_ORDER",
        source_context="service_events.upload",
        is_locked=False,
        date_from="2026-04-01T00:00:00+00:00",
        date_to="2026-04-30T23:59:59+00:00",
        limit=25,
        offset=5,
    )

    assert result["items"][0]["filename"] == "subject-file.pdf"
    assert captured == {
        "db": db,
        "employee_id": "EMP-100",
        "employee_code": "MADC-2024-0100",
        "query": "certificate",
        "entity_type": "SERVICE_EVENT",
        "entity_id": "SE-1",
        "document_type": "ORDER",
        "category": "APPOINTMENT_ORDER",
        "source_context": "service_events.upload",
        "is_locked": False,
        "date_from": "2026-04-01T00:00:00+00:00",
        "date_to": "2026-04-30T23:59:59+00:00",
        "limit": 25,
        "offset": 5,
    }


@pytest.mark.asyncio
async def test_ess_document_download_reads_from_ess_repo(monkeypatch):
    captured: dict = {}

    async def fake_download_subject_document(db, *, filename: str, employee_id: str, employee_code: str | None = None):
        captured.update(
            {
                "db": db,
                "filename": filename,
                "employee_id": employee_id,
                "employee_code": employee_code,
            }
        )
        return {"filename": filename, "download": True}

    monkeypatch.setattr(ess_service.repo, "download_subject_document", fake_download_subject_document)

    db = object()
    current_user = {
        "sub": "u-1",
        "employee_id": "EMP-100",
        "employee_code": "MADC-2024-0100",
        "permissions": ["DOCUMENT_READ_OWN"],
    }

    result = await ess_service.download_my_document("subject-file.pdf", db, current_user=current_user)

    assert result["download"] is True
    assert captured == {
        "db": db,
        "filename": "subject-file.pdf",
        "employee_id": "EMP-100",
        "employee_code": "MADC-2024-0100",
    }


@pytest.mark.asyncio
async def test_ess_documents_require_document_read_own() -> None:
    with pytest.raises(HTTPException) as exc:
        await ess_service.get_my_documents(
            object(),
            current_user={
                "sub": "u-1",
                "employee_id": "EMP-100",
                "permissions": ["LEAVE_READ_OWN"],
            },
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_ess_document_open_reads_from_ess_repo(monkeypatch):
    captured: dict = {}

    async def fake_get_subject_document(db, *, filename: str, employee_id: str, employee_code: str | None = None):
        captured.update(
            {
                "db": db,
                "filename": filename,
                "employee_id": employee_id,
                "employee_code": employee_code,
            }
        )
        return {"filename": filename, "inline": True}

    monkeypatch.setattr(ess_service.repo, "get_subject_document", fake_get_subject_document)

    db = object()
    current_user = {
        "sub": "u-1",
        "employee_id": "EMP-100",
        "employee_code": "MADC-2024-0100",
    }

    result = await ess_service.get_my_document("subject-file.pdf", db, current_user=current_user)

    assert result["inline"] is True
    assert captured == {
        "db": db,
        "filename": "subject-file.pdf",
        "employee_id": "EMP-100",
        "employee_code": "MADC-2024-0100",
    }


@pytest.mark.asyncio
async def test_ess_repo_lifetime_cap_balance_uses_all_time_bounds(monkeypatch) -> None:
    async def fake_find_profile(_db, _employee_id):
        return {
            "employee_id": "EMP-100",
            "employment_type": "REGULAR",
        }

    async def fake_list_leave_types(_db):
        return [
            {
                "code": "CCL",
                "leave_code": "CCL",
                "description": "Child Care Leave",
                "is_active": True,
                "applicable_employment_types": ["REG"],
                "balance_strategy": "lifetime_cap",
                "max_days_lifetime": 730,
            }
        ]

    async def fake_get_leave_ledger_entry(_db, *, employee_id):
        assert employee_id == "EMP-100"
        return None

    captured: dict = {}

    async def fake_list_sanctioned_leave_applications(
        _db,
        *,
        employee_id: str,
        leave_type_code: str,
        from_date_lte: str,
        to_date_gte: str,
        limit: int = 5000,
    ):
        captured.update(
            {
                "employee_id": employee_id,
                "leave_type_code": leave_type_code,
                "from_date_lte": from_date_lte,
                "to_date_gte": to_date_gte,
                "limit": limit,
            }
        )
        return [{"days_applied": 12}]

    monkeypatch.setattr(ess_repo, "find_profile", fake_find_profile)
    monkeypatch.setattr(ess_repo, "list_leave_types", fake_list_leave_types)
    monkeypatch.setattr(ess_repo, "get_leave_ledger_entry", fake_get_leave_ledger_entry)
    monkeypatch.setattr(
        ess_repo,
        "list_sanctioned_leave_applications",
        fake_list_sanctioned_leave_applications,
    )

    result = await ess_repo.get_leave_balances(object(), "EMP-100")

    assert captured == {
        "employee_id": "EMP-100",
        "leave_type_code": "CCL",
        "from_date_lte": "9999-12-31",
        "to_date_gte": "0001-01-01",
        "limit": 5000,
    }
    assert result["balances"]["CCL"]["used_days_total"] == 12.0
    assert result["balances"]["CCL"]["available_days"] == 718.0


@pytest.mark.asyncio
async def test_ess_repo_leave_balances_fall_back_to_service_book_appointment(monkeypatch) -> None:
    async def fake_find_profile(_db, _employee_id):
        return {
            "employee_id": "EMP-100",
            "employment_type": "REGULAR",
            "date_of_initial_engagement": None,
        }

    async def fake_list_leave_types(_db):
        return [
            {
                "code": "EL",
                "leave_code": "EL",
                "description": "Earned Leave",
                "is_active": True,
                "is_accumulative": True,
                "max_days_per_year": 30,
                "balance_strategy": "ledger",
                "applicable_employment_types": ["REG"],
            },
            {
                "code": "HPL",
                "leave_code": "HPL",
                "description": "Half Pay Leave",
                "is_active": True,
                "is_accumulative": True,
                "max_days_per_year": 20,
                "balance_strategy": "ledger",
                "applicable_employment_types": ["REG"],
            },
            {
                "code": "CL",
                "leave_code": "CL",
                "description": "Casual Leave",
                "is_active": True,
                "max_days_per_year": 8,
                "balance_strategy": "ledger",
                "applicable_employment_types": ["REG"],
            },
        ]

    async def fake_get_leave_ledger_entry(_db, *, employee_id):
        assert employee_id == "EMP-100"
        return None

    async def fake_get_employee_initial_appointment_date(_db, *, employee_id: str):
        assert employee_id == "EMP-100"
        return "2025-01-15"

    async def fake_list_sanctioned_leave_applications(
        _db,
        *,
        employee_id: str,
        leave_type_code: str,
        from_date_lte: str,
        to_date_gte: str,
        limit: int = 5000,
    ):
        assert employee_id == "EMP-100"
        return []

    monkeypatch.setattr(ess_repo, "find_profile", fake_find_profile)
    monkeypatch.setattr(ess_repo, "list_leave_types", fake_list_leave_types)
    monkeypatch.setattr(ess_repo, "get_leave_ledger_entry", fake_get_leave_ledger_entry)
    monkeypatch.setattr(
        ess_repo,
        "_get_employee_initial_appointment_date",
        fake_get_employee_initial_appointment_date,
    )
    monkeypatch.setattr(
        ess_repo,
        "list_sanctioned_leave_applications",
        fake_list_sanctioned_leave_applications,
    )

    result = await ess_repo.get_leave_balances(object(), "EMP-100")

    assert result["balances"]["EL"]["available_days"] > 0
    assert result["balances"]["HPL"]["available_days"] > 0
    assert result["balances"]["CL"]["available_days"] == 8.0
