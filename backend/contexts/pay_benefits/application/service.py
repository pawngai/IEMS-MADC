from __future__ import annotations

from app_platform.event_bus.types import EventName
from app_platform.db.atomic import call_with_optional_session, run_atomic
from app_platform.outbox.model import OutboxEvent
from app_platform.outbox.repo import OutboxRepository
from contexts.pay_benefits.contracts.dto import AllowanceChangeCreateDTO, PayRevisionCreateDTO
from contexts.pay_benefits.contracts.ports import PayGateway


class PayApplicationService:
    def __init__(self, *, gateway: PayGateway, outbox_repo: OutboxRepository | None) -> None:
        self._gateway = gateway
        self._outbox_repo = outbox_repo

    async def _enqueue_event(
        self,
        *,
        name: str,
        payload: dict,
        actor_id: str | None,
        department_id: str | None,
        session=None,
    ) -> None:
        if self._outbox_repo is None:
            return
        await call_with_optional_session(
            self._outbox_repo.add_event,
            OutboxEvent(
                name=name,
                payload=payload,
                actor_id=actor_id,
                department_id=department_id,
            ),
            session=session,
        )

    async def revise_pay(self, payload: PayRevisionCreateDTO, *, current_user: dict) -> dict:
        async def _operation(session):
            result = await call_with_optional_session(
                self._gateway.revise_pay,
                payload,
                current_user=current_user,
                session=session,
            )
            await self._enqueue_event(
                name=EventName.PAY_REVISED.value,
                payload={
                    "entry_id": result.get("entry_id"),
                    "employee_id": result.get("employee_id"),
                    "part_code": "VII",
                    "effective_date": result.get("payload", {}).get("effective_date"),
                    "basic_pay": result.get("payload", {}).get("basic_pay"),
                    "pay_level": result.get("payload", {}).get("pay_level"),
                    "remarks": result.get("payload", {}).get("remarks"),
                },
                actor_id=current_user.get("sub"),
                department_id=current_user.get("department_code"),
                session=session,
            )
            return result

        return await run_atomic(getattr(self._gateway, "_db", None), _operation)

    async def change_allowance(
        self, payload: AllowanceChangeCreateDTO, *, current_user: dict
    ) -> dict:
        async def _operation(session):
            result = await call_with_optional_session(
                self._gateway.change_allowance,
                payload,
                current_user=current_user,
                session=session,
            )
            entry_payload = result.get("payload") or {}
            await self._enqueue_event(
                name=EventName.ALLOWANCE_CHANGED.value,
                payload={
                    "entry_id": result.get("entry_id"),
                    "employee_id": result.get("employee_id"),
                    "part_code": "VII",
                    "effective_date": entry_payload.get("effective_date"),
                    "allowance_code": entry_payload.get("allowance_code"),
                    "amount": entry_payload.get("amount"),
                    "operation": entry_payload.get("operation"),
                    "remarks": entry_payload.get("remarks"),
                },
                actor_id=current_user.get("sub"),
                department_id=current_user.get("department_code"),
                session=session,
            )
            return result

        return await run_atomic(getattr(self._gateway, "_db", None), _operation)

    async def list_ledger_entries(self, employee_id: str, *, current_user: dict) -> list[dict]:
        return await self._gateway.list_ledger_entries(employee_id, current_user=current_user)

    async def get_pay_snapshot(self, employee_id: str, *, current_user: dict) -> dict:
        return await self._gateway.get_pay_snapshot(employee_id, current_user=current_user)
