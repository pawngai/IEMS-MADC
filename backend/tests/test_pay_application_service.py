from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.pay_benefits.application.service import PayApplicationService
from contexts.pay_benefits.contracts.dto import AllowanceChangeCreateDTO, PayRevisionCreateDTO
from contexts.pay_benefits.domain.model import build_pay_snapshot


class _FakeOutboxRepo:
    def __init__(self) -> None:
        self.events = []

    async def add_event(self, event) -> None:
        self.events.append(event)


class _FakeGateway:
    async def revise_pay(self, payload: PayRevisionCreateDTO, *, current_user: dict) -> dict:
        return {
            "entry_id": "ENTRY-1",
            "employee_id": payload.employee_id,
            "event_code": "PAY_REVISED",
            "amount": payload.basic_pay,
            "payload": {
                "effective_date": payload.effective_date,
                "basic_pay": payload.basic_pay,
                "pay_level": payload.pay_level,
                "remarks": payload.remarks,
            },
            "created_at": "2026-03-01T00:00:00+00:00",
            "created_by": current_user.get("sub"),
        }

    async def change_allowance(
        self, payload: AllowanceChangeCreateDTO, *, current_user: dict
    ) -> dict:
        return {
            "entry_id": "ENTRY-2",
            "employee_id": payload.employee_id,
            "event_code": "ALLOWANCE_CHANGED",
            "amount": payload.amount,
            "payload": {
                "effective_date": payload.effective_date,
                "allowance_code": payload.allowance_code,
                "amount": payload.amount,
                "operation": payload.operation.value,
                "remarks": payload.remarks,
            },
            "created_at": "2026-03-02T00:00:00+00:00",
            "created_by": current_user.get("sub"),
        }

    async def list_ledger_entries(self, employee_id: str, *, current_user: dict) -> list[dict]:
        return []

    async def get_pay_snapshot(self, employee_id: str, *, current_user: dict) -> dict:
        return {
            "employee_id": employee_id,
            "basic_pay": None,
            "pay_level": None,
            "effective_date": None,
            "allowances": {},
        }


@pytest.mark.asyncio
async def test_revise_pay_enqueues_pay_revised_event() -> None:
    outbox = _FakeOutboxRepo()
    service = PayApplicationService(gateway=_FakeGateway(), outbox_repo=outbox)

    result = await service.revise_pay(
        PayRevisionCreateDTO(
            employee_id="EMP-1",
            effective_date="2026-03-01",
            basic_pay=79000,
            pay_level="L10",
            remarks="Annual increment",
        ),
        current_user={"sub": "U-1", "department_code": "FIN"},
    )

    assert result["event_code"] == "PAY_REVISED"
    assert len(outbox.events) == 1
    assert outbox.events[0].name == "PayRevised"
    assert outbox.events[0].payload["part_code"] == "VII"
    assert outbox.events[0].payload["employee_id"] == "EMP-1"


def test_build_pay_snapshot_uses_latest_entries() -> None:
    entries = [
        {
            "event_code": "ALLOWANCE_CHANGED",
            "amount": 5000,
            "payload": {"allowance_code": "DA", "amount": 5000},
        },
        {
            "event_code": "PAY_REVISED",
            "amount": 65000,
            "payload": {
                "basic_pay": 65000,
                "pay_level": "L9",
                "effective_date": "2026-01-01",
            },
        },
        {
            "event_code": "ALLOWANCE_CHANGED",
            "amount": 3000,
            "payload": {"allowance_code": "HRA", "amount": 3000},
        },
    ]

    snapshot = build_pay_snapshot("EMP-2", entries)

    assert snapshot["employee_id"] == "EMP-2"
    assert snapshot["basic_pay"] == 65000
    assert snapshot["pay_level"] == "L9"
    assert snapshot["allowances"]["DA"] == 5000
    assert snapshot["allowances"]["HRA"] == 3000
