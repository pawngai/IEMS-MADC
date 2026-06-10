"""Leave domain accounting — ledger transaction building (pure, no DB)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


BALANCE_FIELD_BY_LEAVE_TYPE = {
    "EL": "earned_leave_balance",
    "HPL": "half_pay_leave_balance",
    "CML": "commuted_leave_balance",
    "LND": "leave_not_due_balance",
    "CL": "casual_leave_balance",
}


def build_debit_transaction(
    *,
    leave_type_code: str,
    from_date: str,
    to_date: str,
    days: float,
    opening_balance: float,
    user_id: str,
    days_debited: float | None = None,
    debit_source_leave_type: str | None = None,
    order_number: str | None = None,
    order_date: str | None = None,
    remarks: str | None = None,
) -> tuple[dict[str, Any], float]:
    """Build a ledger debit transaction dict and compute the closing balance.

    Returns (transaction_dict, closing_balance).
    Raises ValueError when the resulting balance would be negative.
    """
    closing_balance = opening_balance - days
    if leave_type_code in BALANCE_FIELD_BY_LEAVE_TYPE and closing_balance < -0.001:
        raise ValueError("Insufficient leave balance at sanction time")

    now = datetime.now(timezone.utc).isoformat()
    transaction = {
        "id": str(uuid.uuid4()),
        "transaction_date": now.split("T")[0],
        "transaction_type": "DEBIT",
        "leave_type": leave_type_code,
        "leave_from": from_date,
        "leave_to": to_date,
        "days_availed": days,
        "leave_order_number": order_number,
        "leave_order_date": order_date,
        "opening_balance": opening_balance,
        "closing_balance": closing_balance,
        "days_debited": float(days if days_debited is None else days_debited),
        "debit_source_leave_type": debit_source_leave_type,
        "remarks": remarks,
        "recorded_by": user_id,
    }
    return transaction, closing_balance


def opening_balance_for(account: dict[str, Any] | None, leave_type_code: str) -> float:
    """Extract the current balance for *leave_type_code* from a ledger account."""
    if not account:
        return 0.0
    balance_field = BALANCE_FIELD_BY_LEAVE_TYPE.get(leave_type_code)
    if balance_field:
        return float(account.get(balance_field, 0))
    return 0.0


def build_account_update(
    transaction: dict[str, Any],
    from_date: str,
    summary_leave_type: str,
    balance_updates: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Build the MongoDB update document for the ledger account."""
    now = datetime.now(timezone.utc).isoformat()
    update_fields: dict[str, Any] = {
        "$push": {"transactions": transaction},
        "$set": {"last_updated_at": now},
    }

    for balance_field, balance_value in (balance_updates or {}).items():
        update_fields["$set"][balance_field] = balance_value

    year_key = from_date[:4]
    summary_path = f"yearly_summary.{year_key}"
    update_fields["$set"][f"{summary_path}.last_updated_at"] = now
    update_fields["$inc"] = {f"{summary_path}.{summary_leave_type.lower()}_availed": transaction["days_availed"]}

    return update_fields


def new_empty_account(
    employee_id: str,
    user_id: str,
    *,
    initial_balances: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Seed a blank leave-ledger account."""
    now = datetime.now(timezone.utc).isoformat()
    balances = {
        "earned_leave_balance": 0.0,
        "half_pay_leave_balance": 0.0,
        "commuted_leave_balance": 0.0,
        "leave_not_due_balance": 0.0,
        "casual_leave_balance": 0.0,
    }
    for field_name, value in (initial_balances or {}).items():
        if field_name in balances and value is not None:
            balances[field_name] = float(value)

    return {
        "id": str(uuid.uuid4()),
        "employee_id": employee_id,
        **balances,
        "transactions": [],
        "yearly_summary": {},
        "created_at": now,
        "created_by": user_id,
    }
