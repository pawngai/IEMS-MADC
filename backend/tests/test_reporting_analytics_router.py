from __future__ import annotations

from io import BytesIO

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.responses import StreamingResponse

from app.main import app
from app_platform.auth.current_user import get_current_user
from app_platform.db.runtime import get_db
from contexts.identity_access.rbac.domain.models import Permission
from contexts.reporting_analytics.api import router as reporting_router_module


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_reporting_drilldown_forwards_request_to_query_service(client, monkeypatch):
    captured: dict = {}

    async def _fake_user():
        return {"sub": "actor-1", "permissions": [Permission.PROFILE_READ_ALL.value]}

    async def _fake_get_drilldown(self, *, section, dimension, value=None, values=None, limit=50):
        captured.update(
            section=section,
            dimension=dimension,
            value=value,
            values=values,
            limit=limit,
        )
        return {"section": section, "dimension": dimension, "total": 1, "rows": []}

    app.dependency_overrides[get_current_user] = _fake_user
    app.dependency_overrides[get_db] = lambda: object()
    monkeypatch.setattr(reporting_router_module.AnalyticsQueryService, "get_drilldown", _fake_get_drilldown)

    async with client as c:
        response = await c.get(
            "/api/reporting/analytics/drilldown",
            params={
                "section": "workforce",
                "dimension": "gender",
                "values": "Male,MALE",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    assert response.json()["section"] == "workforce"
    assert captured == {
        "section": "workforce",
        "dimension": "gender",
        "value": None,
        "values": "Male,MALE",
        "limit": 25,
    }


@pytest.mark.asyncio
async def test_reporting_drilldown_accepts_export_sized_limit(client, monkeypatch):
    captured: dict = {}

    async def _fake_user():
        return {"sub": "actor-1", "permissions": [Permission.PROFILE_READ_ALL.value]}

    async def _fake_get_drilldown(self, *, section, dimension, value=None, values=None, limit=50):
        captured.update(limit=limit, section=section, dimension=dimension)
        return {"section": section, "dimension": dimension, "total": 0, "rows": []}

    app.dependency_overrides[get_current_user] = _fake_user
    app.dependency_overrides[get_db] = lambda: object()
    monkeypatch.setattr(reporting_router_module.AnalyticsQueryService, "get_drilldown", _fake_get_drilldown)

    async with client as c:
        response = await c.get(
            "/api/reporting/analytics/drilldown",
            params={"section": "workforce", "dimension": "all", "limit": 617},
        )

    assert response.status_code == 200
    assert captured == {"limit": 617, "section": "workforce", "dimension": "all"}


@pytest.mark.asyncio
async def test_reporting_drilldown_export_forwards_request_and_headers(client, monkeypatch):
    captured: dict = {}

    async def _fake_user():
        return {"sub": "actor-1", "permissions": [Permission.PROFILE_READ_ALL.value]}

    async def _fake_export_response(*, db, section, dimension, value=None, values=None, limit=5000):
        captured.update(
            db=db,
            section=section,
            dimension=dimension,
            value=value,
            values=values,
            limit=limit,
        )
        return StreamingResponse(
            iter(["Employee ID\nemp-1\n"]),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="analytics-workforce.csv"'},
        )

    app.dependency_overrides[get_current_user] = _fake_user
    app.dependency_overrides[get_db] = lambda: object()
    monkeypatch.setattr(reporting_router_module, "build_drilldown_csv_response", _fake_export_response)

    async with client as c:
        response = await c.get(
            "/api/reporting/analytics/drilldown/export",
            params={
                "section": "workforce",
                "dimension": "status",
                "value": "ACTIVE",
                "limit": 500,
            },
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == 'attachment; filename="analytics-workforce.csv"'
    assert captured["section"] == "workforce"
    assert captured["dimension"] == "status"
    assert captured["value"] == "ACTIVE"
    assert captured["values"] is None
    assert captured["limit"] == 500


@pytest.mark.asyncio
async def test_reporting_drilldown_requires_leave_permission_for_leave_section(client):
    async def _fake_user():
        return {"sub": "actor-1", "permissions": [Permission.PROFILE_READ_ALL.value]}

    app.dependency_overrides[get_current_user] = _fake_user
    app.dependency_overrides[get_db] = lambda: object()

    async with client as c:
        response = await c.get(
            "/api/reporting/analytics/drilldown",
            params={"section": "leave", "dimension": "status", "value": "SANCTIONED"},
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_reporting_drilldown_export_requires_leave_permission_for_leave_section(client):
    async def _fake_user():
        return {"sub": "actor-1", "permissions": [Permission.PROFILE_READ_ALL.value]}

    app.dependency_overrides[get_current_user] = _fake_user
    app.dependency_overrides[get_db] = lambda: object()

    async with client as c:
        response = await c.get(
            "/api/reporting/analytics/drilldown/export",
            params={"section": "leave", "dimension": "status", "value": "SANCTIONED"},
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_reporting_drilldown_allows_service_events_with_service_book_permission(client, monkeypatch):
    async def _fake_user():
        return {"sub": "actor-1", "permissions": [Permission.SERVICE_BOOK_READ_ALL.value]}

    async def _fake_get_drilldown(self, *, section, dimension, value=None, values=None, limit=50):
        return {"section": section, "dimension": dimension, "value": value, "total": 0, "rows": []}

    app.dependency_overrides[get_current_user] = _fake_user
    app.dependency_overrides[get_db] = lambda: object()
    monkeypatch.setattr(reporting_router_module.AnalyticsQueryService, "get_drilldown", _fake_get_drilldown)

    async with client as c:
        response = await c.get(
            "/api/reporting/analytics/drilldown",
            params={"section": "serviceEvents", "dimension": "recent_30d"},
        )

    assert response.status_code == 200
    assert response.json()["section"] == "serviceEvents"


@pytest.mark.asyncio
async def test_reporting_drilldown_rejects_unknown_section(client):
    async def _fake_user():
        return {"sub": "actor-1", "permissions": [Permission.PROFILE_READ_ALL.value]}

    app.dependency_overrides[get_current_user] = _fake_user
    app.dependency_overrides[get_db] = lambda: object()

    async with client as c:
        response = await c.get(
            "/api/reporting/analytics/drilldown",
            params={"section": "unknown", "dimension": "all"},
        )

    assert response.status_code == 400
    assert "Unsupported analytics drilldown section" in response.json()["detail"]