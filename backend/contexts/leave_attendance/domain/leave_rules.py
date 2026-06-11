"""Leave domain rules — employment types, leave type definitions, date helpers, balance computation."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any


# ── Employment-type constants ───────────────────────────────────────

EMPLOYMENT_TYPE_MAP: dict[str, str] = {
    "REGULAR": "REG",
    "CONTRACTUAL": "CON",
    "DAILY_WAGE": "CAS",
    "DEPUTATION": "DEP",
    "REEMPLOYED": "REE",
    "OUTSOURCED": "OUT",
    "ADHOC": "ADH",
}

EMPLOYMENT_TYPES_WITH_LEAVE_ACCOUNT: set[str] = {"REG", "CON", "ADH", "DEP", "REE"}
LEDGER_BALANCE_CODES: set[str] = {"EL", "HPL", "CL"}

LEAVE_POLICY_DEFAULTS_BY_CODE: dict[str, dict[str, Any]] = {
    "CL": {
        "max_days_per_spell": 5,
        "balance_strategy": "ledger",
        "debits_leave_account": True,
        "records_ledger_transaction": True,
    },
    "CCL": {
        "min_days_per_spell": 5,
        "max_days_lifetime": 730,
        "balance_strategy": "lifetime_cap",
        "debits_leave_account": False,
        "records_ledger_transaction": False,
    },
    "CML": {
        "balance_strategy": "hpl_half",
        "debit_multiplier": 2.0,
        "debit_source_leave_code": "HPL",
        "debits_leave_account": True,
        "records_ledger_transaction": True,
    },
    "LND": {
        "balance_strategy": "lifetime_cap",
        "max_days_lifetime": 360,
        "debits_leave_account": False,
        "records_ledger_transaction": True,
    },
    "ML": {
        "max_days_per_spell": 180,
        "balance_strategy": "non_debited_special",
        "debits_leave_account": False,
        "records_ledger_transaction": False,
    },
    "PL": {
        "max_days_per_spell": 15,
        "balance_strategy": "non_debited_special",
        "debits_leave_account": False,
        "records_ledger_transaction": False,
    },
    "SCL": {
        "balance_strategy": "annual_cap",
        "debits_leave_account": False,
        "records_ledger_transaction": False,
    },
    "EL": {
        "balance_strategy": "ledger",
        "debits_leave_account": True,
        "records_ledger_transaction": True,
    },
    "HPL": {
        "balance_strategy": "ledger",
        "debits_leave_account": True,
        "records_ledger_transaction": True,
    },
}

REQUIRED_SUPPORTING_DOCUMENT_CODES: set[str] = {"CML", "ML", "PL", "CCL"}

# ── Default leave-type catalogue ────────────────────────────────────

DEFAULT_LEAVE_TYPES: list[dict[str, Any]] = [
    {
        "code": "CL",
        "description": "Casual Leave",
        "leave_code": "CL",
        "max_days_per_year": 8,
        "is_encashable": False,
        "is_accumulative": False,
        "applicable_employment_types": ["REG", "CON", "ADH", "DEP", "REE"],
    },
    {
        "code": "EL",
        "description": "Earned Leave",
        "leave_code": "EL",
        "max_days_per_year": 30,
        "is_encashable": True,
        "is_accumulative": True,
        "applicable_employment_types": ["REG", "DEP"],
    },
    {
        "code": "HPL",
        "description": "Half Pay Leave",
        "leave_code": "HPL",
        "max_days_per_year": 20,
        "is_encashable": False,
        "is_accumulative": True,
        "applicable_employment_types": ["REG", "DEP"],
    },
    {
        "code": "CML",
        "description": "Commuted Leave",
        "leave_code": "CML",
        "max_days_per_year": None,
        "is_encashable": False,
        "is_accumulative": False,
        "applicable_employment_types": ["REG", "DEP"],
    },
    {
        "code": "LND",
        "description": "Leave Not Due",
        "leave_code": "LND",
        "max_days_per_year": None,
        "is_encashable": False,
        "is_accumulative": False,
        "applicable_employment_types": ["REG", "DEP"],
    },
    {
        "code": "CCL",
        "description": "Child Care Leave",
        "leave_code": "CCL",
        "max_days_per_year": 730,
        "is_encashable": False,
        "is_accumulative": False,
        "applicable_employment_types": ["REG", "DEP"],
    },
    {
        "code": "ML",
        "description": "Maternity Leave",
        "leave_code": "ML",
        "max_days_per_year": 180,
        "is_encashable": False,
        "is_accumulative": False,
        "applicable_employment_types": ["REG", "CON", "DEP"],
    },
    {
        "code": "PL",
        "description": "Paternity Leave",
        "leave_code": "PL",
        "max_days_per_year": 15,
        "is_encashable": False,
        "is_accumulative": False,
        "applicable_employment_types": ["REG", "DEP"],
    },
    {
        "code": "SCL",
        "description": "Special Casual Leave",
        "leave_code": "SCL",
        "max_days_per_year": 14,
        "is_encashable": False,
        "is_accumulative": False,
        "applicable_employment_types": ["REG", "CON", "ADH", "DEP"],
    },
]


# ── Pure helpers ────────────────────────────────────────────────────

def normalize_employment_type_code(employment_type: str | None) -> str | None:
    if not employment_type:
        return None
    return EMPLOYMENT_TYPE_MAP.get(employment_type, employment_type)


def get_leave_policy_defaults(leave_type_code: str | None) -> dict[str, Any]:
    normalized_code = str(leave_type_code or "").strip().upper()
    return dict(LEAVE_POLICY_DEFAULTS_BY_CODE.get(normalized_code, {}))


def get_required_supporting_document_message(
    leave_type_code: str | None,
    *,
    medical_certificate_provided: bool | None = None,
    commuted_leave_basis: str | None = None,
    childbirth_date: str | None = None,
    adoption_date: str | None = None,
    child_date_of_birth: str | None = None,
) -> str | None:
    normalized_code = str(leave_type_code or "").strip().upper()
    if normalized_code not in REQUIRED_SUPPORTING_DOCUMENT_CODES:
        return None

    if normalized_code == "CML":
        normalized_basis = str(commuted_leave_basis or "").strip().upper()
        if normalized_basis == "STUDY_PUBLIC_INTEREST":
            return (
                "Commuted leave requires a supporting document. "
                "Upload the approved public-interest study document."
            )
        if medical_certificate_provided:
            return (
                "Commuted leave requires a supporting document. "
                "Upload the medical certificate."
            )
        return (
            "Commuted leave requires a supporting document. "
            "Upload the medical certificate or approved public-interest study document."
        )

    if normalized_code == "ML":
        if str(childbirth_date or "").strip():
            return (
                "Maternity leave requires a supporting document. "
                "Upload the childbirth record."
            )
        return (
            "Maternity leave requires a supporting document. "
            "Upload the expected-delivery certificate."
        )

    if normalized_code == "PL":
        if str(adoption_date or "").strip() and not str(childbirth_date or "").strip():
            return (
                "Paternity leave requires a supporting document. "
                "Upload the adoption record."
            )
        return (
            "Paternity leave requires a supporting document. "
            "Upload the childbirth record."
        )

    if normalized_code == "CCL":
        if str(child_date_of_birth or "").strip():
            return (
                "Child care leave requires a supporting document. "
                "Upload proof of the child's date of birth."
            )
        return (
            "Child care leave requires a supporting document. "
            "Upload proof of the child's date of birth."
        )

    return None


def parse_date(date_str: str) -> date:
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def calculate_days(from_date: str, to_date: str) -> float:
    """Return inclusive day count.  Raises ValueError if to_date < from_date."""
    start = parse_date(from_date)
    end = parse_date(to_date)
    if end < start:
        raise ValueError("to_date cannot be before from_date")
    return float((end - start).days + 1)


def overlap_days(a_start: date, a_end: date, b_start: date, b_end: date) -> int:
    latest_start = max(a_start, b_start)
    earliest_end = min(a_end, b_end)
    if earliest_end < latest_start:
        return 0
    return (earliest_end - latest_start).days + 1


def months_between(start: date, end: date) -> int:
    if end < start:
        return 0
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day >= start.day:
        months += 1
    return max(months, 0)


def normalize_leave_type_record(record: dict[str, Any]) -> dict[str, Any]:
    meta = record.get("metadata") or {}

    def pick(key: str, default=None):
        value = record.get(key)
        if value is None:
            value = meta.get(key, default)
        return value

    code = pick("code") or pick("leave_code") or meta.get("leave_code")
    leave_code = pick("leave_code") or code
    description = (
        record.get("description") or record.get("name") or meta.get("description")
    )
    policy_defaults = get_leave_policy_defaults(leave_code or code)

    return {
        "code": code,
        "description": description,
        "leave_code": leave_code,
        "max_days_per_year": pick("max_days_per_year"),
        "min_days_per_spell": pick(
            "min_days_per_spell", policy_defaults.get("min_days_per_spell")
        ),
        "max_days_per_spell": pick(
            "max_days_per_spell", policy_defaults.get("max_days_per_spell")
        ),
        "max_days_lifetime": pick(
            "max_days_lifetime", policy_defaults.get("max_days_lifetime")
        ),
        "balance_strategy": pick(
            "balance_strategy", policy_defaults.get("balance_strategy", "annual_cap")
        ),
        "debit_multiplier": float(
            pick("debit_multiplier", policy_defaults.get("debit_multiplier", 1.0))
            or 1.0
        ),
        "debit_source_leave_code": pick(
            "debit_source_leave_code", policy_defaults.get("debit_source_leave_code")
        ),
        "debits_leave_account": bool(
            pick("debits_leave_account", policy_defaults.get("debits_leave_account", False))
        ),
        "records_ledger_transaction": bool(
            pick(
                "records_ledger_transaction",
                policy_defaults.get("records_ledger_transaction", False),
            )
        ),
        "is_encashable": bool(pick("is_encashable", False)),
        "is_accumulative": bool(pick("is_accumulative", False)),
        "applicable_employment_types": pick("applicable_employment_types", []) or [],
        "is_active": record.get("is_active", True),
        "version": record.get("version"),
    }


# ── Balance computation (pure domain — receives data, no DB) ───────

def compute_used_days_from_records(
    records: list[dict[str, Any]],
    year_start: date,
    year_end: date,
) -> float:
    """Sum overlap-weighted days from sanctioned leave records for a date range."""
    total = 0.0
    for record in records:
        try:
            record_start = parse_date(record.get("from_date"))
            record_end = parse_date(record.get("to_date"))
            total += overlap_days(record_start, record_end, year_start, year_end)
        except Exception:
            continue
    return float(total)


def compute_used_days_total(records: list[dict[str, Any]]) -> float:
    """Sum raw days_applied from all sanctioned records."""
    total = 0.0
    for record in records:
        try:
            total += float(record.get("days_applied", 0))
        except Exception:
            continue
    return float(total)


def compute_leave_balances(
    *,
    leave_types: list[dict[str, Any]],
    employment_type_code: str,
    account: dict[str, Any] | None,
    service_start_date: str | None,
    year_used: dict[str, float],
    total_used: dict[str, float],
) -> dict[str, Any]:
    """Pure balance computation.

    Parameters
    ----------
    leave_types:
        Normalized leave-type catalog records.
    employment_type_code:
        Normalized short code (e.g. "REG").
    account:
        Leave-ledger account document (may be None for new employees).
    service_start_date:
        ISO date string of the employee's service start for accrual.
    year_used:
        Mapping of leave_code → used days *this year* (pre-computed).
    total_used:
        Mapping of leave_code → total used days ever (pre-computed).
    """
    applicable = [
        lt for lt in leave_types
        if employment_type_code in (lt.get("applicable_employment_types") or [])
    ]

    balances = {
        "EL": account.get("earned_leave_balance", 0) if account else 0,
        "HPL": account.get("half_pay_leave_balance", 0) if account else 0,
        "CML": account.get("commuted_leave_balance", 0) if account else 0,
        "LND": account.get("leave_not_due_balance", 0) if account else 0,
        "CL": account.get("casual_leave_balance", 0) if account else 0,
    }

    accruals: dict[str, float] = {}
    if not account and service_start_date:
        try:
            start_date = parse_date(service_start_date)
            months = months_between(start_date, date.today())
            for lt in applicable:
                if lt.get("is_accumulative") and lt.get("max_days_per_year"):
                    rate = float(lt.get("max_days_per_year")) / 12.0
                    accruals[lt.get("leave_code") or lt.get("code")] = round(
                        months * rate, 2
                    )
        except Exception:
            pass

    results: dict[str, Any] = {}
    ledger_available: dict[str, float | None] = {}

    def _resolve_ledger_available(code: str) -> float | None:
        if code in ledger_available:
            return ledger_available[code]
        if code not in LEDGER_BALANCE_CODES:
            return None
        if account:
            available = float(balances.get(code, 0))
        elif code in ("EL", "HPL"):
            accrued = float(accruals.get(code, 0))
            used_tot = total_used.get(code, 0.0)
            available = max(accrued - used_tot, 0.0)
        else:
            available = 0.0
        ledger_available[code] = available
        return available

    for lt in applicable:
        code = lt.get("leave_code") or lt.get("code")
        max_days = lt.get("max_days_per_year")
        max_days_lifetime = lt.get("max_days_lifetime")
        balance_strategy = lt.get("balance_strategy") or "annual_cap"
        is_accumulative = lt.get("is_accumulative", False)
        used_year = 0.0
        used_total = 0.0
        available = None

        if balance_strategy == "ledger":
            if code == "CL" and max_days is not None:
                used_year = year_used.get(code, 0.0)
                available = max(float(max_days) - used_year, 0.0)
            else:
                available = _resolve_ledger_available(code)
        elif balance_strategy == "hpl_half":
            hpl_available = _resolve_ledger_available("HPL") or 0.0
            available = max(hpl_available / 2.0, 0.0)
        elif balance_strategy == "lifetime_cap":
            used_total = total_used.get(code, 0.0)
            if max_days_lifetime is not None:
                available = max(float(max_days_lifetime) - used_total, 0.0)
        elif balance_strategy == "non_debited_special":
            available = None
        else:
            if max_days is not None:
                used_year = year_used.get(code, 0.0)
                available = max(float(max_days) - used_year, 0.0)

        results[code] = {
            "leave_code": code,
            "description": lt.get("description"),
            "max_days_per_year": max_days,
            "min_days_per_spell": lt.get("min_days_per_spell"),
            "max_days_per_spell": lt.get("max_days_per_spell"),
            "max_days_lifetime": max_days_lifetime,
            "balance_strategy": balance_strategy,
            "debit_multiplier": lt.get("debit_multiplier", 1.0),
            "debit_source_leave_code": lt.get("debit_source_leave_code"),
            "debits_leave_account": lt.get("debits_leave_account", False),
            "records_ledger_transaction": lt.get("records_ledger_transaction", False),
            "is_accumulative": is_accumulative,
            "used_days_year": used_year,
            "used_days_total": used_total,
            "available_days": available,
        }

    return results
