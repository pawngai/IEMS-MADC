from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from contexts.service_book.records.api import router as service_events_router_module
from contexts.service_book.records.api.dependencies import get_service_events_service
from contexts.identity_access.rbac.domain.models import Permission
from app_platform import auth as shared_auth_module
from app_platform.db.runtime import get_db
from shared_kernel.base import DomainError


class _StubServiceEventsService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object, str | None]] = []
        self.verify_error: Exception | None = None
        self.stream_response: dict = {"employee_id": "EMP-100", "events": []}

    async def record(self, *, command, actor_id):
        self.calls.append(("record", command, actor_id))
        return {"ok": True, "service_event_id": "SE-REC-1"}

    async def revise(self, *, command, actor_id):
        self.calls.append(("revise", command, actor_id))
        return {
            "ok": True,
            "service_event_id": command.service_event_id,
            "reason": command.reason,
        }

    async def submit(self, *, command, actor_id):
        self.calls.append(("submit", command, actor_id))
        return {"ok": True, "service_event_id": command.service_event_id}

    async def verify(self, *, command, actor_id):
        self.calls.append(("verify", command, actor_id))
        if self.verify_error is not None:
            raise self.verify_error
        return {"ok": True, "service_event_id": command.service_event_id}

    async def lock(self, *, command, actor_id):
        self.calls.append(("lock", command, actor_id))
        return {"ok": True, "service_event_id": command.service_event_id, "status": "LOCKED"}

    async def attach_document(self, *, command, actor_id):
        self.calls.append(("attach_document", command, actor_id))
        return {
            "ok": True,
            "service_event_id": command.service_event_id,
            "document_id": command.document_id,
            "documents_count": 1,
        }

    async def get_stream(self, *, employee_id):
        self.calls.append(("get_stream", employee_id, None))
        return self.stream_response


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    try:
        yield
    finally:
        app.dependency_overrides.pop(shared_auth_module.get_current_user, None)
        app.dependency_overrides.pop(get_service_events_service, None)
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_record_service_event_owner_allowed_and_contract_forwarded(client):
    stub = _StubServiceEventsService()

    async def _fake_user(_request=None):
        return {"sub": "actor-1", "employee_id": "EMP-100", "permissions": []}

    async def _fake_resolve_identity_ref(_db, *, ref, projection=None):
        _ = projection
        if ref == "EMP-100":
            return {"employee_id": "EMP-100", "employment_type": "REGULAR"}
        return None

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    app.dependency_overrides[get_service_events_service] = lambda: stub
    app.dependency_overrides[get_db] = lambda: object()
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(service_events_router_module, "resolve_identity_ref", _fake_resolve_identity_ref)

    payload = {
        "employee_id": "EMP-100",
        "event_type": "SUSPENSION",
        "part_code": "IV",
        "payload": {
            "suspension_date": "2026-03-14",
            "reason": "Pending enquiry",
        },
    }

    async with client as c:
        response = await c.post("/api/service-book/records", json=payload)

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert len(stub.calls) == 1

    call_name, command, actor_id = stub.calls[0]
    assert call_name == "record"
    assert command.employee_id == "EMP-100"
    assert command.event_type.value == "SUSPENSION"
    assert command.payload["reason"] == "Pending enquiry"
    assert command.part_code == "IV"
    assert actor_id == "actor-1"
    monkeypatch.undo()


@pytest.mark.asyncio
async def test_record_service_event_rejects_unresolved_employee_ref(client, monkeypatch):
    stub = _StubServiceEventsService()

    async def _fake_user(_request=None):
        return {
            "sub": "actor-1",
            "employee_id": "EMP-200",
            "permissions": [],
        }

    async def _missing_identity(_db, *, ref, projection=None):
        _ = (ref, projection)
        return None

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    app.dependency_overrides[get_service_events_service] = lambda: stub
    app.dependency_overrides[get_db] = lambda: object()
    monkeypatch.setattr(service_events_router_module, "resolve_identity_ref", _missing_identity)

    async with client as c:
        response = await c.post(
            "/api/service-book/records",
            json={
                "employee_id": "DOES-NOT-EXIST",
                "event_type": "GENERIC",
                "part_code": "IV",
                "payload": {"order_no": "X", "order_date": "2026-04-05"},
            },
        )

    assert response.status_code == 404
    assert response.json()["detail"]["error_code"] == "EMPLOYEE_NOT_FOUND"
    assert stub.calls == []


