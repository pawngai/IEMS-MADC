from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.ess.infrastructure import service as ess_service


@pytest.mark.asyncio
async def test_ess_read_side_first_skips_legacy_ledger(monkeypatch):
    async def fake_find_profile(_db, _employee_id):
        return {
            "employee_id": "EMP-1",
            "full_name": "Read Side User",
            "employment_type": "REGULAR",
        }

    async def fake_read_side_entries(_db, _employee_id, **_kwargs):
        return [
            {
                "entry_id": "P-1",
                "employee_id": "EMP-1",
                "part_code": "SB_PART_I",
                "payload": {"status": "APPROVED", "name": "Read Side User"},
            }
        ]

    async def fail_legacy_entries(*_args, **_kwargs):
        raise AssertionError("Legacy ledger should not be called when projection has data")

    async def fake_read_side_part(*_args, **_kwargs):
        return None

    monkeypatch.setattr(ess_service.repo, "find_profile", fake_find_profile)
    monkeypatch.setattr(
        ess_service.repo,
        "list_projected_service_book_entries",
        fake_read_side_entries,
    )
    monkeypatch.setattr(
        ess_service.repo,
        "get_projected_service_book_part",
        fake_read_side_part,
    )
    monkeypatch.setattr(ess_service.repo, "list_servicebook_entries", fail_legacy_entries)

    result = await ess_service.get_my_service_book(
        db=object(),
        current_user={
            "sub": "u-1",
            "employee_id": "EMP-1",
            "permissions": ["SERVICE_BOOK_READ_OWN"],
        },
    )

    assert result["employee_id"] == "EMP-1"
    assert "I" in result["parts"]


@pytest.mark.asyncio
async def test_ess_read_side_empty_does_not_fallback_to_legacy(monkeypatch):
    async def fake_find_profile(_db, _employee_id):
        return {
            "employee_id": "EMP-2",
            "full_name": "Legacy Fallback",
            "employment_type": "REGULAR",
        }

    async def fake_read_side_entries(_db, _employee_id, **_kwargs):
        return []

    async def fail_legacy_entries(*_args, **_kwargs):
        raise AssertionError("Legacy ledger fallback must not be used after migration")

    async def fake_read_side_part(_db, _employee_id, _part):
        return None

    async def fail_legacy_part(*_args, **_kwargs):
        raise AssertionError("Legacy part fallback must not be used after migration")

    monkeypatch.setattr(ess_service.repo, "find_profile", fake_find_profile)
    monkeypatch.setattr(
        ess_service.repo,
        "list_projected_service_book_entries",
        fake_read_side_entries,
    )
    monkeypatch.setattr(ess_service.repo, "list_servicebook_entries", fail_legacy_entries)
    monkeypatch.setattr(
        ess_service.repo,
        "get_projected_service_book_part",
        fake_read_side_part,
    )
    monkeypatch.setattr(ess_service.repo, "get_service_book_part", fail_legacy_part)

    result = await ess_service.get_my_service_book(
        db=object(),
        current_user={
            "sub": "u-2",
            "employee_id": "EMP-2",
            "permissions": ["SERVICE_BOOK_READ_OWN"],
        },
    )

    assert result["employee_id"] == "EMP-2"
    assert result["parts"] == {}
