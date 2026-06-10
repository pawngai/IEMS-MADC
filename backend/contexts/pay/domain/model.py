from __future__ import annotations


def _as_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def build_pay_snapshot(employee_id: str, entries: list[dict]) -> dict:
    basic_pay: float | None = None
    pay_level: str | None = None
    effective_date: str | None = None
    allowances: dict[str, float] = {}

    # Entries are read newest-first; first relevant value is the current one.
    for entry in entries:
        event_code = str(entry.get("event_code") or "").upper()
        payload = entry.get("payload") or {}

        if event_code == "PAY_REVISED" and basic_pay is None:
            pay_value = _as_float(payload.get("basic_pay"))
            if pay_value is None:
                pay_value = _as_float(entry.get("amount"))
            basic_pay = pay_value
            pay_level = payload.get("pay_level")
            effective_date = payload.get("effective_date")

        if event_code == "ALLOWANCE_CHANGED":
            allowance_code = str(payload.get("allowance_code") or "").strip().upper()
            allowance_amount = _as_float(payload.get("amount"))
            if allowance_code and allowance_amount is not None and allowance_code not in allowances:
                allowances[allowance_code] = allowance_amount

    return {
        "employee_id": employee_id,
        "basic_pay": basic_pay,
        "pay_level": pay_level,
        "effective_date": effective_date,
        "allowances": allowances,
    }