@pytest.mark.asyncio
async def test_record_service_event_rejects_non_regular_employee_ref(client, monkeypatch):
    stub = _StubServiceEventsService()

    async def _fake_user(_request=None):
        return {
            "sub": "actor-1",
            "employee_id": "EMP-200",
            "permissions": [],
        }

    async def _contractual_identity(_db, *, ref, projection=None):
        _ = projection
        if ref == "EMP-200":
            return {"employee_id": "EMP-200", "employment_type": "CONTRACTUAL"}
        return None

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    app.dependency_overrides[get_service_events_service] = lambda: stub
    app.dependency_overrides[get_db] = lambda: object()
    monkeypatch.setattr(service_events_router_module, "resolve_identity_ref", _contractual_identity)

    async with client as c:
        response = await c.post(
            "/api/service-book/records",
            json={
                "employee_id": "EMP-200",
                "event_type": "GENERIC",
                "part_code": "IV",
                "payload": {"order_no": "X", "order_date": "2026-04-05"},
            },
        )

    assert response.status_code == 403
    detail = response.json()["detail"]
    assert detail["required_employment_type"] == "REGULAR"
    assert "REGULAR employees" in detail["message"]
    assert stub.calls == []


@pytest.mark.asyncio
async def test_record_service_event_accepts_regular_assignment_from_profile_read_model(client, monkeypatch):
    stub = _StubServiceEventsService()

    async def _fake_user(_request=None):
        return {
            "sub": "actor-1",
            "employee_id": "EMP-200",
            "permissions": [],
        }

    class _FakeIdentityCollection:
        async def find_one(self, query, projection=None):
            _ = projection
            if query.get("employee_id") == "EMP-200":
                return {"employee_id": "EMP-200", "employee_code": "CODE-EMP-200"}
            if query.get("employee_code") == "CODE-EMP-200":
                return {"employee_id": "EMP-200", "employee_code": "CODE-EMP-200"}
            return None

    class _FakeProfileReadModels:
        def find(self, query, projection=None):
            _ = projection
            employee_ids = ((query or {}).get("employee_id") or {}).get("$in") or []
            rows = []
            if "EMP-200" in employee_ids:
                rows.append({"employee_id": "EMP-200", "employment_type": "REGULAR"})

            class _Cursor:
                def __init__(self, cursor_rows):
                    self._rows = cursor_rows

                async def to_list(self, length=None):
                    return self._rows[:length] if length else self._rows

            return _Cursor(rows)

    class _FakeDb:
        def __init__(self):
            self.employee_identities = _FakeIdentityCollection()
            self.employee_profile_read_models = _FakeProfileReadModels()
            self.employee_profile_extensions = None

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    app.dependency_overrides[get_service_events_service] = lambda: stub
    app.dependency_overrides[get_db] = lambda: _FakeDb()

    async with client as c:
        response = await c.post(
            "/api/service-book/records",
            json={
                "employee_id": "EMP-200",
                "event_type": "GENERIC",
                "part_code": "IV",
                "payload": {"order_no": "X", "order_date": "2026-04-05"},
            },
        )

    assert response.status_code == 200
    assert stub.calls[0][0] == "record"
    assert stub.calls[0][1].employee_id == "EMP-200"


@pytest.mark.asyncio
async def test_service_records_accept_non_regular_engagement_record(client, monkeypatch):
    stub = _StubServiceEventsService()

    async def _fake_user(_request=None):
        return {
            "sub": "actor-1",
            "employee_id": "EMP-200",
            "permissions": [Permission.SERVICE_BOOK_ENTRY_CREATE.value],
        }

    async def _contractual_identity(_db, *, ref, projection=None):
        _ = projection
        if ref == "EMP-200":
            return {"employee_id": "EMP-200", "employee_status": "ACTIVE"}
        return None

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    app.dependency_overrides[get_service_events_service] = lambda: stub
    app.dependency_overrides[get_db] = lambda: object()
    monkeypatch.setattr(service_events_router_module, "resolve_identity_ref", _contractual_identity)

    async with client as c:
        response = await c.post(
            "/api/service-book/service-records",
            json={
                "employee_id": "EMP-200",
                "record_type": "ENGAGEMENT_RECORDED",
                "record_category": "ENGAGEMENT",
                "effective_date": "2026-05-11",
                "payload": {
                    "employment_type_code": "MUSTER_ROLL",
                    "department_id": "DEPT-PWD",
                    "office_id": "OFFICE-PWD-SIAHA",
                    "designation_id": "DESIG-WORKER",
                    "service_id": "SERVICE-WORKS",
                    "engagement_order_no": "A.12031/1/2026-PWD",
                },
                "document_ids": ["DOC-000201"],
            },
        )

    assert response.status_code == 200
    call_name, command, actor_id = stub.calls[0]
    assert call_name == "record"
    assert command.employee_id == "EMP-200"
    assert command.event_type.value == "ENGAGEMENT_RECORDED"
    assert command.payload["record_category"] == "ENGAGEMENT"
    assert command.payload["document_ids"] == ["DOC-000201"]
    assert actor_id == "actor-1"


