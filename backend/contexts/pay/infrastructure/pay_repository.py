from __future__ import annotations

from app_platform.domain_separation.data_ownership import assert_collection_ownership
from shared_kernel.ids import new_id
from shared_kernel.events import utc_now_iso


class PayLedgerRepository:
    def __init__(self, *, db) -> None:
        assert_collection_ownership(
            context="pay",
            collection_name="pay_ledger_entries",
            write=True,
        )
        self._db = db

    async def append_entry(
        self,
        *,
        employee_id: str,
        event_code: str,
        amount: float,
        payload: dict,
        actor_id: str | None,
        session=None,
    ) -> str:
        entry_id = new_id()
        document = {
            "entry_id": entry_id,
            "employee_id": employee_id,
            "event_code": event_code,
            "amount": amount,
            "payload": payload or {},
            "created_at": utc_now_iso(),
            "created_by": actor_id,
        }
        if session is None:
            await self._db.pay_ledger_entries.insert_one(document)
        else:
            await self._db.pay_ledger_entries.insert_one(document, session=session)
        return entry_id

    async def list_entries(self, *, employee_id: str, limit: int = 200) -> list[dict]:
        return (
            await self._db.pay_ledger_entries.find(
                {"employee_id": employee_id},
                {"_id": 0},
            )
            .sort("created_at", -1)
            .to_list(length=limit)
        )
