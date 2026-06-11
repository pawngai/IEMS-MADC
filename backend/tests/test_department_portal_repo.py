from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.organization_master.repository import department_portal_repo


class _NoDirectDepartmentCollectionAccess:
    def __getattr__(self, _name: str):
        raise AssertionError("department repo should use reference data service for department master reads")


@pytest.mark.asyncio
async def test_get_department_info_reads_via_reference_data_service(monkeypatch) -> None:
    async def _fake_get_departments(db):
        assert isinstance(db, _NoDirectDepartmentCollectionAccess)
        return [
            {"code": "HR", "name": "Human Resources", "status": "ACTIVE"},
            {"code": "FIN", "name": "Finance", "status": "ACTIVE"},
        ]

    monkeypatch.setattr(
        department_portal_repo.reference_data_service,
        "get_departments",
        _fake_get_departments,
    )

    result = await department_portal_repo.get_department_info(
        _NoDirectDepartmentCollectionAccess(),
        "fin",
    )

    assert result == {
        "code": "FIN",
        "name": "Finance",
        "status": "ACTIVE",
    }


@pytest.mark.asyncio
async def test_get_department_info_returns_none_when_department_missing(monkeypatch) -> None:
    async def _fake_get_departments(_db):
        return [{"code": "HR", "name": "Human Resources", "status": "ACTIVE"}]

    monkeypatch.setattr(
        department_portal_repo.reference_data_service,
        "get_departments",
        _fake_get_departments,
    )

    result = await department_portal_repo.get_department_info(
        _NoDirectDepartmentCollectionAccess(),
        "fin",
    )

    assert result is None