@pytest.mark.asyncio
async def test_service_records_post_maps_to_lock_for_projection_posting(client):
    stub = _StubServiceEventsService()

    async def _fake_user(_request=None):
        return {
            "sub": "actor-approver",
            "employee_id": "EMP-100",
            "permissions": [Permission.SERVICE_BOOK_ENTRY_APPROVE.value],
        }

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    app.dependency_overrides[get_service_events_service] = lambda: stub

    async with client as c:
        response = await c.post("/api/service-book/service-records/SR-1/post")

    assert response.status_code == 200
    call_name, command, actor_id = stub.calls[0]
    assert call_name == "lock"
    assert command.service_event_id == "SR-1"
    assert actor_id == "actor-approver"


@pytest.mark.asyncio
async def test_service_records_reject_non_projectable_service_event_types(client, monkeypatch):
    stub = _StubServiceEventsService()

    async def _fake_user(_request=None):
        return {
            "sub": "actor-1",
            "employee_id": "EMP-200",
            "permissions": [Permission.SERVICE_BOOK_ENTRY_CREATE.value],
        }

    async def _identity(_db, *, ref, projection=None):
        _ = projection
        if ref == "EMP-200":
            return {"employee_id": "EMP-200", "employee_status": "ACTIVE"}
        return None

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    app.dependency_overrides[get_service_events_service] = lambda: stub
    app.dependency_overrides[get_db] = lambda: object()
    monkeypatch.setattr(service_events_router_module, "resolve_identity_ref", _identity)

    async with client as c:
        response = await c.post(
            "/api/service-book/service-records",
            json={
                "employee_id": "EMP-200",
                "event_type": "SUSPENSION",
                "payload": {"reason": "Pending enquiry"},
            },
        )

    assert response.status_code == 422
    assert stub.calls == []


@pytest.mark.asyncio
async def test_service_records_queue_endpoint_is_not_available(client):
    async def _fake_user(_request=None):
        return {
            "sub": "actor-reader",
            "employee_id": "EMP-100",
            "permissions": [Permission.SERVICE_BOOK_READ_ALL.value],
        }

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user

    async with client as c:
        response = await c.get("/api/service-book/service-records/queue", params={"workflow_state": "SUBMITTED"})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_service_event_stream_rejects_unresolved_employee_ref(client, monkeypatch):
    stub = _StubServiceEventsService()

    async def _fake_user(_request=None):
        return {
            "sub": "actor-reader",
            "employee_id": "EMP-100",
            "permissions": [Permission.SERVICE_BOOK_READ_ALL.value],
        }

    async def _missing_identity(_db, *, ref, projection=None):
        _ = (ref, projection)
        return None

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    app.dependency_overrides[get_service_events_service] = lambda: stub
    app.dependency_overrides[get_db] = lambda: object()
    monkeypatch.setattr(service_events_router_module, "resolve_identity_ref", _missing_identity)

    async with client as c:
        response = await c.get("/api/service-book/records/employees/DOES-NOT-EXIST")

    assert response.status_code == 404
    assert response.json()["detail"]["error_code"] == "EMPLOYEE_NOT_FOUND"
    assert stub.calls == []


@pytest.mark.asyncio
async def test_get_service_event_stream_rejects_non_regular_employee_ref(client, monkeypatch):
    stub = _StubServiceEventsService()

    async def _fake_user(_request=None):
        return {
            "sub": "actor-reader",
            "employee_id": "EMP-100",
            "permissions": [Permission.SERVICE_BOOK_READ_ALL.value],
        }

    async def _contractual_identity(_db, *, ref, projection=None):
        _ = projection
        if ref == "EMP-200":
            return {"employee_id": "EMP-200", "employment_type": "CONTRACTUAL"}
        return None

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    app.dependency_overrides[get_service_events_service] = lambda: stub
    app.dependency_overrides[get_db] = lambda: object()
    monkeypatch.setattr(service_events_router_module, "resolve_identity_ref", _contractual_identity)

    async with client as c:
        response = await c.get("/api/service-book/records/employees/EMP-200")

    assert response.status_code == 403
    detail = response.json()["detail"]
    assert detail["required_employment_type"] == "REGULAR"
    assert "REGULAR employees" in detail["message"]
    assert stub.calls == []


