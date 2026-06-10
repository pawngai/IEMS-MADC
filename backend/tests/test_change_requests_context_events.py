from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app_platform.event_bus.types import EventName
from contexts.change_requests.application.service import ChangeRequestApplicationService


class _FakeGateway:
    async def create_change_request(self, payload, *, current_user):
        return {
            "request_id": "CR-100",
            "employee_id": current_user.get("employee_id"),
            "status": "PENDING",
            "request_type": payload.request_type.value,
            "category": payload.category,
        }

    async def list_my_change_requests(self, *, current_user, status=None):
        return {"items": [], "total": 0}

    async def get_change_request(self, request_id, *, current_user):
        return {"request_id": request_id, "employee_id": current_user.get("employee_id")}

    async def cancel_change_request(self, request_id, *, current_user):
        return {"request_id": request_id, "employee_id": current_user.get("employee_id"), "status": "CANCELLED"}

    async def list_change_requests(self, *, current_user, status=None, employee_id=None, page=1, page_size=20):
        return {"items": [], "total": 0, "page": page, "page_size": page_size}

    async def review_change_request(self, request_id, *, action, remarks, current_user):
        status = "APPLIED" if action == "APPROVE" else "REJECTED"
        return {
            "request_id": request_id,
            "employee_id": "EMP-200",
            "status": status,
            "request_type": "PROFILE",
            "category": "CONTACT",
        }

    async def get_pending_count(self, *, current_user):
        return 0


class _FakeOutboxRepo:
    def __init__(self) -> None:
        self.events: list[dict] = []

    async def add_event(self, event):
        self.events.append(event.to_document())


@pytest.mark.asyncio
async def test_submit_emits_change_request_submitted(create_change_request_payload):
    repo = _FakeOutboxRepo()
    service = ChangeRequestApplicationService(gateway=_FakeGateway(), outbox_repo=repo)

    current_user = {"sub": "user-1", "employee_id": "EMP-1", "department_code": "FIN"}
    await service.create_change_request(create_change_request_payload, current_user=current_user)

    assert len(repo.events) == 1
    assert repo.events[0]["name"] == EventName.CHANGE_REQUEST_SUBMITTED.value
    assert repo.events[0]["payload"]["request_id"] == "CR-100"


@pytest.mark.asyncio
async def test_review_approve_emits_applied_event():
    repo = _FakeOutboxRepo()
    service = ChangeRequestApplicationService(gateway=_FakeGateway(), outbox_repo=repo)

    current_user = {"sub": "admin-1", "department_code": "FIN"}
    await service.review_change_request("CR-201", action="APPROVE", remarks="ok", current_user=current_user)

    assert len(repo.events) == 1
    assert repo.events[0]["name"] == EventName.CHANGE_REQUEST_APPLIED.value
    assert repo.events[0]["payload"]["request_id"] == "CR-201"


@pytest.mark.asyncio
async def test_review_reject_emits_rejected_event():
    repo = _FakeOutboxRepo()
    service = ChangeRequestApplicationService(gateway=_FakeGateway(), outbox_repo=repo)

    current_user = {"sub": "admin-2", "department_code": "FIN"}
    await service.review_change_request("CR-202", action="REJECT", remarks="no", current_user=current_user)

    assert len(repo.events) == 1
    assert repo.events[0]["name"] == EventName.CHANGE_REQUEST_REJECTED.value


@pytest.mark.asyncio
async def test_cancel_emits_cancelled_event():
    repo = _FakeOutboxRepo()
    service = ChangeRequestApplicationService(gateway=_FakeGateway(), outbox_repo=repo)

    current_user = {"sub": "user-2", "employee_id": "EMP-2", "department_code": "HR"}
    await service.cancel_change_request("CR-203", current_user=current_user)

    assert len(repo.events) == 1
    assert repo.events[0]["name"] == EventName.CHANGE_REQUEST_CANCELLED.value


@pytest.fixture
def create_change_request_payload():
    from contexts.change_requests.contracts.dto import CreateChangeRequestDTO

    return CreateChangeRequestDTO(
        request_type="PROFILE",
        category="CONTACT",
        fields=[
            {
                "field_name": "mobile_primary",
                "current_value": "1111111111",
                "requested_value": "9999999999",
            }
        ],
        reason="Need to update contact number",
    )
