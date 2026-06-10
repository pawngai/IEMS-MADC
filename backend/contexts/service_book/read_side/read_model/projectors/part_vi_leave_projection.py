from __future__ import annotations

from contexts.leave.contracts.leave_directory import get_leave_ledger_entry
from contexts.service_book.read_side.application.part_vi_projection import (
    PART_VI_CODE,
    merge_part_vi_entries,
    merge_part_vi_projection_list,
    resolve_part_vi_projection,
)


class LeaveLedgerPartVIProjectionSource:
    async def merge_entries(
        self,
        *,
        db,
        entries: list[dict],
        employee_id: str,
        part_code: str | None,
    ) -> list[dict]:
        if part_code not in {None, PART_VI_CODE}:
            return entries
        leave_ledger_entry = await get_leave_ledger_entry(db, employee_id=employee_id)
        return merge_part_vi_entries(
            entries=entries,
            employee_id=employee_id,
            leave_ledger_entry=leave_ledger_entry,
        )

    async def merge_parts(self, *, db, parts: list[dict], employee_id: str) -> list[dict]:
        leave_ledger_entry = await get_leave_ledger_entry(db, employee_id=employee_id)
        return merge_part_vi_projection_list(
            parts=parts,
            employee_id=employee_id,
            leave_ledger_entry=leave_ledger_entry,
        )

    async def resolve_part(
        self,
        *,
        db,
        existing_projection: dict | None,
        employee_id: str,
        part_code: str,
    ) -> dict | None:
        if part_code != PART_VI_CODE:
            return existing_projection
        leave_ledger_entry = await get_leave_ledger_entry(db, employee_id=employee_id)
        return resolve_part_vi_projection(
            existing_projection=existing_projection,
            employee_id=employee_id,
            leave_ledger_entry=leave_ledger_entry,
        )
