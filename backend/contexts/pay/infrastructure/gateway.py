from __future__ import annotations

from contexts.employee_master.contracts.profile_directory import require_profile_view
from contexts.pay.contracts.dto import AllowanceChangeCreateDTO, PayRevisionCreateDTO
from contexts.pay.domain.model import build_pay_snapshot
from contexts.pay.infrastructure.pay_repository import PayLedgerRepository


class PayMongoGateway:
    def __init__(self, *, db) -> None:
        self._db = db
        self._repo = PayLedgerRepository(db=db)

    async def _ensure_employee_profile_exists(self, employee_id: str) -> None:
        await require_profile_view(
            self._db,
            employee_id=employee_id,
            projection={"_id": 0, "employee_id": 1},
        )

    async def revise_pay(self, payload: PayRevisionCreateDTO, *, current_user: dict, session=None) -> dict:
        await self._ensure_employee_profile_exists(payload.employee_id)
        entry_payload = {
            "part_code": "VII",
            "effective_date": payload.effective_date,
            "basic_pay": float(payload.basic_pay),
            "pay_level": payload.pay_level,
            "remarks": payload.remarks,
            "metadata": payload.metadata,
        }
        entry_id = await self._repo.append_entry(
            employee_id=payload.employee_id,
            event_code="PAY_REVISED",
            amount=float(payload.basic_pay),
            payload=entry_payload,
            actor_id=current_user.get("sub"),
            session=session,
        )
        return {
            "entry_id": entry_id,
            "employee_id": payload.employee_id,
            "event_code": "PAY_REVISED",
            "amount": float(payload.basic_pay),
            "payload": entry_payload,
            "created_by": current_user.get("sub"),
        }

    async def change_allowance(
        self, payload: AllowanceChangeCreateDTO, *, current_user: dict, session=None
    ) -> dict:
        await self._ensure_employee_profile_exists(payload.employee_id)
        entry_payload = {
            "part_code": "VII",
            "effective_date": payload.effective_date,
            "allowance_code": payload.allowance_code.strip().upper(),
            "amount": float(payload.amount),
            "operation": payload.operation.value,
            "remarks": payload.remarks,
            "metadata": payload.metadata,
        }
        entry_id = await self._repo.append_entry(
            employee_id=payload.employee_id,
            event_code="ALLOWANCE_CHANGED",
            amount=float(payload.amount),
            payload=entry_payload,
            actor_id=current_user.get("sub"),
            session=session,
        )
        return {
            "entry_id": entry_id,
            "employee_id": payload.employee_id,
            "event_code": "ALLOWANCE_CHANGED",
            "amount": float(payload.amount),
            "payload": entry_payload,
            "created_by": current_user.get("sub"),
        }

    async def list_ledger_entries(self, employee_id: str, *, current_user: dict) -> list[dict]:
        await self._ensure_employee_profile_exists(employee_id)
        return await self._repo.list_entries(employee_id=employee_id, limit=500)

    async def get_pay_snapshot(self, employee_id: str, *, current_user: dict) -> dict:
        await self._ensure_employee_profile_exists(employee_id)
        entries = await self._repo.list_entries(employee_id=employee_id, limit=1000)
        return build_pay_snapshot(employee_id, entries)
