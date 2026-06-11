from __future__ import annotations

import os
import sys

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.leave_attendance.application.service import LeaveApplicationService
from contexts.leave_attendance.infrastructure import gateway as leave_gateway
from contexts.leave_attendance.infrastructure.gateway import LeaveMongoGateway


class _FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, *_args, **_kwargs):
        return self

    def skip(self, _n):
        return self

    def limit(self, _n):
        return self

    async def to_list(self, length=0):
        if length and length > 0:
            return self.docs[:length]
        return self.docs


class _FakeEmployeeProfilesCollection:
    def __init__(self, by_employee_id=None, by_department=None):
        self.by_employee_id = by_employee_id or {}
        self.by_department = by_department or {}

    async def find_one(self, query, _projection=None):
        employee_id = query.get("employee_id")
        if employee_id and employee_id in self.by_employee_id:
            return dict(self.by_employee_id[employee_id])
        return None

    def find(self, query, _projection=None):
        dept = query.get("current_department_id")
        docs = [{"employee_id": eid} for eid in self.by_department.get(dept, [])]
        return _FakeCursor(docs)


class _FakeUsersCollection:
    def __init__(self, by_id=None):
        self.by_id = by_id or {}

    async def find_one(self, query, _projection=None):
        user_id = query.get("id")
        if user_id in self.by_id:
            return dict(self.by_id[user_id])
        return None


class _FakeLeaveCursor:
    def __init__(self, docs):
        self.docs = list(docs)

    def sort(self, *_args, **_kwargs):
        return self

    def limit(self, n):
        self.docs = self.docs[:n]
        return self

    async def to_list(self, length=0):
        if length and length > 0:
            return self.docs[:length]
        return list(self.docs)


class _FakeLeaveApplicationsCollection:
    def __init__(self, docs=None):
        self.docs = docs or []
        self.last_query = None

    def find(self, query, _projection=None):
        self.last_query = dict(query)
        return _FakeLeaveCursor(self.docs)


class _FakeDB:
    def __init__(self, *, profiles=None, dept_map=None, users=None, leave_docs=None):
        self.employee_identities = _FakeEmployeeProfilesCollection(profiles, dept_map)
        self.users = _FakeUsersCollection(users)
        self.leave_applications = _FakeLeaveApplicationsCollection(leave_docs)


def _build_leave_service(db) -> LeaveApplicationService:
    return LeaveApplicationService(
        gateway=LeaveMongoGateway(db),
        outbox_repo=None,
        leave_rules_evaluator=None,
    )


@pytest.mark.asyncio
async def test_leave_list_department_role_fail_closed_without_department():
    db = _FakeDB()
    current_user = {
        "sub": "u-1",
        "authorities": ["HOD"],
        "permissions": ["LEAVE_RECOMMEND"],
    }

    with pytest.raises(HTTPException) as exc:
        await _build_leave_service(db).list_leaves(
            status=None,
            leave_type_code=None,
            employee_id=None,
            current_user=current_user,
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_leave_list_department_role_scoped_to_department(monkeypatch):
    db = _FakeDB(
        dept_map={"FIN": ["EMP-1", "EMP-2"]},
        leave_docs=[{"id": "L-1", "employee_id": "EMP-1"}],
    )
    current_user = {
        "sub": "u-2",
        "authorities": ["HOD"],
        "permissions": ["LEAVE_RECOMMEND"],
        "department_code": "FIN",
    }

    result = await _build_leave_service(db).list_leaves(
        status="SUBMITTED",
        leave_type_code=None,
        employee_id=None,
        current_user=current_user,
    )

    assert len(result) == 1
    assert db.leave_applications.last_query["employee_id"] == {"$in": ["EMP-1", "EMP-2"]}
    assert db.leave_applications.last_query["status"] == "SUBMITTED"


@pytest.mark.asyncio
async def test_leave_list_department_role_denies_other_department_employee(monkeypatch):
    async def fake_get_employee_profile(_db, employee_id):
        return {"employee_id": employee_id, "current_department_id": "HR"}

    monkeypatch.setattr(leave_gateway, "_find_employee_profile", fake_get_employee_profile)

    db = _FakeDB()
    current_user = {
        "sub": "u-3",
        "authorities": ["HOD"],
        "permissions": ["LEAVE_RECOMMEND"],
        "department_code": "FIN",
    }

    with pytest.raises(HTTPException) as exc:
        await _build_leave_service(db).list_leaves(
            status=None,
            leave_type_code=None,
            employee_id="EMP-HR-1",
            current_user=current_user,
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_leave_list_global_role_not_department_scoped(monkeypatch):
    db = _FakeDB(leave_docs=[{"id": "L-9", "employee_id": "EMP-HR-1"}])
    current_user = {
        "sub": "u-4",
        "authorities": ["SYSTEM_ADMIN"],
        "permissions": ["LEAVE_READ_ALL"],
    }

    result = await _build_leave_service(db).list_leaves(
        status=None,
        leave_type_code="EL",
        employee_id="EMP-HR-1",
        current_user=current_user,
    )

    assert len(result) == 1
    assert db.leave_applications.last_query["employee_id"] == "EMP-HR-1"
    assert db.leave_applications.last_query["leave_type_code"] == "EL"
