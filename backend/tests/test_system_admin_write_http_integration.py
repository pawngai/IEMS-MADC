from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app_platform import auth as shared_auth_module
from contexts.system_admin.api import router as system_admin_router
from contexts.system_admin.api.shared import get_db


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    try:
        yield
    finally:
        app.dependency_overrides.pop(shared_auth_module.get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


class _FakeUpdateResult:
    def __init__(self, modified_count: int = 1):
        self.modified_count = modified_count


class _FakeCollection:
    def __init__(self, docs: list[dict] | None = None):
        self.docs = [dict(doc) for doc in (docs or [])]

    async def find_one(self, query: dict, projection: dict | None = None):
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in query.items()):
                result = dict(doc)
                if projection and projection.get("_id") == 0:
                    result.pop("_id", None)
                return result
        return None

    async def count_documents(self, query: dict) -> int:
        def _matches(doc: dict, needle: dict) -> bool:
            for key, value in needle.items():
                if isinstance(value, dict) and "$in" in value:
                    if doc.get(key) not in value["$in"]:
                        return False
                    continue
                if doc.get(key) != value:
                    return False
            return True

        return sum(1 for doc in self.docs if _matches(doc, query))

    async def insert_one(self, doc: dict):
        self.docs.append(dict(doc))
        return None

    async def delete_one(self, query: dict):
        for idx, doc in enumerate(self.docs):
            if all(doc.get(k) == v for k, v in query.items()):
                self.docs.pop(idx)
                break
        return None

    async def update_one(self, query: dict, update: dict, **_kwargs):
        for idx, doc in enumerate(self.docs):
            if all(doc.get(k) == v for k, v in query.items()):
                patched = dict(doc)
                for key, value in (update.get("$set") or {}).items():
                    patched[key] = value
                self.docs[idx] = patched
                return _FakeUpdateResult(modified_count=1)
        return _FakeUpdateResult(modified_count=0)


class _FakeSystemAdminDb:
    def __init__(self, *, employee_identities=None, read_models=None, servicebook_entries=None, leave_applications=None):
        self.employee_identities = _FakeCollection(employee_identities)
        self.employee_profile_extensions = _FakeCollection([])
        self.employee_profile_read_models = _FakeCollection(read_models)
        self.employee_profiles_deleted = _FakeCollection([])
        self.servicebook_entries = _FakeCollection(servicebook_entries)
        self.service_book_entries = self.servicebook_entries
        self.leave_applications = _FakeCollection(leave_applications)


@pytest.mark.asyncio
async def test_delete_employee_http_returns_403_for_system_admin(client, monkeypatch):
    async def _fake_user(_request=None):
        return {"sub": "admin-1", "authorities": ["SYSTEM_ADMIN"], "permissions": []}

    async def _should_not_run(*_args, **_kwargs):
        raise AssertionError("transactional delete dependency should not run")

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    app.dependency_overrides[get_db] = lambda: object()

    monkeypatch.setattr(system_admin_router, "find_profile_view", _should_not_run)
    monkeypatch.setattr(system_admin_router, "count_servicebook_entries", _should_not_run)

    async with client as c:
        response = await c.post(
            "/api/system-admin/employees/EMP-1/delete",
            json={"reason": "Delete duplicate seeded employee"},
        )

    assert response.status_code == 403
    body = response.json()
    assert body["detail"]["error_code"] == "SYSTEM_ADMIN_FORBIDDEN"


@pytest.mark.asyncio
async def test_admin_cancel_leave_http_returns_403_for_system_admin(client, monkeypatch):
    async def _fake_user(_request=None):
        return {"sub": "admin-9", "authorities": ["SYSTEM_ADMIN"], "permissions": []}

    async def _should_not_run(*_args, **_kwargs):
        raise AssertionError("transactional leave dependency should not run")

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    app.dependency_overrides[get_db] = lambda: object()

    monkeypatch.setattr(system_admin_router, "get_leave_application_by_id", _should_not_run)
    monkeypatch.setattr(system_admin_router, "admin_cancel_leave_application", _should_not_run)

    async with client as c:
        response = await c.post(
            "/api/system-admin/leave/L-22/admin-cancel",
            json={"reason": "Cancel invalid duplicate leave request"},
        )

    assert response.status_code == 403
    body = response.json()
    assert body["detail"]["error_code"] == "SYSTEM_ADMIN_FORBIDDEN"


@pytest.mark.asyncio
async def test_delete_employee_http_real_contract_path_is_blocked(client):
    async def _fake_user(_request=None):
        return {"sub": "admin-real-1", "authorities": ["SYSTEM_ADMIN"], "permissions": []}

    fake_db = _FakeSystemAdminDb(
        employee_identities=[{"employee_id": "EMP-R1", "full_name": "Real Contract"}],
        read_models=[{"employee_id": "EMP-R1", "full_name": "Real Contract"}],
        servicebook_entries=[],
        leave_applications=[],
    )

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    app.dependency_overrides[get_db] = lambda: fake_db

    async with client as c:
        response = await c.post(
            "/api/system-admin/employees/EMP-R1/delete",
            json={"reason": "Delete seeded no-ledger employee"},
        )

    assert response.status_code == 403
    body = response.json()
    assert body["detail"]["error_code"] == "SYSTEM_ADMIN_FORBIDDEN"
    assert await fake_db.employee_identities.find_one({"employee_id": "EMP-R1"}) is not None
    archived = await fake_db.employee_profiles_deleted.find_one({"employee_id": "EMP-R1"})
    assert archived is None


@pytest.mark.asyncio
async def test_admin_cancel_leave_http_real_contract_path_is_blocked(client):
    async def _fake_user(_request=None):
        return {"sub": "admin-real-2", "authorities": ["SYSTEM_ADMIN"], "permissions": []}

    fake_db = _FakeSystemAdminDb(
        employee_identities=[],
        read_models=[],
        servicebook_entries=[],
        leave_applications=[
            {
                "id": "L-REAL-1",
                "employee_id": "EMP-R2",
                "status": "SUBMITTED",
                "remarks": "",
            }
        ],
    )

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    app.dependency_overrides[get_db] = lambda: fake_db

    async with client as c:
        response = await c.post(
            "/api/system-admin/leave/L-REAL-1/admin-cancel",
            json={"reason": "Cancel seeded pending leave"},
        )

    assert response.status_code == 403
    body = response.json()
    assert body["detail"]["error_code"] == "SYSTEM_ADMIN_FORBIDDEN"
    updated = await fake_db.leave_applications.find_one({"id": "L-REAL-1"})
    assert updated is not None
    assert updated["status"] == "SUBMITTED"
    assert "cancelled_by" not in updated