@pytest.mark.asyncio
async def test_verify_service_event_returns_not_found_for_missing_event(client):
    stub = _StubServiceEventsService()
    stub.verify_error = ValueError("Service event not found")

    async def _fake_user(_request=None):
        return {
            "sub": "actor-verifier",
            "employee_id": "EMP-100",
            "permissions": [Permission.SERVICE_BOOK_ENTRY_VERIFY.value],
        }

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    app.dependency_overrides[get_service_events_service] = lambda: stub

    async with client as c:
        response = await c.post("/api/service-book/records/SE-MISSING/verify")

    assert response.status_code == 404
    assert response.json()["detail"]["error_code"] == "SERVICE_EVENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_verify_service_event_returns_conflict_for_invalid_transition(client):
    stub = _StubServiceEventsService()
    stub.verify_error = DomainError("Invalid transition from DRAFT to VERIFIED")

    async def _fake_user(_request=None):
        return {
            "sub": "actor-verifier",
            "employee_id": "EMP-100",
            "permissions": [Permission.SERVICE_BOOK_ENTRY_VERIFY.value],
        }

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    app.dependency_overrides[get_service_events_service] = lambda: stub

    async with client as c:
        response = await c.post("/api/service-book/records/SE-DRAFT/verify")

    assert response.status_code == 409
    assert response.json()["detail"]["error_code"] == "SERVICE_EVENT_CONFLICT"


@pytest.mark.asyncio
async def test_correct_service_event_uses_path_id_over_payload_id(client):
    stub = _StubServiceEventsService()

    async def _fake_user(_request=None):
        return {
            "sub": "actor-approver",
            "employee_id": "EMP-777",
            "permissions": [Permission.SERVICE_BOOK_ENTRY_APPROVE.value],
        }

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    app.dependency_overrides[get_service_events_service] = lambda: stub

    payload = {
        "service_event_id": "SE-PAYLOAD-SHOULD-NOT-WIN",
        "corrected_payload": {"to_post": "Administrative Officer"},
        "reason": "Typo in source order",
    }

    async with client as c:
        response = await c.patch("/api/service-book/records/SE-PATH-1/correct", json=payload)

    assert response.status_code == 200
    assert len(stub.calls) == 1

    call_name, command, actor_id = stub.calls[0]
    assert call_name == "revise"
    assert command.service_event_id == "SE-PATH-1"
    assert command.corrected_payload["to_post"] == "Administrative Officer"
    assert actor_id == "actor-approver"


@pytest.mark.asyncio
async def test_submit_service_event_requires_submit_permission(client):
    stub = _StubServiceEventsService()

    async def _fake_user(_request=None):
        return {
            "sub": "actor-no-submit",
            "employee_id": "EMP-100",
            "permissions": [Permission.SERVICE_BOOK_ENTRY_CREATE.value],
        }

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    app.dependency_overrides[get_service_events_service] = lambda: stub

    async with client as c:
        response = await c.post("/api/service-book/records/SE-NEEDS-PERM/submit")

    assert response.status_code == 403
    assert response.json()["detail"]["error_code"] == "INSUFFICIENT_PERMISSION"
    assert stub.calls == []


@pytest.mark.asyncio
async def test_attach_service_event_document_uses_path_id_and_create_permission(client):
    stub = _StubServiceEventsService()

    async def _fake_user(_request=None):
        return {
            "sub": "actor-data-entry",
            "employee_id": "EMP-100",
            "permissions": [Permission.SERVICE_BOOK_ENTRY_CREATE.value],
        }

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    app.dependency_overrides[get_service_events_service] = lambda: stub

    payload = {
        "service_event_id": "SE-PAYLOAD-SHOULD-NOT-WIN",
        "document_id": "DOC-EXISTING-1",
        "document_type": "order",
    }

    async with client as c:
        response = await c.post("/api/service-book/records/SE-PATH-ATTACH-1/documents", json=payload)

    assert response.status_code == 200
    assert response.json()["service_event_id"] == "SE-PATH-ATTACH-1"
    assert response.json()["document_id"] == "DOC-EXISTING-1"
    assert len(stub.calls) == 1

    call_name, command, actor_id = stub.calls[0]
    assert call_name == "attach_document"
    assert command.service_event_id == "SE-PATH-ATTACH-1"
    assert command.document_id == "DOC-EXISTING-1"
    assert command.document_type == "order"
    assert actor_id == "actor-data-entry"


