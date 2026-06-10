from __future__ import annotations

from copy import deepcopy
from typing import Any


PART_VI_CODE = "SB_PART_VI"
PART_VI_OPENING_SCHEMA = "SB_VI_LEAVE_OPENING_BALANCE"
PART_VI_TRANSACTION_SCHEMA = "SB_VI_LEAVE_TRANSACTION_ROW"
PART_VI_STATUS = "LOCKED"
PART_VI_SCHEMA_KEYS = {PART_VI_OPENING_SCHEMA, PART_VI_TRANSACTION_SCHEMA}
PART_VI_ALLOWED_LEAVE_TYPES = {"EL", "HPL", "CML", "LND"}


def _to_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _part_code_for(entry: dict[str, Any]) -> str:
    return str(entry.get("part_code") or entry.get("part_key") or "").strip().upper()


def _is_part_vi_entry(entry: dict[str, Any]) -> bool:
    return _part_code_for(entry) in {"VI", PART_VI_CODE} or str(
        entry.get("schema_key") or ""
    ).strip().upper() in PART_VI_SCHEMA_KEYS


def _sort_key(entry: dict[str, Any]) -> str:
    return str(
        entry.get("created_at")
        or entry.get("updated_at")
        or entry.get("effective_date")
        or entry.get("payload", {}).get("transaction_date")
        or ""
    )


def build_part_vi_projection(
    *, employee_id: str, leave_ledger_entry: dict[str, Any] | None
) -> dict[str, Any] | None:
    if not leave_ledger_entry:
        return None

    return {
        "employee_id": employee_id,
        "part_code": PART_VI_CODE,
        "earned_leave_balance": _to_float(
            leave_ledger_entry.get("earned_leave_balance")
        ),
        "half_pay_leave_balance": _to_float(
            leave_ledger_entry.get("half_pay_leave_balance")
        ),
        "commuted_leave_balance": _to_float(
            leave_ledger_entry.get("commuted_leave_balance")
        ),
        "leave_not_due_balance": _to_float(
            leave_ledger_entry.get("leave_not_due_balance")
        ),
        "updated_at": leave_ledger_entry.get("last_updated_at")
        or leave_ledger_entry.get("created_at"),
        "source": "LEAVE_LEDGER",
    }


def build_part_vi_entries(
    *, employee_id: str, leave_ledger_entry: dict[str, Any] | None
) -> list[dict[str, Any]]:
    if not leave_ledger_entry:
        return []

    ledger_id = str(leave_ledger_entry.get("id") or employee_id)
    opening_created_at = leave_ledger_entry.get("created_at") or leave_ledger_entry.get(
        "last_updated_at"
    )
    entries = [
        {
            "id": f"{ledger_id}:opening",
            "entry_id": f"{ledger_id}:opening",
            "employee_id": employee_id,
            "part_code": PART_VI_CODE,
            "schema_key": PART_VI_OPENING_SCHEMA,
            "status": PART_VI_STATUS,
            "workflow_state": PART_VI_STATUS,
            "created_at": opening_created_at,
            "payload": {
                "earned_leave_balance": _to_float(
                    leave_ledger_entry.get("earned_leave_balance")
                ),
                "half_pay_leave_balance": _to_float(
                    leave_ledger_entry.get("half_pay_leave_balance")
                ),
                "commuted_leave_balance": _to_float(
                    leave_ledger_entry.get("commuted_leave_balance")
                ),
                "leave_not_due_balance": _to_float(
                    leave_ledger_entry.get("leave_not_due_balance")
                ),
            },
        }
    ]

    for index, transaction in enumerate(leave_ledger_entry.get("transactions") or []):
        payload = deepcopy(transaction)
        leave_type = str(payload.get("leave_type") or "").strip().upper()
        if leave_type not in PART_VI_ALLOWED_LEAVE_TYPES:
            continue
        entry_id = str(payload.get("id") or f"{ledger_id}:txn:{index}")
        entries.append(
            {
                "id": entry_id,
                "entry_id": entry_id,
                "employee_id": employee_id,
                "part_code": PART_VI_CODE,
                "schema_key": PART_VI_TRANSACTION_SCHEMA,
                "status": PART_VI_STATUS,
                "workflow_state": PART_VI_STATUS,
                "created_at": payload.get("recorded_at")
                or payload.get("transaction_date")
                or leave_ledger_entry.get("last_updated_at")
                or opening_created_at,
                "payload": payload,
            }
        )

    return entries


def merge_part_vi_projection_list(
    *,
    parts: list[dict[str, Any]],
    employee_id: str,
    leave_ledger_entry: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    filtered = [part for part in parts if _part_code_for(part) != PART_VI_CODE]
    projection = build_part_vi_projection(
        employee_id=employee_id,
        leave_ledger_entry=leave_ledger_entry,
    )
    if projection:
        filtered.append(projection)
    return filtered


def resolve_part_vi_projection(
    *,
    existing_projection: dict[str, Any] | None,
    employee_id: str,
    leave_ledger_entry: dict[str, Any] | None,
) -> dict[str, Any] | None:
    projection = build_part_vi_projection(
        employee_id=employee_id,
        leave_ledger_entry=leave_ledger_entry,
    )
    return projection or existing_projection


def merge_part_vi_entries(
    *,
    entries: list[dict[str, Any]],
    employee_id: str,
    leave_ledger_entry: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    filtered = [entry for entry in entries if not _is_part_vi_entry(entry)]
    filtered.extend(
        build_part_vi_entries(
            employee_id=employee_id,
            leave_ledger_entry=leave_ledger_entry,
        )
    )
    return sorted(filtered, key=_sort_key, reverse=True)