from __future__ import annotations

import os
import sys

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.change_requests.application.service import ChangeRequestApplicationService
from contexts.change_requests.infrastructure import gateway as change_request_gateway
from contexts.change_requests.infrastructure.gateway import ChangeRequestMongoGateway


class _FakeCursor:
    def __init__(self, docs):
        self._docs = list(docs)

    def sort(self, *_args, **_kwargs):
        return self

    def skip(self, n):
        self._docs = self._docs[n:]
        return self

    def limit(self, n):
        self._docs = self._docs[:n]
        return self

    async def to_list(self, length=0):
        if length and length > 0:
            return self._docs[:length]
        return list(self._docs)


class _FakeUsersCollection:
    def __init__(self, user_docs=None):
        self.user_docs = user_docs or {}

    async def find_one(self, query, _projection=None):
        user_id = query.get("id")
        if user_id in self.user_docs:
            return dict(self.user_docs[user_id])
        return None


class _FakeEmployeeProfilesCollection:
    def __init__(self, by_employee_id=None):
        self.by_employee_id = by_employee_id or {}

    async def find_one(self, query, _projection=None):
        employee_id = query.get("employee_id")
        if employee_id in self.by_employee_id:
            return dict(self.by_employee_id[employee_id])
        return None


class _FakeChangeRequestsCollection:
    def __init__(self, docs=None):
        self.docs = {d["request_id"]: dict(d) for d in (docs or [])}

    async def insert_one(self, doc):
        self.docs[doc["request_id"]] = dict(doc)
        return None

    async def count_documents(self, query):
        return len(self._filtered_docs(query))

    def find(self, query, _projection=None):
        return _FakeCursor(self._filtered_docs(query))

    async def find_one(self, query, _projection=None):
        req_id = query.get("request_id")
        if req_id:
            doc = self.docs.get(req_id)
            if not doc:
                return None
            for k, v in query.items():
                if doc.get(k) != v:
                    return None
            return dict(doc)
        for doc in self.docs.values():
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                return dict(doc)
        return None

    async def update_one(self, query, update, **_kwargs):
        req_id = query.get("request_id")
        if req_id in self.docs:
            self.docs[req_id].update(update.get("$set", {}))
        return None

    def _filtered_docs(self, query):
        items = []
        for doc in self.docs.values():
            ok = True
            for key, value in query.items():
                if doc.get(key) != value:
                    ok = False
                    break
            if ok:
                items.append(dict(doc))
        return items


class _FakeNotificationsCollection:
    def __init__(self):
        self.items = []

    async def insert_one(self, doc):
        self.items.append(dict(doc))
        return None


class _FakeDB:
    def __init__(self, *, users=None, profiles=None, requests=None):
        self.users = _FakeUsersCollection(users)
        self.employee_profile_read_models = _FakeEmployeeProfilesCollection(profiles)
        self.change_requests = _FakeChangeRequestsCollection(requests)
        self.notifications = _FakeNotificationsCollection()
        self.client = None

    def __getitem__(self, name):
        if name == "change_requests":
            return self.change_requests
        raise KeyError(name)


def _build_change_request_service(db) -> ChangeRequestApplicationService:
    return ChangeRequestApplicationService(
        gateway=ChangeRequestMongoGateway(db),
        outbox_repo=None,
    )


