from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app_platform import auth as shared_auth_module
from contexts.identity.api import users_router as users_router_module


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    try:
        yield
    finally:
        app.dependency_overrides.pop(shared_auth_module.get_current_user, None)
        app.dependency_overrides.pop(users_router_module.get_db, None)


@pytest.mark.asyncio
async def test_list_employee_directory_route_returns_identity_payload(client, monkeypatch):
    async def _fake_user(_request=None):
        return {"sub": "admin-1", "authorities": ["SYSTEM_ADMIN"], "permissions": []}

    captured = {}

    async def _fake_list_employee_directory(_db, **kwargs):
        captured["list"] = kwargs
        return [{"employee_id": "EMP-1", "full_name": "Alice"}]

    async def _fake_get_employee_directory_count(_db, **kwargs):
        captured["count"] = kwargs
        return {"count": 1}

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    app.dependency_overrides[users_router_module.get_db] = lambda: object()

    monkeypatch.setattr(users_router_module.identity_service, "list_employee_directory", _fake_list_employee_directory)
    monkeypatch.setattr(users_router_module.identity_service, "get_employee_directory_count", _fake_get_employee_directory_count)

    async with client as c:
        response = await c.get(
            "/api/users/employees",
            params={
                "skip": 10,
                "limit": 25,
                "search": "alice",
                "department": "FIN",
                "employment_type": "REGULAR",
                "workflow_status": "APPROVED",
                "designation_id": "DESIG-1",
                "office_id": "OFF-1",
                "employee_status": "ACTIVE",
                "recruitment_mode": "DIRECT",
                "pay_level": "L10",
                "service": "IAS",
                "service_group": "A",
                "date_from": "2026-01-01",
                "date_to": "2026-12-31",
                "sort_by": "employee_code",
                "sort_dir": "desc",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "employees": [{"employee_id": "EMP-1", "full_name": "Alice"}],
        "total": 1,
        "limit": 25,
        "offset": 10,
    }
    assert captured["list"]["skip"] == 10
    assert captured["list"]["limit"] == 25
    assert captured["list"]["search"] == "alice"
    assert captured["list"]["department"] == "FIN"
    assert captured["list"]["employment_type"] == "REGULAR"
    assert captured["list"]["workflow_status"] == "APPROVED"
    assert captured["list"]["designation_id"] == "DESIG-1"
    assert captured["list"]["office_id"] == "OFF-1"
    assert captured["list"]["employee_status"] == "ACTIVE"
    assert captured["list"]["recruitment_mode"] == "DIRECT"
    assert captured["list"]["pay_level"] == "L10"
    assert captured["list"]["service"] == "IAS"
    assert captured["list"]["service_group"] == "A"
    assert captured["list"]["date_from"] == "2026-01-01"
    assert captured["list"]["date_to"] == "2026-12-31"
    assert captured["list"]["sort_by"] == "employee_code"
    assert captured["list"]["sort_dir"] == "desc"
    assert captured["count"] == {
        "search": "alice",
        "department": "FIN",
        "employment_type": "REGULAR",
        "workflow_status": "APPROVED",
        "designation_id": "DESIG-1",
        "office_id": "OFF-1",
        "employee_status": "ACTIVE",
        "recruitment_mode": "DIRECT",
        "pay_level": "L10",
        "service": "IAS",
        "service_group": "A",
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "current_user": {"sub": "admin-1", "authorities": ["SYSTEM_ADMIN"], "permissions": []},
    }


@pytest.mark.asyncio
async def test_list_employee_directory_route_is_not_captured_by_user_id_route(client, monkeypatch):
    async def _fake_user(_request=None):
        return {"sub": "admin-2", "authorities": ["SYSTEM_ADMIN"], "permissions": []}

    async def _fake_list_employee_directory(_db, **_kwargs):
        return []

    async def _fake_get_employee_directory_count(_db, **_kwargs):
        return {"count": 0}

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    app.dependency_overrides[users_router_module.get_db] = lambda: object()

    monkeypatch.setattr(users_router_module.identity_service, "list_employee_directory", _fake_list_employee_directory)
    monkeypatch.setattr(users_router_module.identity_service, "get_employee_directory_count", _fake_get_employee_directory_count)

    async with client as c:
        response = await c.get("/api/users/employees")

    assert response.status_code == 200
    assert response.json()["employees"] == []