from __future__ import annotations

import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.employee_master.profile.application.read_profiles import list_profiles_response


class _FakeWorkflowService:
    def __init__(self) -> None:
        self.last_query: dict | None = None

    async def count_profile_records(self, *, query: dict) -> int:
        self.last_query = dict(query)
        return 0

    async def list_profile_records(
        self, *, query: dict, skip: int, limit: int, sort: list | None = None
    ) -> list[dict]:
        self.last_query = dict(query)
        return []


async def _no_scope(*_args, **_kwargs):
    return None


@pytest.mark.asyncio
async def test_verifier_default_query_excludes_attested() -> None:
    service = _FakeWorkflowService()

    await list_profiles_response(
        db=SimpleNamespace(),
        search=None,
        status=None,
        workflow_status=None,
        department_id=None,
        employment_type=None,
        force_all=False,
        page=1,
        page_size=20,
        current_user={"sub": "u1", "permissions": ["PROFILE_READ_ALL"]},
        user_role="VERIFIER",
        workflow_service=service,
        enforce_department_scope_or_raise_fn=_no_scope,
        data_entry_roles={"DATA_ENTRY", "DEPT_DATA_ENTRY", "GLOBAL_DATA_ENTRY"},
        role_verifier="VERIFIER",
        role_approver="APPROVING_AUTHORITY",
    )

    assert service.last_query == {
        "workflow_status": {"$in": ["SUBMITTED", "VERIFIED", "APPROVED", "LOCKED"]}
    }


@pytest.mark.asyncio
async def test_approver_default_query_excludes_attested() -> None:
    service = _FakeWorkflowService()

    await list_profiles_response(
        db=SimpleNamespace(),
        search=None,
        status=None,
        workflow_status=None,
        department_id=None,
        employment_type=None,
        force_all=False,
        page=1,
        page_size=20,
        current_user={"sub": "u2", "permissions": ["PROFILE_READ_ALL"]},
        user_role="APPROVING_AUTHORITY",
        workflow_service=service,
        enforce_department_scope_or_raise_fn=_no_scope,
        data_entry_roles={"DATA_ENTRY", "DEPT_DATA_ENTRY", "GLOBAL_DATA_ENTRY"},
        role_verifier="VERIFIER",
        role_approver="APPROVING_AUTHORITY",
    )

    assert service.last_query == {
        "workflow_status": {"$in": ["VERIFIED", "APPROVED", "LOCKED"]}
    }


@pytest.mark.asyncio
async def test_list_profiles_enriches_login_account_state(monkeypatch) -> None:
    class _WorkflowServiceWithRows(_FakeWorkflowService):
        async def count_profile_records(self, *, query: dict) -> int:
            self.last_query = dict(query)
            return 2

        async def list_profile_records(
            self, *, query: dict, skip: int, limit: int, sort: list | None = None
        ) -> list[dict]:
            self.last_query = dict(query)
            return [
                {
                    "employee_id": "EMP-1",
                    "employee_code": "E-001",
                    "full_name": "Alice",
                    "workflow_status": "APPROVED",
                },
                {
                    "employee_id": "EMP-2",
                    "employee_code": "E-002",
                    "full_name": "Bob",
                    "workflow_status": "LOCKED",
                },
            ]

    async def _fake_find_user_by_employee_id(_db, *, employee_id, projection=None):
        assert projection == {"_id": 0, "email": 1}
        if employee_id == "EMP-1":
            return {"email": "alice@madc.gov.in"}
        return None

    result = await list_profiles_response(
        db=SimpleNamespace(),
        search=None,
        status=None,
        workflow_status=None,
        department_id=None,
        employment_type=None,
        force_all=False,
        page=1,
        page_size=20,
        current_user={"sub": "u3", "permissions": ["PROFILE_READ_ALL"]},
        user_role="GLOBAL_DATA_ENTRY",
        workflow_service=_WorkflowServiceWithRows(),
        enforce_department_scope_or_raise_fn=_no_scope,
        data_entry_roles={"DATA_ENTRY", "DEPT_DATA_ENTRY", "GLOBAL_DATA_ENTRY"},
        role_verifier="VERIFIER",
        role_approver="APPROVING_AUTHORITY",
        find_employee_account_by_employee_id_fn=_fake_find_user_by_employee_id,
    )

    assert result["profiles"][0]["has_login_account"] is True
    assert result["profiles"][0]["account_email"] == "alice@madc.gov.in"
    assert result["profiles"][1]["has_login_account"] is False
    assert "account_email" not in result["profiles"][1]