@pytest.mark.asyncio
async def test_attach_service_event_document_requires_attach_permission(client):
    stub = _StubServiceEventsService()

    async def _fake_user(_request=None):
        return {
            "sub": "actor-no-attach",
            "employee_id": "EMP-100",
            "permissions": [],
        }

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    app.dependency_overrides[get_service_events_service] = lambda: stub

    async with client as c:
        response = await c.post(
            "/api/service-book/records/SE-NEEDS-ATTACH-PERM/documents",
            json={
                "service_event_id": "SE-IGNORED",
                "document_id": "DOC-EXISTING-2",
            },
        )

    assert response.status_code == 403
    assert response.json()["detail"]["error_code"] == "INSUFFICIENT_PERMISSION"
    assert stub.calls == []


@pytest.mark.asyncio
async def test_record_service_event_validates_required_request_fields(client):
    stub = _StubServiceEventsService()

    async def _fake_user(_request=None):
        return {"sub": "actor-1", "employee_id": "EMP-100", "permissions": []}

    app.dependency_overrides[shared_auth_module.get_current_user] = _fake_user
    app.dependency_overrides[get_service_events_service] = lambda: stub
    app.dependency_overrides[get_db] = lambda: object()

    async with client as c:
        response = await c.post(
            "/api/service-book/records",
            json={
                "event_type": "SUSPENSION",
                "part_code": "IV",
                "payload": {"reason": "Pending enquiry"},
            },
        )

    assert response.status_code == 422
    assert stub.calls == []


@pytest.mark.asyncio
async def test_service_events_schema_endpoint_requires_read_permission_and_returns_contract(client):
    async def _forbidden_user(_request=None):
        return {"sub": "actor-1", "employee_id": "EMP-100", "permissions": []}

    app.dependency_overrides[shared_auth_module.get_current_user] = _forbidden_user
    async with client as c:
        forbidden = await c.get("/api/service-book/records/schema")

        assert forbidden.status_code == 403

        async def _allowed_user(_request=None):
            return {
                "sub": "actor-2",
                "employee_id": "EMP-100",
                "permissions": [Permission.SERVICE_BOOK_READ_ALL.value],
            }

        app.dependency_overrides[shared_auth_module.get_current_user] = _allowed_user
        response = await c.get("/api/service-book/records/schema")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data.get("canonical_category_options"), list)
        assert isinstance(data.get("category_to_part_code"), dict)
        assert isinstance(data.get("required_payload_keys_by_category"), dict)
        assert isinstance(data.get("field_definitions"), dict)
        assert set(data["category_to_part_code"].values()) == {"IV"}
        assert any(option.get("value") == "CUSTOM" for option in data["canonical_category_options"])
        assert all(option.get("value") != "CONFIRMATION" for option in data["canonical_category_options"])
        assert all(option.get("value") != "GENERIC" for option in data["canonical_category_options"])
        assert data["required_payload_keys_by_category"]["APPOINTMENT"] == [
            "appointment_order_no",
            "appointment_order_date",
            "post_name",
            "office_name",
            "service_group",
        ]
        assert data["required_payload_keys_by_category"]["PROMOTION"] == [
            "promotion_date",
            "to_post",
            "promotion_type",
        ]
        assert data["field_definitions"]["service"]["label"] == "Service"
        assert data["field_definitions"]["service_group"]["label"] == "Service Group"
        assert data["field_definitions"]["grade"]["label"] == "Grade"
        assert data["field_definitions"]["to_service"]["label"] == "To Service"
        assert data["field_definitions"]["to_service_group"]["label"] == "To Service Group"
        assert data["field_definitions"]["to_grade"]["label"] == "To Grade"
        assert data["cpc_payload_keys_by_category"]["6TH_CPC"]["FINANCIAL_UPGRADATION"] == [
            "from_pay_band",
            "from_grade_pay",
            "to_pay_band",
            "to_grade_pay",
            "from_basic_pay",
            "to_basic_pay",
        ]
        assert data["cpc_payload_keys_by_category"]["7TH_CPC"]["FINANCIAL_UPGRADATION"] == [
            "from_pay_level",
            "to_pay_level",
            "from_basic_pay",
            "to_basic_pay",
        ]
