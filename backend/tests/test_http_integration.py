"""
HTTP Integration Tests
======================
Tests that exercise real HTTP requests against the FastAPI app (without a
running server) using ``httpx.AsyncClient``.  This catches routing, middleware,
serialisation, and RBAC issues that unit-only tests miss.

Requirements: httpx, pytest-asyncio
"""

from __future__ import annotations

import os
import sys
import pytest

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Keep production strictness while making this test file self-contained.
os.environ.setdefault("JWT_SECRET", "integration-test-secret-key-at-least-32chars")
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "iems_test_db")

from httpx import ASGITransport, AsyncClient
from app.main import app  # the FastAPI application
from contexts.employee_master.identity.application import dependencies as employee_identity_deps
import contexts.employee_master.identity.api.read_router as employee_identity_read_module
import contexts.employee_master.identity.api.write_router as employee_identity_write_module
from contexts.employee_master.profile.application import dependencies as employee_deps
import contexts.employee_master.profile.api.write_router as employee_write_module
from app_platform import auth as shared_auth_module
from app_platform.config.settings import settings
from app_platform.db.runtime import get_db, get_db_optional
from contexts.identity.infrastructure import service as identity_service
from contexts.rbac.domain.models import TokenResponse, UserResponse

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TRANSPORT = ASGITransport(app=app)
BASE = "http://testserver"


@pytest.fixture
def client():
    """Synchronous-friendly factory - returns an async-context-manager."""
    return AsyncClient(transport=TRANSPORT, base_url=BASE)


