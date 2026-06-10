from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.change_requests.application.service import ChangeRequestApplicationService
from contexts.change_requests.contracts.dto import CreateChangeRequestDTO
from contexts.change_requests.infrastructure.gateway import ChangeRequestMongoGateway


def _build_service(db) -> ChangeRequestApplicationService:
    return ChangeRequestApplicationService(
        gateway=ChangeRequestMongoGateway(db),
        outbox_repo=None,
    )


@pytest.mark.asyncio
async def test_change_request_service_create_routes_via_gateway(monkeypatch):
    called = {"ok": False}

    class _FakeGateway:
        async def create_change_request(self, payload, *, current_user: dict):
            called["ok"] = True
            return {
                "request_id": "CR-TEST-1",
                "employee_id": current_user.get("employee_id"),
                "status": "PENDING",
                "request_type": payload.request_type,
                "category": payload.category,
            }

        async def list_my_change_requests(self, *, current_user: dict, status: str | None = None):
            return {"items": [], "total": 0}

        async def get_change_request(self, request_id: str, *, current_user: dict):
            return {"request_id": request_id}

        async def cancel_change_request(self, request_id: str, *, current_user: dict):
            return {"request_id": request_id, "status": "CANCELLED"}

        async def list_change_requests(self, *, current_user: dict, status: str | None = None, employee_id: str | None = None, page: int = 1, page_size: int = 20):
            return {"items": [], "total": 0, "page": page, "page_size": page_size}

        async def review_change_request(self, request_id: str, *, action: str, remarks: str | None, current_user: dict):
            return {"request_id": request_id, "status": "APPLIED"}

        async def get_pending_count(self, *, current_user: dict):
            return 0

    service = ChangeRequestApplicationService(gateway=_FakeGateway(), outbox_repo=None)

    result = await service.create_change_request(
        CreateChangeRequestDTO.model_validate({
            "request_type": "PROFILE",
            "category": "BASIC",
            "fields": [{"field_name": "mobile_primary", "requested_value": "9999999999"}],
            "reason": "profile update request",
        }),
        current_user={"employee_id": "EMP-1", "sub": "u-1"},
    )

    assert called["ok"] is True
    assert result["request_id"] == "CR-TEST-1"


@pytest.mark.asyncio
async def test_change_request_service_review_routes_via_gateway(monkeypatch):
    called = {"ok": False}

    class _FakeGateway:
        async def create_change_request(self, payload, *, current_user: dict):
            return {
                "request_id": "CR-TEST-2",
                "employee_id": current_user.get("employee_id"),
                "status": "PENDING",
                "request_type": payload.request_type,
                "category": payload.category,
            }

        async def list_my_change_requests(self, *, current_user: dict, status: str | None = None):
            return {"items": [], "total": 0}

        async def get_change_request(self, request_id: str, *, current_user: dict):
            return {"request_id": request_id}

        async def cancel_change_request(self, request_id: str, *, current_user: dict):
            return {"request_id": request_id, "status": "CANCELLED"}

        async def list_change_requests(self, *, current_user: dict, status: str | None = None, employee_id: str | None = None, page: int = 1, page_size: int = 20):
            return {"items": [], "total": 0, "page": page, "page_size": page_size}

        async def review_change_request(self, request_id: str, *, action: str, remarks: str | None, current_user: dict):
            called["ok"] = True
            return {
                "request_id": request_id,
                "status": "REJECTED" if action == "REJECT" else "APPLIED",
                "employee_id": "EMP-1",
                "request_type": "PROFILE",
                "category": "BASIC",
            }

        async def get_pending_count(self, *, current_user: dict):
            return 0

    service = ChangeRequestApplicationService(gateway=_FakeGateway(), outbox_repo=None)

    result = await service.review_change_request(
        request_id="CR-1",
        action="REJECT",
        remarks="bad",
        current_user={"sub": "admin"},
    )

    assert called["ok"] is True
    assert result["status"] == "REJECTED"