@pytest.mark.asyncio
async def test_change_request_department_roles_cannot_list_admin_queue():
    db = _FakeDB(
        users={},
        profiles={},
        requests=[{"request_id": "CR-1", "employee_id": "EMP-1", "department_id": "FIN", "status": "PENDING"}],
    )
    current_user = {
        "sub": "u-1",
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


@pytest.mark.asyncio
async def test_change_request_department_roles_cannot_review_requests(monkeypatch):
    db = _FakeDB(
        users={"hod-1": {"id": "hod-1", "name": "HOD User", "department_code": "FIN"}},
        profiles={},
        requests=[
            {
                "request_id": "CR-1A",
                "employee_id": "EMP-1",
                "department_id": "FIN",
                "status": "PENDING",
                "request_type": "PROFILE",
                "category": "BASIC",
                "fields": [{"field_name": "mobile_primary", "requested_value": "9123456789"}],
                "attachments": [],
            }
        ],
    )

    async def fake_get_user_display_name(_db, _user_id):
        return "HOD User"

    monkeypatch.setattr(change_request_gateway, "_get_user_display_name", fake_get_user_display_name)

    with pytest.raises(HTTPException) as exc:
        await _build_change_request_service(db).review_change_request(
            "CR-1A",
            action="APPROVE",
            remarks="Looks good",
            current_user={
                "sub": "hod-1",
                "authorities": ["HOD"],
                "permissions": ["PROFILE_UPDATE_ALL"],
                "department_code": "FIN",
            },
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "Department-scoped roles cannot access change request operations."


@pytest.mark.asyncio
async def test_change_request_reject_transition_sets_rejected_state(monkeypatch):
    db = _FakeDB(
        users={"sys-1": {"id": "sys-1", "name": "Sys Admin", "department_code": "FIN"}},
        profiles={},
        requests=[
            {
                "request_id": "CR-2",
                "employee_id": "EMP-2",
                "department_id": "FIN",
                "status": "PENDING",
                "request_type": "PROFILE",
                "category": "BASIC",
                "fields": [{"field_name": "mobile_primary", "requested_value": "9999999999"}],
                "attachments": [],
            }
        ],
    )

    async def fake_get_user_display_name(_db, _user_id):
        return "Sys Admin"

    monkeypatch.setattr(change_request_gateway, "_get_user_display_name", fake_get_user_display_name)

    result = await _build_change_request_service(db).review_change_request(
        "CR-2",
        action="REJECT",
        remarks="Not valid",
        current_user={
            "sub": "sys-1",
            "authorities": ["SYSTEM_ADMIN"],
            "permissions": ["PROFILE_UPDATE_ALL"],
        },
    )

    assert result["status"] == "REJECTED"
    assert result["review_remarks"] == "Not valid"


@pytest.mark.asyncio
async def test_change_request_approve_transition_sets_applied_state(monkeypatch):
    db = _FakeDB(
        users={"sys-2": {"id": "sys-2", "name": "Sys Admin", "department_code": "FIN"}},
        profiles={},
        requests=[
            {
                "request_id": "CR-3",
                "employee_id": "EMP-3",
                "department_id": "FIN",
                "status": "PENDING",
                "request_type": "PROFILE",
                "category": "BASIC",
                "fields": [{"field_name": "mobile_primary", "requested_value": "8888888888"}],
                "attachments": [],
            }
        ],
    )

    async def fake_apply_changes(_db, _doc, session=None):
        return None

    async def fake_get_user_display_name(_db, _user_id):
        return "Sys Admin"

    monkeypatch.setattr(change_request_gateway, "_apply_changes", fake_apply_changes)
    monkeypatch.setattr(change_request_gateway, "_get_user_display_name", fake_get_user_display_name)

    result = await _build_change_request_service(db).review_change_request(
        "CR-3",
        action="APPROVE",
        remarks="Approved",
        current_user={
            "sub": "sys-2",
            "authorities": ["SYSTEM_ADMIN"],
            "permissions": ["PROFILE_UPDATE_ALL"],
        },
    )

    assert result["status"] == "APPLIED"
    assert result.get("applied_at")


@pytest.mark.asyncio
async def test_change_request_approve_locks_attachments_after_apply(monkeypatch):
    db = _FakeDB(
        users={"sys-2": {"id": "sys-2", "name": "Sys Admin", "department_code": "FIN"}},
        profiles={},
        requests=[
            {
                "request_id": "CR-LOCK-1",
                "employee_id": "EMP-3",
                "department_id": "FIN",
                "status": "PENDING",
                "request_type": "PROFILE",
                "category": "BASIC",
                "fields": [{"field_name": "mobile_primary", "requested_value": "8888888888"}],
                "attachments": [{"filename": "supporting-order.pdf"}],
            }
        ],
    )
    captured: list[dict] = []

    async def fake_apply_changes(_db, _doc, session=None):
        return None

    async def fake_get_user_display_name(_db, _user_id):
        return "Sys Admin"

    async def fake_lock(attachments, *, request_id, status, db=None):
        captured.append(
            {
                "attachments": attachments,
                "request_id": request_id,
                "status": status,
                "db": db,
            }
        )

    monkeypatch.setattr(change_request_gateway, "_apply_changes", fake_apply_changes)
    monkeypatch.setattr(change_request_gateway, "_get_user_display_name", fake_get_user_display_name)
    monkeypatch.setattr(change_request_gateway, "_lock_documents_for_approved_request", fake_lock)

    result = await _build_change_request_service(db).review_change_request(
        "CR-LOCK-1",
        action="APPROVE",
        remarks="Approved",
        current_user={
            "sub": "sys-2",
            "authorities": ["SYSTEM_ADMIN"],
            "permissions": ["PROFILE_UPDATE_ALL"],
        },
    )

    assert result["status"] == "APPLIED"
    assert len(captured) == 1
    assert captured[0]["attachments"] == [{"filename": "supporting-order.pdf"}]
    assert captured[0]["request_id"] == "CR-LOCK-1"
    assert captured[0]["status"] == "APPLIED"
    assert captured[0]["db"] is db


@pytest.mark.asyncio
async def test_change_request_approve_skips_attachment_lock_when_no_attachments(monkeypatch):
    db = _FakeDB(
        users={"sys-2": {"id": "sys-2", "name": "Sys Admin", "department_code": "FIN"}},
        profiles={},
        requests=[
            {
                "request_id": "CR-LOCK-2",
                "employee_id": "EMP-3",
                "department_id": "FIN",
                "status": "PENDING",
                "request_type": "PROFILE",
                "category": "BASIC",
                "fields": [{"field_name": "mobile_primary", "requested_value": "8888888888"}],
                "attachments": [],
            }
        ],
    )
    captured: list[dict] = []

    async def fake_apply_changes(_db, _doc, session=None):
        return None

    async def fake_get_user_display_name(_db, _user_id):
        return "Sys Admin"

    async def fake_lock(*args, **kwargs):
        captured.append({"args": args, "kwargs": kwargs})

    monkeypatch.setattr(change_request_gateway, "_apply_changes", fake_apply_changes)
    monkeypatch.setattr(change_request_gateway, "_get_user_display_name", fake_get_user_display_name)
    monkeypatch.setattr(change_request_gateway, "_lock_documents_for_approved_request", fake_lock)

    result = await _build_change_request_service(db).review_change_request(
        "CR-LOCK-2",
        action="APPROVE",
        remarks="Approved",
        current_user={
            "sub": "sys-2",
            "authorities": ["SYSTEM_ADMIN"],
            "permissions": ["PROFILE_UPDATE_ALL"],
        },
    )

    assert result["status"] == "APPLIED"
    assert captured == []


@pytest.mark.asyncio
async def test_change_request_review_non_pending_rejected():
    db = _FakeDB(
        requests=[
            {
                "request_id": "CR-4",
                "employee_id": "EMP-4",
                "department_id": "FIN",
                "status": "APPLIED",
                "request_type": "PROFILE",
                "category": "BASIC",
                "fields": [{"field_name": "mobile_primary", "requested_value": "7777777777"}],
                "attachments": [],
            }
        ],
    )

    with pytest.raises(HTTPException) as exc:
        await _build_change_request_service(db).review_change_request(
            "CR-4",
            action="REJECT",
            remarks="late",
            current_user={
                "sub": "sys-3",
                "authorities": ["SYSTEM_ADMIN"],
                "permissions": ["PROFILE_UPDATE_ALL"],
            },
        )

    assert exc.value.status_code == 400
