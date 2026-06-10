from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.leave.application.service import LeaveApplicationService
from contexts.leave.contracts.dto import LeaveApplicationCreateDTO


class _FakeGateway:
    async def get_leave_balances(self, employee_id: str, *, current_user: dict):
        return {"employee_id": employee_id}

    async def apply_leave(self, payload, *, current_user: dict):
        return {
            "id": "LV-1",
            "employee_id": current_user.get("employee_id"),
            "leave_type_code": payload.leave_type_code,
            "status": "SUBMITTED",
        }

    async def list_my_leaves(self, *, current_user: dict):
        return []

    async def list_leaves(self, *, status, leave_type_code, employee_id, current_user: dict):
        return [
            {
                "id": "LV-22",
                "employee_id": employee_id,
                "status": status or "PENDING",
                "leave_type_code": leave_type_code or "CL",
            }
        ]

    async def recommend_leave(self, leave_id: str, action, *, current_user: dict):
        return {"id": leave_id}

    async def sanction_leave(self, leave_id: str, action, *, current_user: dict):
        return {"id": leave_id}

    async def reject_leave(self, leave_id: str, action, *, current_user: dict):
        return {"id": leave_id}

    async def cancel_leave(self, leave_id: str, action, *, current_user: dict):
        return {"id": leave_id, "status": "CANCELLED"}


@pytest.mark.asyncio
async def test_leave_service_apply_routes_via_gateway():
    service = LeaveApplicationService(gateway=_FakeGateway(), outbox_repo=None, leave_rules_evaluator=None)

    result = await service.apply_leave(
        LeaveApplicationCreateDTO.model_validate({
            "leave_type_code": "CL",
            "from_date": "2026-03-01",
            "to_date": "2026-03-02",
            "reason": "medical emergency",
            "contact_during_leave": "9999999999",
        }),
        current_user={"employee_id": "EMP-1", "sub": "u-1"},
    )

    assert result["id"] == "LV-1"


@pytest.mark.asyncio
async def test_leave_service_list_leaves_routes_via_gateway():
    service = LeaveApplicationService(gateway=_FakeGateway(), outbox_repo=None, leave_rules_evaluator=None)

    result = await service.list_leaves(
        status="PENDING",
        leave_type_code="CL",
        employee_id="EMP-9",
        current_user={
            "authorities": ["HOD"],
            "permissions": ["LEAVE_RECOMMEND"],
            "department_code": "FIN",
        },
    )

    assert result[0]["id"] == "LV-22"