# ---------------------------------------------------------------------------
# Health & Smoke
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_endpoint(client):
    async with client as c:
        r = await c.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_security_headers_present(client):
    async with client as c:
        r = await c.get("/api/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "script-src 'self'" in r.headers["content-security-policy"]
    assert "unsafe-eval" not in r.headers["content-security-policy"]


@pytest.mark.asyncio
async def test_cors_headers_on_preflight(client):
    async with client as c:
        r = await c.options(
            "/api/health",
            headers={
                "origin": "http://localhost:3000",
                "access-control-request-method": "GET",
            },
        )
    # Should see the CORS allow-origin header for a whitelisted origin
    assert r.headers.get("access-control-allow-origin") in (
        "http://localhost:3000",
        "*",
    )


@pytest.mark.asyncio
async def test_cors_headers_on_vite_preflight(client):
    async with client as c:
        r = await c.options(
            "/api/health",
            headers={
                "origin": "http://localhost:5173",
                "access-control-request-method": "GET",
            },
        )
    assert r.headers.get("access-control-allow-origin") in (
        "http://localhost:5173",
        "*",
    )


@pytest.mark.asyncio
async def test_cors_exposes_analytics_export_headers(client):
    async with client as c:
        r = await c.get(
            "/api/health",
            headers={"origin": "http://localhost:3000"},
        )

    exposed_headers = {
        header.strip().lower()
        for header in (r.headers.get("access-control-expose-headers") or "").split(",")
        if header.strip()
    }

    assert "content-disposition" in exposed_headers
    assert "x-iems-analytics-total" in exposed_headers
    assert "x-iems-analytics-exported" in exposed_headers


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_missing_body_returns_422(client):
    async with client as c:
        r = await c.post("/api/auth/login")
    assert r.status_code in (400, 422)  # validation/client payload error


@pytest.mark.asyncio
async def test_login_bad_credentials_not_500(client):
    async with client as c:
        r = await c.post(
            "/api/auth/login",
            json={"email": "nobody@example.com", "password": "wrong"},
        )
    # 401 (bad creds), 422 (validation), 429 (rate limit), 503 (no DB)
    assert r.status_code in (401, 422, 429, 503)
    if "application/json" in (r.headers.get("content-type") or ""):
        body = r.json()
        assert isinstance(body, dict)
        assert any(key in body for key in ("detail", "message", "error"))


@pytest.mark.asyncio
async def test_login_sets_refresh_cookie_and_redacts_body_refresh_token(client, monkeypatch):
    async def _fake_login(_db_optional, _credentials):
        return TokenResponse(
            access_token="access-token",
            refresh_token="refresh-token",
            user=UserResponse(
                id="u-1",
                email="user@example.com",
                name="User",
                authorities=["EMPLOYEE"],
                permissions=["PROFILE_READ_OWN"],
            ),
            expires_in=1800,
        )

    monkeypatch.setattr(identity_service, "login", _fake_login)

    original_samesite = settings.refresh_cookie_samesite
    original_secure = settings.refresh_cookie_secure
    object.__setattr__(settings, "refresh_cookie_samesite", "none")
    object.__setattr__(settings, "refresh_cookie_secure", True)

    try:
        async with client as c:
            r = await c.post(
                "/api/auth/login",
                json={"email": "user@example.com", "password": "strong-password"},
            )
    finally:
        object.__setattr__(settings, "refresh_cookie_samesite", original_samesite)
        object.__setattr__(settings, "refresh_cookie_secure", original_secure)

    assert r.status_code == 200
    body = r.json()
    assert body.get("access_token") == "access-token"
    assert body.get("refresh_token") is None

    set_cookie = r.headers.get("set-cookie", "")
    assert "iems_refresh_token=refresh-token" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "Secure" in set_cookie
    assert "SameSite=none" in set_cookie


@pytest.mark.asyncio
async def test_refresh_uses_cookie_and_rotates_refresh_cookie(client, monkeypatch):
    seen = {"token": None}

    async def _fake_refresh_access_token(_db, refresh_token):
        seen["token"] = refresh_token
        return {
            "access_token": "new-access",
            "refresh_token": "new-refresh",
            "token_type": "bearer",
            "expires_in": 1800,
            "user": {
                "id": "u-1",
                "email": "user@example.com",
                "name": "User",
                "authorities": ["EMPLOYEE"],
                "permissions": ["PROFILE_READ_OWN"],
            },
        }

    app.dependency_overrides[get_db] = lambda: object()
    monkeypatch.setattr(identity_service, "refresh_access_token", _fake_refresh_access_token)
    try:
        async with client as c:
            c.cookies.set("iems_refresh_token", "old-refresh")
            r = await c.post(
                "/api/auth/refresh",
            )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert r.status_code == 200
    assert seen["token"] == "old-refresh"
    assert r.json().get("refresh_token") is None
    set_cookie = r.headers.get("set-cookie", "")
    assert "iems_refresh_token=new-refresh" in set_cookie


@pytest.mark.asyncio
async def test_logout_uses_cookie_and_clears_refresh_cookie(client, monkeypatch):
    seen = {"token": None}

    async def _fake_logout(_db, refresh_token):
        seen["token"] = refresh_token
        return {"message": "Logged out successfully"}

    app.dependency_overrides[get_db_optional] = lambda: object()
    monkeypatch.setattr(identity_service, "logout", _fake_logout)
    try:
        async with client as c:
            c.cookies.set("iems_refresh_token", "refresh-to-revoke")
            r = await c.post(
                "/api/auth/logout",
            )
    finally:
        app.dependency_overrides.pop(get_db_optional, None)

    assert r.status_code == 200
    assert seen["token"] == "refresh-to-revoke"
    set_cookie = r.headers.get("set-cookie", "")
    assert "iems_refresh_token=" in set_cookie
    assert "Max-Age=0" in set_cookie


@pytest.mark.asyncio
async def test_protected_route_without_token(client):
    async with client as c:
        r = await c.get("/api/ess/dashboard")
    # 401 (no token) or 503 (DB offline and checked first) - never 200/500
    assert r.status_code in (401, 503)


@pytest.mark.asyncio
async def test_protected_route_with_bad_token(client):
    async with client as c:
        r = await c.get(
            "/api/ess/dashboard",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
    # 401 (bad token) or 503 (DB offline) - never 200/500
    assert r.status_code in (401, 503)


@pytest.mark.asyncio
async def test_forms_endpoint_requires_auth(client):
    async with client as c:
        r = await c.get("/api/forms/employee-profile")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_forms_endpoint_allows_profile_reader(client):
    async def _fake_user(_request=None):
        return {
            "sub": "forms-tester",
            "employee_id": "EMP-001",
            "authorities": ["EMPLOYEE"],
            "permissions": ["PROFILE_READ_OWN"],
        }

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    try:
        async with client as c:
            r = await c.get("/api/forms/employee-profile")
        assert r.status_code == 200
        payload = r.json()
        assert isinstance(payload, dict)
        assert "fields" in payload
    finally:
        app.dependency_overrides.pop(shared_auth_module.get_current_user, None)


@pytest.mark.asyncio
async def test_forms_endpoint_rejects_user_without_profile_permissions(client):
    async def _fake_user(_request=None):
        return {
            "sub": "forms-denied",
            "employee_id": "EMP-002",
            "authorities": ["EMPLOYEE"],
            "permissions": ["MASTER_READ"],
        }

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    try:
        async with client as c:
            r = await c.get("/api/forms/employee-profile")
        assert r.status_code == 403
    finally:
        app.dependency_overrides.pop(shared_auth_module.get_current_user, None)


# ---------------------------------------------------------------------------
# Route existence checks (regression guard against accidental removal)
# ---------------------------------------------------------------------------


EXPECTED_ROUTES = [
    "/api/health",
    "/api/auth/login",
    "/api/auth/refresh",
    "/api/auth/logout",
    "/api/users/",
    "/api/masters/departments",
    "/api/masters/designations",
    "/api/ess/dashboard",
    "/api/ess/my-documents",
    "/api/ess/my-documents/example.pdf",
    "/api/audit/logs",
    "/api/service-book/parts/SB_PART_I/schema",
    "/api/documents/document",
    "/api/documents/files",
    "/api/forms/employee-profile",
]


@pytest.mark.asyncio
@pytest.mark.parametrize("path", EXPECTED_ROUTES)
async def test_route_exists(client, path):
    """Every listed route should respond with something other than 404."""
    async with client as c:
        # Use GET; some routes may require auth -> 401 is fine; 404 is not.
        r = await c.get(path)
    assert r.status_code not in (404, 500), f"{path} returned {r.status_code} - route missing or crashing"


# ---------------------------------------------------------------------------
# Pagination upper-bound enforcement (issue #17)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pagination_rejects_excessive_limit(client):
    """Endpoints with Query(le=500) should reject limit > 500.

    Without a DB connection the endpoint may return 503 before reaching
    parameter validation - that is still acceptable (not 200).
    """
    async with client as c:
        r = await c.get(
            "/api/audit/logs?limit=9999",
            headers={"Authorization": "Bearer fake"},
        )
    # 422 (validation), 401 (auth), or 503 (DB offline) - never 200
    assert r.status_code in (401, 422, 503)


@pytest.mark.asyncio
async def test_pagination_rejects_negative_limit(client):
    async with client as c:
        r = await c.get(
            "/api/audit/logs?limit=-1",
            headers={"Authorization": "Bearer fake"},
        )
    assert r.status_code in (401, 422, 503)


@pytest.mark.asyncio
async def test_documents_upload_rejects_unsupported_entity_type_with_error_code(client):
    async def _fake_user(_request=None):
        return {
            "sub": "documents-uploader",
            "employee_id": "EMP-001",
            "authorities": ["EMPLOYEE"],
        }

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    try:
        async with client as c:
            r = await c.post(
                "/api/documents/document?entity_type=payroll&entity_id=PAY-1",
                files={"file": ("proof.pdf", b"%PDF-1.4\nentity-link", "application/pdf")},
            )
        assert r.status_code == 422
        detail = r.json()["detail"]
        assert detail["error_code"] == "DOCUMENT_ENTITY_TYPE_INVALID"
        assert detail["entity_type"] == "payroll"
        assert "Allowed types" in detail["message"]
    finally:
        app.dependency_overrides.pop(shared_auth_module.get_current_user, None)


@pytest.mark.asyncio
async def test_documents_upload_rejects_missing_entity_type_with_error_code(client):
    async def _fake_user(_request=None):
        return {
            "sub": "documents-uploader",
            "employee_id": "EMP-001",
            "authorities": ["EMPLOYEE"],
        }

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    try:
        async with client as c:
            r = await c.post(
                "/api/documents/document?entity_id=L-1",
                files={"file": ("proof.pdf", b"%PDF-1.4\nentity-link", "application/pdf")},
            )
        assert r.status_code == 422
        detail = r.json()["detail"]
        assert detail["error_code"] == "DOCUMENT_ENTITY_TYPE_REQUIRED"
        assert detail["entity_id"] == "L-1"
        assert detail["message"] == "entity_type is required when entity_id is provided"
    finally:
        app.dependency_overrides.pop(shared_auth_module.get_current_user, None)


@pytest.mark.asyncio
async def test_documents_upload_rejects_unsupported_document_type_with_error_code(client):
    async def _fake_user(_request=None):
        return {
            "sub": "documents-uploader",
            "employee_id": "EMP-001",
            "authorities": ["EMPLOYEE"],
        }

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    try:
        async with client as c:
            r = await c.post(
                "/api/documents/document?document_type=memo",
                files={"file": ("proof.pdf", b"%PDF-1.4\nentity-link", "application/pdf")},
            )
        assert r.status_code == 422
        detail = r.json()["detail"]
        assert detail["error_code"] == "DOCUMENT_TYPE_INVALID"
        assert detail["document_type"] == "memo"
        assert "Allowed types" in detail["message"]
    finally:
        app.dependency_overrides.pop(shared_auth_module.get_current_user, None)


@pytest.mark.asyncio
async def test_documents_upload_rejects_invalid_source_context_with_error_code(client):
    async def _fake_user(_request=None):
        return {
            "sub": "documents-uploader",
            "employee_id": "EMP-001",
            "authorities": ["EMPLOYEE"],
        }

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    try:
        async with client as c:
            r = await c.post(
                "/api/documents/document?source_context=service/book",
                files={"file": ("proof.pdf", b"%PDF-1.4\nentity-link", "application/pdf")},
            )
        assert r.status_code == 422
        detail = r.json()["detail"]
        assert detail["error_code"] == "DOCUMENT_SOURCE_CONTEXT_INVALID"
        assert detail["source_context"] == "service/book"
    finally:
        app.dependency_overrides.pop(shared_auth_module.get_current_user, None)


@pytest.mark.asyncio
async def test_documents_upload_rejects_invalid_category_with_error_code(client):
    async def _fake_user(_request=None):
        return {
            "sub": "documents-uploader",
            "employee_id": "EMP-001",
            "authorities": ["EMPLOYEE"],
        }

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    try:
        async with client as c:
            r = await c.post(
                "/api/documents/document?category=service/book",
                files={"file": ("proof.pdf", b"%PDF-1.4\nentity-link", "application/pdf")},
            )
        assert r.status_code == 422
        detail = r.json()["detail"]
        assert detail["error_code"] == "DOCUMENT_CATEGORY_INVALID"
        assert detail["category"] == "service/book"
    finally:
        app.dependency_overrides.pop(shared_auth_module.get_current_user, None)


@pytest.mark.asyncio
async def test_documents_list_rejects_invalid_source_context_filter_with_error_code(client):
    async def _fake_user(_request=None):
        return {
            "sub": "documents-reader",
            "employee_id": "EMP-001",
            "authorities": ["EMPLOYEE"],
        }

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    try:
        async with client as c:
            r = await c.get("/api/documents/files?source_context=service/book")
        assert r.status_code == 422
        detail = r.json()["detail"]
        assert detail["error_code"] == "DOCUMENT_SOURCE_CONTEXT_INVALID"
        assert detail["source_context"] == "service/book"
    finally:
        app.dependency_overrides.pop(shared_auth_module.get_current_user, None)


@pytest.mark.asyncio
async def test_documents_list_rejects_invalid_date_from_filter_with_error_code(client):
    async def _fake_user(_request=None):
        return {
            "sub": "documents-reader",
            "employee_id": "EMP-001",
            "authorities": ["EMPLOYEE"],
        }

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    try:
        async with client as c:
            r = await c.get("/api/documents/files?date_from=not-a-date")
        assert r.status_code == 422
        detail = r.json()["detail"]
        assert detail["error_code"] == "DOCUMENT_DATE_FROM_INVALID"
        assert detail["date_from"] == "not-a-date"
    finally:
        app.dependency_overrides.pop(shared_auth_module.get_current_user, None)


# ---------------------------------------------------------------------------
# Profile nominee-family enforcement (API-level)
# ---------------------------------------------------------------------------


class _FakeCountersCollection:
    async def find_one_and_update(self, *_args, **_kwargs):
        return {"seq": 1}


class _FakeInsertCollection:
    async def insert_one(self, *_args, **_kwargs):
        return None


class _FakeOutboxCollection:
    def __init__(self):
        self.events = []

    async def update_one(self, filter_doc, update, upsert=False):
        document = dict(update.get("$setOnInsert") or {})
        if upsert and document:
            document.update(filter_doc)
            self.events.append(document)
        return _FakeUpdateResult(modified_count=1)


class _FakeUpdateResult:
    def __init__(self, modified_count=1):
        self.modified_count = modified_count
        self.upserted_id = None


class _FakeEmployeeProfilesCollection:
    def __init__(self, initial_profile=None):
        self.by_employee_id = {}
        if isinstance(initial_profile, dict) and initial_profile.get("employee_id"):
            self.by_employee_id[initial_profile["employee_id"]] = dict(initial_profile)

    async def insert_one(self, doc):
        employee_id = doc.get("employee_id")
        if employee_id:
            self.by_employee_id[employee_id] = dict(doc)
        return None

    async def find_one(self, query, _projection=None):
        employee_id = query.get("employee_id")
        if employee_id in self.by_employee_id:
            return dict(self.by_employee_id[employee_id])
        return None

    async def update_one(self, query, update, upsert=False, **_kwargs):
        employee_id = query.get("employee_id")
        existing = self.by_employee_id.get(employee_id)
        if not existing:
            if upsert and employee_id:
                existing = {"employee_id": employee_id}
            else:
                return _FakeUpdateResult(modified_count=0)
        for key, value in (update.get("$set") or {}).items():
            if "." in key:
                head, tail = key.split(".", 1)
                nested = dict(existing.get(head) or {})
                nested[tail] = value
                existing[head] = nested
            else:
                existing[key] = value
        self.by_employee_id[employee_id] = existing
        return _FakeUpdateResult(modified_count=1)

    async def delete_one(self, query):
        employee_id = query.get("employee_id")
        self.by_employee_id.pop(employee_id, None)
        return _FakeUpdateResult(modified_count=1)


class _FakeDB:
    def __init__(self, initial_profile=None):
        self.counters = _FakeCountersCollection()
        self.employee_identities = _FakeEmployeeProfilesCollection(initial_profile=initial_profile)
        self.employee_profile_extensions = _FakeEmployeeProfilesCollection(initial_profile=initial_profile)
        self.employee_profile_read_models = _FakeEmployeeProfilesCollection(initial_profile=initial_profile)
        self.domain_violation_logs = _FakeInsertCollection()
        self.outbox_events = _FakeOutboxCollection()


def _patch_employee_profile_write_dependencies(
    monkeypatch,
    *,
    fake_db,
    fake_scope,
    noop_async=None,
):
    monkeypatch.setattr(employee_write_module, "get_db", lambda: fake_db)
    monkeypatch.setattr(
        employee_write_module,
        "require_permissions",
        lambda *_a, **_k: None,
        raising=False,
    )
    monkeypatch.setattr(employee_write_module, "enforce_profile_write_scope_or_raise", fake_scope)

    if noop_async is not None:
        monkeypatch.setattr(employee_write_module, "create_audit_log", noop_async)


def _patch_identity_write_dependencies(monkeypatch, *, fake_db):
    app.dependency_overrides[employee_identity_deps.get_db] = lambda: fake_db
    monkeypatch.setattr(
        employee_identity_write_module,
        "require_permissions",
        lambda *_a, **_k: None,
    )


async def _fake_scope(*_args, **_kwargs):
    return None


async def _fake_data_entry_user(_request=None):
    return {"sub": "tester", "authorities": ["GLOBAL_DATA_ENTRY"]}


async def _fake_dealing_assistant_user(_request=None):
    return {"sub": "dealing-assistant", "authorities": ["DEALING_ASSISTANT"]}


async def _noop_async(*_args, **_kwargs):
    return None


def _identity_create_payload(**overrides):
    payload = {
        "full_name": "Test Employee",
        "gender": "Male",
        "date_of_birth": "1990-01-01",
    }
    payload.update(overrides)
    return payload


def _validation_messages(response) -> str:
    detail = response.json().get("detail")
    assert isinstance(detail, list)
    return " ".join(
        str(item.get("msg") or "")
        for item in detail
        if isinstance(item, dict)
    )


@pytest.mark.asyncio
async def test_create_profile_rejects_profile_extension_fields_at_identity_boundary(
    client, monkeypatch
):
    fake_db = _FakeDB()
    app.dependency_overrides[employee_deps.get_current_user] = _fake_data_entry_user
    app.dependency_overrides[employee_identity_deps.get_current_user] = _fake_data_entry_user

    _patch_employee_profile_write_dependencies(
        monkeypatch,
        fake_db=fake_db,
        fake_scope=_fake_scope,
    )
    _patch_identity_write_dependencies(monkeypatch, fake_db=fake_db)

    payload = _identity_create_payload(
        mobile_primary="9876543210",
        father_name="Parent Name",
    )

    try:
        async with client as c:
            response = await c.post("/api/employee-identities/", json=payload)
        assert response.status_code == 422
        messages = _validation_messages(response)
        assert "Employee identity create accepts only core identity fields" in messages
        assert "Move non-identity fields to their owning context after the identity exists" in messages
        assert "father_name" in messages
    finally:
        app.dependency_overrides.pop(employee_deps.get_current_user, None)
        app.dependency_overrides.pop(employee_identity_deps.get_current_user, None)
        app.dependency_overrides.pop(employee_identity_deps.get_db, None)


@pytest.mark.asyncio
async def test_employee_identity_bootstrap_returns_editor_reference_data(client, monkeypatch):
    async def _fake_bootstrap(_db):
        return {
            "departments": [{"code": "FIN", "name": "Finance"}],
            "designations": [{"code": "SO", "name": "Section Officer"}],
            "employment_types": [{"code": "REGULAR", "label": "Regular"}],
        }

    async def _fake_identity_reader(_request=None):
        return {
            "sub": "tester",
            "authorities": ["GLOBAL_DATA_ENTRY"],
            "permissions": ["PROFILE_CREATE"],
        }

    app.dependency_overrides[employee_identity_deps.get_current_user] = _fake_identity_reader
    app.dependency_overrides[employee_identity_deps.get_db] = lambda: object()
    monkeypatch.setattr(
        employee_identity_read_module,
        "get_identity_editor_bootstrap",
        _fake_bootstrap,
    )

    try:
        async with client as c:
            response = await c.get("/api/employee-identities/bootstrap")
        assert response.status_code == 200
        assert response.json() == {
            "departments": [{"code": "FIN", "name": "Finance"}],
            "designations": [{"code": "SO", "name": "Section Officer"}],
            "employment_types": [{"code": "REGULAR", "label": "Regular"}],
        }
    finally:
        app.dependency_overrides.pop(employee_identity_deps.get_current_user, None)
        app.dependency_overrides.pop(employee_identity_deps.get_db, None)


@pytest.mark.asyncio
async def test_create_profile_rejects_service_book_owned_fields_at_identity_boundary(
    client, monkeypatch
):
    fake_db = _FakeDB()
    app.dependency_overrides[employee_deps.get_current_user] = _fake_data_entry_user
    app.dependency_overrides[employee_identity_deps.get_current_user] = _fake_data_entry_user

    _patch_employee_profile_write_dependencies(
        monkeypatch,
        fake_db=fake_db,
        fake_scope=_fake_scope,
    )
    _patch_identity_write_dependencies(monkeypatch, fake_db=fake_db)

    payload = _identity_create_payload(
        family_members=[{"name": "Asha", "relationship": "SPOUSE"}],
        previous_services=[{"post_held": "Assistant"}],
    )

    try:
        async with client as c:
            response = await c.post("/api/employee-identities/", json=payload)
        assert response.status_code == 422
        messages = _validation_messages(response)
        assert "Employee identity create accepts only core identity fields" in messages
        assert "identity-first 2-step contract" in messages
        assert "family_members" in messages
        assert "previous_services" in messages
    finally:
        app.dependency_overrides.pop(employee_deps.get_current_user, None)
        app.dependency_overrides.pop(employee_identity_deps.get_current_user, None)
        app.dependency_overrides.pop(employee_identity_deps.get_db, None)


@pytest.mark.asyncio
async def test_create_profile_accepts_identity_only_payload(client, monkeypatch):
    fake_db = _FakeDB()
    app.dependency_overrides[employee_deps.get_current_user] = _fake_data_entry_user
    app.dependency_overrides[employee_identity_deps.get_current_user] = _fake_data_entry_user

    _patch_employee_profile_write_dependencies(
        monkeypatch,
        fake_db=fake_db,
        fake_scope=_fake_scope,
        noop_async=_noop_async,
    )
    _patch_identity_write_dependencies(monkeypatch, fake_db=fake_db)

    monkeypatch.setattr(employee_write_module, "validate_form_data", lambda **_kwargs: [])

    payload = _identity_create_payload(
        full_name="Valid Identity Only Profile",
        current_designation_id="SO",
        current_office_id="HQ",
    )

    try:
        async with client as c:
            response = await c.post("/api/employee-identities/", json=payload)
        assert response.status_code == 200
        body = response.json()
        employee_id = body.get("employee_id")
        assert body.get("success") is True
        assert employee_id
        assert body.get("employee_code")

        identity_doc = fake_db.employee_identities.by_employee_id[employee_id]

        assert identity_doc["full_name"] == "Valid Identity Only Profile"
        assert identity_doc["current_designation_id"] == "SO"
        assert identity_doc["current_office_id"] == "HQ"
        assert employee_id not in fake_db.employee_profile_extensions.by_employee_id
        assert employee_id not in fake_db.employee_profile_read_models.by_employee_id
        event_names = [event.get("name") for event in fake_db.outbox_events.events]
        assert "EmployeeIdentityCreated" in event_names
        assert "EmployeeCreated" in event_names
        assert identity_doc.get("workflow_status") == "DRAFT"
    finally:
        app.dependency_overrides.pop(employee_deps.get_current_user, None)
        app.dependency_overrides.pop(employee_identity_deps.get_current_user, None)
        app.dependency_overrides.pop(employee_identity_deps.get_db, None)


@pytest.mark.asyncio
async def test_dealing_assistant_can_create_identity(client, monkeypatch):
    fake_db = _FakeDB()
    app.dependency_overrides[employee_deps.get_current_user] = _fake_dealing_assistant_user
    app.dependency_overrides[employee_identity_deps.get_current_user] = _fake_dealing_assistant_user

    _patch_employee_profile_write_dependencies(
        monkeypatch,
        fake_db=fake_db,
        fake_scope=_fake_scope,
        noop_async=_noop_async,
    )
    _patch_identity_write_dependencies(monkeypatch, fake_db=fake_db)

    try:
        async with client as c:
            response = await c.post(
                "/api/employee-identities/",
                json=_identity_create_payload(full_name="Dealing Assistant Identity"),
            )
        assert response.status_code == 200
        employee_id = response.json().get("employee_id")
        assert employee_id
        identity_doc = fake_db.employee_identities.by_employee_id[employee_id]
        assert identity_doc["created_by"] == "dealing-assistant"
        assert identity_doc["workflow_status"] == "DRAFT"
    finally:
        app.dependency_overrides.pop(employee_deps.get_current_user, None)
        app.dependency_overrides.pop(employee_identity_deps.get_current_user, None)
        app.dependency_overrides.pop(employee_identity_deps.get_db, None)


@pytest.mark.asyncio
async def test_create_then_update_profile_extension_completes_two_step_employee_creation_flow(
    client, monkeypatch
):
    fake_db = _FakeDB()
    app.dependency_overrides[employee_deps.get_current_user] = _fake_data_entry_user
    app.dependency_overrides[employee_identity_deps.get_current_user] = _fake_data_entry_user

    _patch_employee_profile_write_dependencies(
        monkeypatch,
        fake_db=fake_db,
        fake_scope=_fake_scope,
        noop_async=_noop_async,
    )
    _patch_identity_write_dependencies(monkeypatch, fake_db=fake_db)

    monkeypatch.setattr(employee_write_module, "validate_form_data", lambda **_kwargs: [])

    create_payload = _identity_create_payload(
        full_name="Two Step Employee",
        current_designation_id="SO",
    )
    extension_payload = {
        "father_name": "Parent Name",
        "mobile_primary": "9876543212",
        "address_line1": "Main Road",
        "city": "Pune",
        "state": "MH",
        "pincode": "411001",
    }

    try:
        async with client as c:
            create_response = await c.post("/api/employee-identities/", json=create_payload)
            assert create_response.status_code == 200
            employee_id = create_response.json()["employee_id"]

            update_response = await c.put(
                f"/api/employee-profiles/{employee_id}",
                json=extension_payload,
            )

        assert update_response.status_code == 200
        body = update_response.json()
        assert body.get("success") is True
        assert set(extension_payload.keys()).issubset(set(body.get("updated_fields", [])))

        extension_doc = fake_db.employee_profile_extensions.by_employee_id[employee_id]
        projection_doc = fake_db.employee_profile_read_models.by_employee_id[employee_id]

        assert extension_doc["father_name"] == "Parent Name"
        assert extension_doc["contact"]["mobile_primary"] == "9876543212"
        assert projection_doc["father_name"] == "Parent Name"
        assert projection_doc["mobile_primary"] == "9876543212"
    finally:
        app.dependency_overrides.pop(employee_deps.get_current_user, None)
        app.dependency_overrides.pop(employee_identity_deps.get_current_user, None)
        app.dependency_overrides.pop(employee_identity_deps.get_db, None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("employment_type", "extension_payload", "asserted_fields"),
    [
        (
            "CONTRACTUAL",
            {
                "father_name": "Parent Name",
                "mobile_primary": "9876543212",
                "address_line1": "Main Road",
                "city": "Pune",
                "state": "MH",
                "pincode": "411001",
                "contract_order_no": "CON-2025-001",
                "contract_start_date": "2025-01-01",
                "contract_end_date": "2025-12-31",
                "consolidated_pay": 50000,
                "contract_authority": "Director HR",
                "renewal_allowed": "YES",
            },
            {
                "contract_order_no": "CON-2025-001",
                "contract_start_date": "2025-01-01",
                "contract_end_date": "2025-12-31",
                "consolidated_pay": 50000,
                "contract_authority": "Director HR",
                "renewal_allowed": "YES",
            },
        ),
        (
            "DAILY_WAGE",
            {
                "father_name": "Parent Name",
                "mobile_primary": "9876543212",
                "address_line1": "Main Road",
                "city": "Pune",
                "state": "MH",
                "pincode": "411001",
                "engagement_order_no": "DW-2025-001",
                "muster_roll_number": "MR-2025-001",
                "daily_wage_rate": 750,
                "engagement_office": "District Office",
                "nature_of_work": "Data Entry",
            },
            {
                "engagement_order_no": "DW-2025-001",
                "muster_roll_number": "MR-2025-001",
                "daily_wage_rate": 750,
                "engagement_office": "District Office",
                "nature_of_work": "Data Entry",
            },
        ),
        (
            "DEPUTATION",
            {
                "father_name": "Parent Name",
                "mobile_primary": "9876543212",
                "address_line1": "Main Road",
                "city": "Pune",
                "state": "MH",
                "pincode": "411001",
                "deputation_order_no": "DEP-2025-001",
                "parent_department": "Finance Department",
                "parent_designation": "Section Officer",
                "lien_status": "RETAINED",
                "deputation_start_date": "2025-01-01",
                "deputation_end_date": "2025-12-31",
            },
            {
                "deputation_order_no": "DEP-2025-001",
                "parent_department": "Finance Department",
                "parent_designation": "Section Officer",
                "lien_status": "RETAINED",
                "deputation_start_date": "2025-01-01",
                "deputation_end_date": "2025-12-31",
            },
        ),
    ],
)
async def test_create_then_update_profile_extension_persists_type_specific_fields_across_employment_types(
    client, monkeypatch, employment_type, extension_payload, asserted_fields
):
    fake_db = _FakeDB()
    app.dependency_overrides[employee_deps.get_current_user] = _fake_data_entry_user
    app.dependency_overrides[employee_identity_deps.get_current_user] = _fake_data_entry_user

    _patch_employee_profile_write_dependencies(
        monkeypatch,
        fake_db=fake_db,
        fake_scope=_fake_scope,
        noop_async=_noop_async,
    )
    _patch_identity_write_dependencies(monkeypatch, fake_db=fake_db)

    monkeypatch.setattr(employee_write_module, "validate_form_data", lambda **_kwargs: [])

    create_payload = _identity_create_payload(
        full_name=f"{employment_type} Employee",
        current_designation_id="SO",
    )
    extension_payload = {
        "employment_type": employment_type,
        **extension_payload,
    }

    try:
        async with client as c:
            create_response = await c.post("/api/employee-identities/", json=create_payload)
            assert create_response.status_code == 200
            employee_id = create_response.json()["employee_id"]

            update_response = await c.put(
                f"/api/employee-profiles/{employee_id}",
                json=extension_payload,
            )

        assert update_response.status_code == 200
        body = update_response.json()
        assert body.get("success") is True
        assert set(extension_payload.keys()).issubset(set(body.get("updated_fields", [])))

        extension_doc = fake_db.employee_profile_extensions.by_employee_id[employee_id]
        projection_doc = fake_db.employee_profile_read_models.by_employee_id[employee_id]

        assert extension_doc["father_name"] == "Parent Name"
        assert extension_doc["contact"]["mobile_primary"] == "9876543212"
        assert projection_doc["father_name"] == "Parent Name"
        assert projection_doc["mobile_primary"] == "9876543212"

        for field, expected in asserted_fields.items():
            assert extension_doc[field] == expected
            assert projection_doc[field] == expected
    finally:
        app.dependency_overrides.pop(employee_deps.get_current_user, None)
        app.dependency_overrides.pop(employee_identity_deps.get_current_user, None)
        app.dependency_overrides.pop(employee_identity_deps.get_db, None)


@pytest.mark.asyncio
async def test_create_profile_blocks_on_actionable_forms_validation_error(
    client, monkeypatch
):
    fake_db = _FakeDB()
    app.dependency_overrides[employee_deps.get_current_user] = _fake_data_entry_user
    app.dependency_overrides[employee_identity_deps.get_current_user] = _fake_data_entry_user

    _patch_employee_profile_write_dependencies(
        monkeypatch,
        fake_db=fake_db,
        fake_scope=_fake_scope,
    )
    _patch_identity_write_dependencies(monkeypatch, fake_db=fake_db)

    monkeypatch.setattr(
        employee_write_module,
        "validate_form_data",
        lambda **_kwargs: [
            {
                "field_id": "mobile_primary",
                "error_type": "required",
                "message": "Mobile Number is required",
            }
        ],
    )

    try:
        async with client as c:
            create_response = await c.post(
                "/api/employee-identities/",
                json=_identity_create_payload(full_name="Blocked by Forms"),
            )
            assert create_response.status_code == 200
            employee_id = create_response.json()["employee_id"]
            response = await c.put(
                f"/api/employee-profiles/{employee_id}",
                json={"mobile_primary": ""},
            )
        assert response.status_code == 422
        detail = response.json().get("detail", {})
        assert detail.get("error_code") == "FORM_VALIDATION_FAILED"
        assert any(err.get("field_id") == "mobile_primary" for err in (detail.get("errors") or []))
    finally:
        app.dependency_overrides.pop(employee_deps.get_current_user, None)
        app.dependency_overrides.pop(employee_identity_deps.get_current_user, None)
        app.dependency_overrides.pop(employee_identity_deps.get_db, None)


@pytest.mark.asyncio
async def test_create_profile_blocks_on_conditional_required_forms_error(client, monkeypatch):
    fake_db = _FakeDB()
    app.dependency_overrides[employee_deps.get_current_user] = _fake_data_entry_user
    app.dependency_overrides[employee_identity_deps.get_current_user] = _fake_data_entry_user

    _patch_employee_profile_write_dependencies(
        monkeypatch,
        fake_db=fake_db,
        fake_scope=_fake_scope,
    )
    _patch_identity_write_dependencies(monkeypatch, fake_db=fake_db)

    monkeypatch.setattr(
        employee_write_module,
        "validate_form_data",
        lambda **_kwargs: [
            {
                "field_id": "agency_name",
                "error_type": "required",
                "message": "Outsourcing Agency is required",
            }
        ],
    )

    try:
        async with client as c:
            create_response = await c.post(
                "/api/employee-identities/",
                json=_identity_create_payload(
                    full_name="Outsourced Employee",
                    current_designation_id="DEO",
                ),
            )
            assert create_response.status_code == 200
            employee_id = create_response.json()["employee_id"]
            response = await c.put(
                f"/api/employee-profiles/{employee_id}",
                json={"agency_name": ""},
            )
        assert response.status_code == 422
        detail = response.json().get("detail", {})
        assert detail.get("error_code") == "FORM_VALIDATION_FAILED"
        assert any(err.get("field_id") == "agency_name" for err in (detail.get("errors") or []))
    finally:
        app.dependency_overrides.pop(employee_deps.get_current_user, None)
        app.dependency_overrides.pop(employee_identity_deps.get_current_user, None)
        app.dependency_overrides.pop(employee_identity_deps.get_db, None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "employment_type",
    ["OUTSOURCED", "CONTRACTUAL", "DEPUTATION", "DAILY_WAGE", "REEMPLOYED"],
)
async def test_identity_create_allows_missing_designation_for_conditional_types(
    client, monkeypatch, employment_type
):
    fake_db = _FakeDB()
    app.dependency_overrides[employee_deps.get_current_user] = _fake_data_entry_user
    app.dependency_overrides[employee_identity_deps.get_current_user] = _fake_data_entry_user

    _patch_employee_profile_write_dependencies(
        monkeypatch,
        fake_db=fake_db,
        fake_scope=_fake_scope,
    )
    _patch_identity_write_dependencies(monkeypatch, fake_db=fake_db)

    try:
        async with client as c:
            response = await c.post(
                "/api/employee-identities/",
                json=_identity_create_payload(
                    full_name=f"{employment_type} Without Designation",
                ),
            )
        assert response.status_code == 200
        body = response.json()
        assert body.get("success") is True
        assert body.get("employee_id")
    finally:
        app.dependency_overrides.pop(employee_deps.get_current_user, None)
        app.dependency_overrides.pop(employee_identity_deps.get_current_user, None)
        app.dependency_overrides.pop(employee_identity_deps.get_db, None)


@pytest.mark.asyncio
async def test_create_profile_regular_extension_requirements_do_not_block_identity_creation(
    client, monkeypatch
):
    fake_db = _FakeDB()
    app.dependency_overrides[employee_deps.get_current_user] = _fake_data_entry_user
    app.dependency_overrides[employee_identity_deps.get_current_user] = _fake_data_entry_user

    _patch_employee_profile_write_dependencies(
        monkeypatch,
        fake_db=fake_db,
        fake_scope=_fake_scope,
        noop_async=_noop_async,
    )
    _patch_identity_write_dependencies(monkeypatch, fake_db=fake_db)

    try:
        async with client as c:
            response = await c.post(
                "/api/employee-identities/",
                json=_identity_create_payload(
                    full_name="Regular Identity Only Create",
                ),
            )
        assert response.status_code == 200
        body = response.json()
        assert body.get("success") is True
        assert body.get("employee_id")
    finally:
        app.dependency_overrides.pop(employee_deps.get_current_user, None)
        app.dependency_overrides.pop(employee_identity_deps.get_current_user, None)
        app.dependency_overrides.pop(employee_identity_deps.get_db, None)


@pytest.mark.asyncio
async def test_update_profile_rejects_service_book_owned_fields(client, monkeypatch):
    async def _fake_scope(*_args, **_kwargs):
        return None

    async def _fake_user(_request=None):
        return {"sub": "tester", "authorities": ["DEPT_DATA_ENTRY"]}

    initial_profile = {
        "employee_id": "EMP-UPDATE-1",
        "workflow_status": "DRAFT",
        "contact": {"mobile_primary": "9876543210"},
        "version": 1,
    }
    fake_db = _FakeDB(initial_profile=initial_profile)
    app.dependency_overrides[employee_deps.get_current_user] = _fake_user

    _patch_employee_profile_write_dependencies(
        monkeypatch,
        fake_db=fake_db,
        fake_scope=_fake_scope,
    )

    payload = {"pcf_nomination": [{"name": "Ravi", "relationship": "SON", "share_percent": 100}]}

    try:
        async with client as c:
            response = await c.put("/api/employee-profiles/EMP-UPDATE-1", json=payload)
        assert response.status_code == 422
        messages = _validation_messages(response)
        assert "Employee profile extension update accepts only employee-owned profile fields" in messages
        assert "pcf_nomination" in messages
    finally:
        app.dependency_overrides.pop(employee_deps.get_current_user, None)


@pytest.mark.asyncio
async def test_update_profile_rejects_part_iii_fields(client, monkeypatch):
    async def _fake_scope(*_args, **_kwargs):
        return None

    async def _fake_user(_request=None):
        return {"sub": "tester", "authorities": ["DEPT_DATA_ENTRY"]}

    initial_profile = {
        "employee_id": "EMP-UPDATE-2",
        "workflow_status": "DRAFT",
        "contact": {"mobile_primary": "9876543213"},
        "version": 1,
    }
    fake_db = _FakeDB(initial_profile=initial_profile)
    app.dependency_overrides[employee_deps.get_current_user] = _fake_user

    _patch_employee_profile_write_dependencies(
        monkeypatch,
        fake_db=fake_db,
        fake_scope=_fake_scope,
    )

    payload = {"previous_services": [{"post_held": "Assistant"}]}

    try:
        async with client as c:
            response = await c.put("/api/employee-profiles/EMP-UPDATE-2", json=payload)
        assert response.status_code == 422
        messages = _validation_messages(response)
        assert "Employee profile extension update accepts only employee-owned profile fields" in messages
        assert "previous_services" in messages
    finally:
        app.dependency_overrides.pop(employee_deps.get_current_user, None)


@pytest.mark.asyncio
async def test_update_profile_blocks_on_forms_validation_error(client, monkeypatch):
    async def _fake_scope(*_args, **_kwargs):
        return None

    async def _fake_user(_request=None):
        return {"sub": "tester", "authorities": ["DEPT_DATA_ENTRY"]}

    initial_profile = {
        "employee_id": "EMP-UPDATE-FORMS-1",
        "workflow_status": "DRAFT",
        "employment_type": "REGULAR",
        "contact": {"mobile_primary": "9876543299"},
        "version": 1,
    }
    fake_db = _FakeDB(initial_profile=initial_profile)
    app.dependency_overrides[employee_deps.get_current_user] = _fake_user

    _patch_employee_profile_write_dependencies(
        monkeypatch,
        fake_db=fake_db,
        fake_scope=_fake_scope,
    )

    monkeypatch.setattr(
        employee_write_module,
        "validate_form_data",
        lambda **_kwargs: [{"field_id": "mobile_number", "error_type": "required", "message": "Mobile Number is required"}],
    )

    payload = {
        "mobile_primary": "",
    }

    try:
        async with client as c:
            response = await c.put("/api/employee-profiles/EMP-UPDATE-FORMS-1", json=payload)
        assert response.status_code == 422
        detail = response.json().get("detail", {})
        assert detail.get("error_code") == "FORM_VALIDATION_FAILED"
        assert any(err.get("field_id") == "mobile_number" for err in (detail.get("errors") or []))
    finally:
        app.dependency_overrides.pop(employee_deps.get_current_user, None)


@pytest.mark.asyncio
async def test_update_profile_regular_service_history_fields_are_rejected(client, monkeypatch):
    async def _fake_scope(*_args, **_kwargs):
        return None

    async def _fake_user(_request=None):
        return {"sub": "tester", "authorities": ["DEPT_DATA_ENTRY"]}

    initial_profile = {
        "employee_id": "EMP-UPDATE-REG-SERVICE-1",
        "workflow_status": "DRAFT",
        "employment_type": "REGULAR",
        "service": "GROUP-A",
        "pension_scheme": "NPS",
        "contact": {"mobile_primary": "9876543299"},
        "version": 1,
    }
    fake_db = _FakeDB(initial_profile=initial_profile)
    app.dependency_overrides[employee_deps.get_current_user] = _fake_user

    _patch_employee_profile_write_dependencies(
        monkeypatch,
        fake_db=fake_db,
        fake_scope=_fake_scope,
    )

    payload = {
        "service": "",
    }

    try:
        async with client as c:
            response = await c.put("/api/employee-profiles/EMP-UPDATE-REG-SERVICE-1", json=payload)
        assert response.status_code == 422
        messages = _validation_messages(response)
        assert "Employee profile extension update accepts only employee-owned profile fields" in messages
        assert "service" in messages
    finally:
        app.dependency_overrides.pop(employee_deps.get_current_user, None)


@pytest.mark.asyncio
async def test_update_profile_regular_pension_scheme_is_rejected(client, monkeypatch):
    async def _fake_scope(*_args, **_kwargs):
        return None

    async def _fake_user(_request=None):
        return {"sub": "tester", "authorities": ["DEPT_DATA_ENTRY"]}

    initial_profile = {
        "employee_id": "EMP-UPDATE-REG-PENSION-1",
        "workflow_status": "DRAFT",
        "employment_type": "REGULAR",
        "service": "GROUP-A",
        "pension_scheme": "NPS",
        "contact": {"mobile_primary": "9876543298"},
        "version": 1,
    }
    fake_db = _FakeDB(initial_profile=initial_profile)
    app.dependency_overrides[employee_deps.get_current_user] = _fake_user

    _patch_employee_profile_write_dependencies(
        monkeypatch,
        fake_db=fake_db,
        fake_scope=_fake_scope,
    )

    payload = {
        "pension_scheme": "",
    }

    try:
        async with client as c:
            response = await c.put("/api/employee-profiles/EMP-UPDATE-REG-PENSION-1", json=payload)
        assert response.status_code == 422
        messages = _validation_messages(response)
        assert "Employee profile extension update accepts only employee-owned profile fields" in messages
        assert "pension_scheme" in messages
    finally:
        app.dependency_overrides.pop(employee_deps.get_current_user, None)


@pytest.mark.asyncio
async def test_update_profile_contractual_rejects_pension_scheme(client, monkeypatch):
    async def _fake_scope(*_args, **_kwargs):
        return None

    async def _fake_user(_request=None):
        return {"sub": "tester", "authorities": ["DEPT_DATA_ENTRY"]}

    initial_profile = {
        "employee_id": "EMP-UPDATE-CON-PENSION-1",
        "workflow_status": "DRAFT",
        "employment_type": "CONTRACTUAL",
        "contact": {"mobile_primary": "9876543296"},
        "version": 1,
    }
    fake_db = _FakeDB(initial_profile=initial_profile)
    app.dependency_overrides[employee_deps.get_current_user] = _fake_user

    _patch_employee_profile_write_dependencies(
        monkeypatch,
        fake_db=fake_db,
        fake_scope=_fake_scope,
    )

    payload = {
        "pension_scheme": "NPS",
    }

    try:
        async with client as c:
            response = await c.put(
                "/api/employee-profiles/EMP-UPDATE-CON-PENSION-1",
                json=payload,
            )
        assert response.status_code == 422
        messages = _validation_messages(response)
        assert "Employee profile extension update accepts only employee-owned profile fields" in messages
        assert "pension_scheme" in messages
    finally:
        app.dependency_overrides.pop(employee_deps.get_current_user, None)


@pytest.mark.asyncio
async def test_update_profile_regular_unrelated_field_update_not_blocked_by_missing_required_fields(client, monkeypatch):
    async def _fake_scope(*_args, **_kwargs):
        return None

    async def _fake_user(_request=None):
        return {"sub": "tester", "authorities": ["DEPT_DATA_ENTRY"]}

    async def _noop_async(*_args, **_kwargs):
        return None

    initial_profile = {
        "employee_id": "EMP-UPDATE-REG-PASS-1",
        "workflow_status": "DRAFT",
        "employment_type": "REGULAR",
        "service": "GROUP-A",
        "pension_scheme": "NPS",
        "contact": {"mobile_primary": "9876543297"},
        "version": 1,
    }
    fake_db = _FakeDB(initial_profile=initial_profile)
    app.dependency_overrides[employee_deps.get_current_user] = _fake_user

    _patch_employee_profile_write_dependencies(
        monkeypatch,
        fake_db=fake_db,
        fake_scope=_fake_scope,
        noop_async=_noop_async,
    )

    # Simulate forms engine reporting missing required regular fields in merged data,
    # but these fields are not being updated in this request.
    monkeypatch.setattr(
        employee_write_module,
        "validate_form_data",
        lambda **_kwargs: [
            {"field_id": "service_group", "error_type": "required", "message": "Service Group is required"},
            {"field_id": "pension_scheme", "error_type": "required", "message": "Pension Scheme is required"},
        ],
    )

    payload = {
        "mobile_primary": "9876543200",
    }

    try:
        async with client as c:
            response = await c.put("/api/employee-profiles/EMP-UPDATE-REG-PASS-1", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body.get("success") is True
        assert "mobile_primary" in body.get("updated_fields", [])
    finally:
        app.dependency_overrides.pop(employee_deps.get_current_user, None)




