from __future__ import annotations

import os
import sys

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.change_requests.application.service import ChangeRequestApplicationService
from contexts.change_requests.infrastructure import gateway as change_request_gateway
from contexts.change_requests.infrastructure.gateway import ChangeRequestMongoGateway
from contexts.leave.application.service import LeaveApplicationService
from contexts.leave.infrastructure import gateway as leave_gateway
from contexts.leave.infrastructure.gateway import LeaveMongoGateway


class _FakeProfileCursor:
    def __init__(self, docs):
        self._docs = docs

    def sort(self, *_args, **_kwargs):
        return self

    def skip(self, _n):
        return self

    def limit(self, _n):
        return self

    async def to_list(self, length=0):
        if length and length > 0:
            return self._docs[:length]
        return list(self._docs)


class _FakeEmployeeProfilesCollection:
    def __init__(self, dept_profiles=None):
        self.dept_profiles = dept_profiles or []

    def find(self, _query, _projection=None):
        return _FakeProfileCursor(self.dept_profiles)


class _FakeLeaveCursor:
    def __init__(self, docs):
        self._docs = list(docs)

    def sort(self, *_args, **_kwargs):
        return self

    def limit(self, n):
        self._docs = self._docs[:n]
        return self

    async def to_list(self, length=0):
        if length and length > 0:
            return self._docs[:length]
        return list(self._docs)


class _FakeLeaveApplicationsCollection:
    def __init__(self, docs=None):
        self._docs = docs or []
        self.last_query = None

    def find(self, query, _projection=None):
        self.last_query = dict(query)
        return _FakeLeaveCursor(self._docs)


class _FakeUsersCollection:
    async def find_one(self, _query, _projection=None):
        return None


class _FakeDBForLeave:
    def __init__(self, dept_profiles=None, leave_docs=None):
        self.employee_identities = _FakeEmployeeProfilesCollection(dept_profiles)
        self.users = _FakeUsersCollection()
        self.leave_applications = _FakeLeaveApplicationsCollection(leave_docs)


def _build_leave_service(db) -> LeaveApplicationService:
    return LeaveApplicationService(
        gateway=LeaveMongoGateway(db),
        outbox_repo=None,
        leave_rules_evaluator=None,
    )


def _build_change_request_service(db) -> ChangeRequestApplicationService:
    return ChangeRequestApplicationService(
        gateway=ChangeRequestMongoGateway(db),
        outbox_repo=None,
    )


@pytest.mark.asyncio
async def test_list_leaves_scopes_department_role_to_department_employee_ids(monkeypatch):
    db = _FakeDBForLeave(
        dept_profiles=[{"employee_id": "EMP-1"}, {"employee_id": "EMP-2"}],
        leave_docs=[],
    )
    current_user = {
        "authorities": ["HOD"],
        "permissions": ["LEAVE_RECOMMEND"],
        "department_code": "FIN",
    }

    result = await _build_leave_service(db).list_leaves(
        status=None,
        leave_type_code=None,
        employee_id=None,
        current_user=current_user,
    )

    assert result == []
    assert db.leave_applications.last_query["employee_id"] == {"$in": ["EMP-1", "EMP-2"]}


@pytest.mark.asyncio
async def test_list_leaves_rejects_department_role_when_target_employee_outside_department(monkeypatch):
    async def fake_get_employee_profile(_db, _employee_id):
        return {"employee_id": "EMP-9", "current_department_id": "HR"}

    monkeypatch.setattr(leave_gateway, "_find_employee_profile", fake_get_employee_profile)

    db = _FakeDBForLeave()
    current_user = {
        "authorities": ["HOD"],
        "permissions": ["LEAVE_RECOMMEND"],
        "department_code": "FIN",
    }

    with pytest.raises(HTTPException) as exc:
        await _build_leave_service(db).list_leaves(
            status=None,
            leave_type_code=None,
            employee_id="EMP-9",
            current_user=current_user,
        )

    assert exc.value.status_code == 403


class _FakeChangeRequestsCollection:
    def __init__(self, doc):
        self.doc = dict(doc)
        self.last_set = None

    async def find_one(self, query, _projection=None):
        if query.get("request_id") == self.doc.get("request_id"):
            return dict(self.doc)
        return None

    async def update_one(self, _query, update, **_kwargs):
        patch = update.get("$set", {})
        self.last_set = dict(patch)
        self.doc.update(patch)
        return None


class _FakeDBForChangeRequests:
    def __init__(self, doc):
        self.change_requests = _FakeChangeRequestsCollection(doc)

    def __getitem__(self, name):
        if name == "change_requests":
            return self.change_requests
        raise KeyError(name)


@pytest.mark.asyncio
async def test_review_change_request_approve_still_marks_applied_when_attachment_lock_fails(monkeypatch):
    doc = {
        "request_id": "CR-TEST-1",
        "employee_id": "EMP-1",
        "status": "PENDING",
        "department_id": "FIN",
        "request_type": "PROFILE",
        "category": "BASIC",
        "fields": [{"field_name": "mobile_primary", "requested_value": "9999999999"}],
        "attachments": [{"filename": "x.pdf"}],
    }
    db = _FakeDBForChangeRequests(doc)

    async def fake_apply_changes(_db, _doc, session=None):
        return None

    async def fake_notify(_db, _doc, _status):
        return None

    async def fake_get_user_display_name(_db, _user_id):
        return "Reviewer"

    def fake_lock(*_args, **_kwargs):
        raise RuntimeError("lock failed")

    monkeypatch.setattr(change_request_gateway, "_apply_changes", fake_apply_changes)
    monkeypatch.setattr(change_request_gateway, "_notify_employee", fake_notify)
    monkeypatch.setattr(change_request_gateway, "_get_user_display_name", fake_get_user_display_name)
    monkeypatch.setattr(change_request_gateway, "_lock_documents_for_approved_request", fake_lock)

    current_user = {
        "sub": "admin-1",
        "authorities": ["SYSTEM_ADMIN"],
        "permissions": ["PROFILE_UPDATE_ALL"],
    }

    result = await _build_change_request_service(db).review_change_request(
        "CR-TEST-1",
        action="APPROVE",
        remarks="ok",
        current_user=current_user,
    )

    assert result["status"] == "APPLIED"
    assert db.change_requests.last_set["status"] == "APPLIED"
