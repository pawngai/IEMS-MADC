from __future__ import annotations

import os
import sys

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.change_requests.application.service import ChangeRequestApplicationService
from contexts.change_requests.infrastructure.gateway import (
    ChangeRequestMongoGateway,
    _resolve_user_department,
)
from contexts.employee_profile.application.dependencies import get_db as get_employee_db
from contexts.seniority.api.router import _get_db as get_seniority_db
from contexts.system_admin.api.shared import get_db as get_system_admin_db
from app_platform.db.runtime import mongo_state


class _FakeUsersCollection:
    def __init__(self, dept_by_user_id: dict[str, str] | None = None):
        self.dept_by_user_id = dept_by_user_id or {}
        self.last_query = None

    async def find_one(self, query, _projection=None):
        self.last_query = query
        user_id = query.get("id")
        if user_id in self.dept_by_user_id:
            return {"department_code": self.dept_by_user_id[user_id]}
        return None


class _FakeEmployeeProfilesCollection:
    async def find_one(self, _query, _projection=None):
        return None


class _FakeChangeRequestsCollection:
    async def count_documents(self, _query):
        return 0


class _FakeDB:
    def __init__(self, dept_by_user_id: dict[str, str] | None = None):
        self.users = _FakeUsersCollection(dept_by_user_id)
        self.employee_profile_read_models = _FakeEmployeeProfilesCollection()
        self.change_requests = _FakeChangeRequestsCollection()

    def __getitem__(self, item):
        if item == "change_requests":
            return self.change_requests
        raise KeyError(item)


def _build_change_request_service(db) -> ChangeRequestApplicationService:
    return ChangeRequestApplicationService(
        gateway=ChangeRequestMongoGateway(db),
        outbox_repo=None,
    )


@pytest.mark.asyncio
async def test_change_request_department_resolution_uses_canonical_user_id_field():
    db = _FakeDB(dept_by_user_id={"user-1": "FIN"})
    current_user = {"sub": "user-1"}

    dept = await _resolve_user_department(db, current_user)

    assert dept == "FIN"
    assert db.users.last_query == {"id": "user-1"}


@pytest.mark.asyncio
async def test_change_request_department_scoped_roles_fail_closed():
    db = _FakeDB(dept_by_user_id={})
    current_user = {
        "sub": "user-2",
        "authorities": ["DEPT_DATA_ENTRY"],
        "permissions": ["PROFILE_READ_ALL"],
    }

    with pytest.raises(HTTPException) as exc:
        await _build_change_request_service(db).list_change_requests(
            current_user=current_user,
            status=None,
            employee_id=None,
            page=1,
            page_size=20,
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "Department-scoped roles cannot access change request operations."


def test_profile_router_get_db_returns_503_when_database_offline():
    original_db = mongo_state.db
    try:
        mongo_state.db = None
        with pytest.raises(HTTPException) as exc:
            get_employee_db()
        assert exc.value.status_code == 503
        assert exc.value.detail == "Database not available"
    finally:
        mongo_state.db = original_db


def test_seniority_router_get_db_returns_503_when_database_offline():
    original_db = mongo_state.db
    try:
        mongo_state.db = None
        with pytest.raises(HTTPException) as exc:
            get_seniority_db()
        assert exc.value.status_code == 503
        assert exc.value.detail == "Database not available"
    finally:
        mongo_state.db = original_db


def test_system_admin_get_db_returns_503_when_database_offline():
    original_db = mongo_state.db
    try:
        mongo_state.db = None
        with pytest.raises(HTTPException) as exc:
            get_system_admin_db()
        assert exc.value.status_code == 503
        assert exc.value.detail == "Database not available"
    finally:
        mongo_state.db = original_db
