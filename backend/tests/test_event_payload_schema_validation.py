from __future__ import annotations

import pytest

import app_platform.contracts.events  # noqa: F401
from app_platform.contracts.registry import ContractValidationError, validate_event_payload
from app_platform.outbox.model import OutboxEvent
from app_platform.outbox.repo import OutboxRepository


class _FakeCollection:
    async def update_one(self, *_args, **_kwargs):
        return None


class _FakeDb:
    outbox_events = _FakeCollection()


def test_employee_created_payload_must_match_schema() -> None:
    payload = {
        "name": "Alice",
        "created_at": "2026-03-03T00:00:00Z",
    }
    with pytest.raises(ContractValidationError):
        validate_event_payload(name="EmployeeCreated", version="v1", payload=payload)


@pytest.mark.asyncio
async def test_outbox_add_event_fails_for_invalid_payload() -> None:
    repo = OutboxRepository(_FakeDb())
    with pytest.raises(ContractValidationError):
        await repo.add_event(
            OutboxEvent(
                name="EmployeeCreated",
                payload={"name": "Alice", "created_at": "2026-03-03T00:00:00Z"},
            )
        )
