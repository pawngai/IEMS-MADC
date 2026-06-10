from __future__ import annotations

import os
import sys

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.ess.infrastructure import service as ess_service


@pytest.mark.asyncio
async def test_ess_service_book_denied_for_non_regular_employee(monkeypatch):
    async def fake_find_profile(_db, _employee_id):
        return {
            "employee_id": "EMP-OUT-1",
            "full_name": "Outsourced Employee",
            "employment_type": "OUTSOURCED",
        }

    monkeypatch.setattr(ess_service.repo, "find_profile", fake_find_profile)
    async def fake_list_projected_service_book_entries(_db, _employee_id, **_kwargs):
        return []

    monkeypatch.setattr(
        ess_service.repo,
        "list_projected_service_book_entries",
        fake_list_projected_service_book_entries,
    )

    with pytest.raises(HTTPException) as exc:
        await ess_service.get_my_service_book(
            db=object(),
            current_user={
                "sub": "u-1",
                "employee_id": "EMP-OUT-1",
                "permissions": ["SERVICE_BOOK_READ_OWN"],
            },
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_ess_service_book_allowed_for_regular_employee(monkeypatch):
    async def fake_find_profile(_db, _employee_id):
        return {
            "employee_id": "EMP-REG-1",
            "full_name": "Regular Employee",
            "employment_type": "REGULAR",
        }

    async def fake_list_projected_service_book_entries(_db, employee_id, **_kwargs):
        return [
            {
                "entry_id": "SB-E-1",
                "employee_id": employee_id,
                "part_code": "SB_PART_I",
                "schema_key": "SB_I_BIODATA",
                "payload": {
                    "status": "APPROVED",
                    "name": "Regular Employee",
                },
            }
        ]

    monkeypatch.setattr(ess_service.repo, "find_profile", fake_find_profile)
    monkeypatch.setattr(
        ess_service.repo,
        "list_projected_service_book_entries",
        fake_list_projected_service_book_entries,
    )

    async def fake_get_projected_service_book_part(_db, _employee_id, _part):
        return None

    monkeypatch.setattr(
        ess_service.repo,
        "get_projected_service_book_part",
        fake_get_projected_service_book_part,
    )

    result = await ess_service.get_my_service_book(
        db=object(),
        current_user={
            "sub": "u-2",
            "employee_id": "EMP-REG-1",
            "permissions": ["SERVICE_BOOK_READ_OWN"],
        },
    )

    assert result["employee_id"] == "EMP-REG-1"
    assert "I" in result["parts"]
