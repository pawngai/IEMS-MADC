"""
ESS (Employee Self-Service) Portal — Repository layer.

Pure MongoDB queries. No business logic.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from contexts.employee_master.contracts.profile_directory import (
    find_profile_view,
)
from contexts.employee_master.contracts.profile_commands import (
    update_profile_fields,
)
from contexts.documents.contracts.document_metadata import (
    download_subject_document_for_employee,
    get_subject_document_for_employee,
    list_subject_documents_for_employee,
)
from contexts.leave_attendance.contracts.leave_directory import (
    count_leave_applications_by_status,
    get_leave_balances_for_employee,
    get_leave_ledger_entry,
    list_leave_applications_for_employee,
    list_leave_types,
    list_sanctioned_leave_applications,
)
from contexts.notifications.contracts.notification_directory import (
    count_unread_notifications as _count_unread,
    list_notifications_for_employee as _list_notifications,
)
from contexts.notifications.contracts.notification_commands import mark_notification_read as _mark_read
from contexts.service_book.contracts.service_book_directory import (
    count_service_book_parts as _count_sb_parts,
    count_servicebook_entries as _count_sb_entries,
    get_employee_initial_appointment_date as _get_employee_initial_appointment_date,
    count_projected_service_book_entries as _count_projected_sb_entries,
    get_projected_service_book_part as _get_projected_sb_part,
    get_service_book_part as _get_sb_part,
    list_projected_service_book_entries as _list_projected_sb_entries,
    list_servicebook_entries as _list_sb_entries,
)

EMPLOYMENT_TYPE_MAP = {
    "REGULAR": "REG",
    "CONTRACTUAL": "CON",
    "DAILY_WAGE": "CAS",
    "DEPUTATION": "DEP",
    "REEMPLOYED": "REE",
    "OUTSOURCED": "OUT",
    "ADHOC": "ADH",
}

EMPLOYMENT_TYPES_WITH_LEAVE_ACCOUNT = {"REG", "CON", "ADH", "DEP", "REE"}

DEFAULT_LEAVE_TYPES = [
    {
        "code": "CL",
        "description": "Casual Leave",
        "leave_code": "CL",
        "max_days_per_year": 8,
        "max_days_per_spell": 5,
        "is_accumulative": False,
        "applicable_employment_types": ["REG", "CON", "ADH", "DEP", "REE"],
    },
    {
        "code": "EL",
        "description": "Earned Leave",
        "leave_code": "EL",
        "max_days_per_year": 30,
        "is_accumulative": True,
        "applicable_employment_types": ["REG", "DEP"],
    },
    {
        "code": "HPL",
        "description": "Half Pay Leave",
        "leave_code": "HPL",
        "max_days_per_year": 20,
        "is_accumulative": True,
        "applicable_employment_types": ["REG", "DEP"],
    },
    {
        "code": "CML",
        "description": "Commuted Leave",
        "leave_code": "CML",
        "max_days_per_year": None,
        "is_accumulative": False,
        "applicable_employment_types": ["REG", "DEP"],
    },
    {
        "code": "LND",
        "description": "Leave Not Due",
        "leave_code": "LND",
        "max_days_per_year": None,
        "is_accumulative": False,
        "applicable_employment_types": ["REG", "DEP"],
    },
    {
        "code": "CCL",
        "description": "Child Care Leave",
        "leave_code": "CCL",
        "max_days_per_year": 730,
        "min_days_per_spell": 5,
        "max_days_lifetime": 730,
        "is_accumulative": False,
        "applicable_employment_types": ["REG", "DEP"],
    },
    {
        "code": "ML",
        "description": "Maternity Leave",
        "leave_code": "ML",
        "max_days_per_year": 180,
        "max_days_per_spell": 180,
        "is_accumulative": False,
        "applicable_employment_types": ["REG", "CON", "DEP"],
    },
    {
        "code": "PL",
        "description": "Paternity Leave",
        "leave_code": "PL",
        "max_days_per_year": 15,
        "max_days_per_spell": 15,
        "is_accumulative": False,
        "applicable_employment_types": ["REG", "DEP"],
    },
    {
        "code": "SCL",
        "description": "Special Casual Leave",
        "leave_code": "SCL",
        "max_days_per_year": 14,
        "is_accumulative": False,
        "applicable_employment_types": ["REG", "CON", "ADH", "DEP"],
    },
]


LEAVE_POLICY_DEFAULTS_BY_CODE = {
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


def _normalize_employment_type_code(employment_type: str) -> str | None:
    if not employment_type:
        return None
    return EMPLOYMENT_TYPE_MAP.get(employment_type, employment_type)


def _normalize_leave_type_record(record: dict[str, Any]) -> dict[str, Any]:
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
    policy_defaults = LEAVE_POLICY_DEFAULTS_BY_CODE.get(
        str(leave_code or code or "").strip().upper(),
        {},
    )

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
        "is_accumulative": bool(pick("is_accumulative", False)),
        "applicable_employment_types": pick("applicable_employment_types", []) or [],
        "is_active": record.get("is_active", True),
    }


def _parse_date(date_str: str) -> date:
    return datetime.strptime(date_str, "%Y-%m-%d").date()


async def list_subject_documents(
    db,
    *,
    employee_id: str,
    employee_code: str | None = None,
    query: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    document_type: str | None = None,
    category: str | None = None,
    source_context: str | None = None,
    is_locked: bool | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    return await list_subject_documents_for_employee(
        employee_id=employee_id,
        employee_code=employee_code,
        query=query,
        entity_type=entity_type,
        entity_id=entity_id,
        document_type=document_type,
        category=category,
        source_context=source_context,
        is_locked=is_locked,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
        db=db,
    )


async def download_subject_document(
    db,
    *,
    filename: str,
    employee_id: str,
    employee_code: str | None = None,
):
    return await download_subject_document_for_employee(
        filename,
        employee_id=employee_id,
        employee_code=employee_code,
        db=db,
    )


async def get_subject_document(
    db,
    *,
    filename: str,
    employee_id: str,
    employee_code: str | None = None,
):
    return await get_subject_document_for_employee(
        filename,
        employee_id=employee_id,
        employee_code=employee_code,
        db=db,
    )


def _overlap_days(a_start: date, a_end: date, b_start: date, b_end: date) -> int:
    latest_start = max(a_start, b_start)
    earliest_end = min(a_end, b_end)
    if earliest_end < latest_start:
        return 0
    return (earliest_end - latest_start).days + 1


async def _get_used_leave_days(
    db, employee_id: str, leave_type_code: str, year: int
) -> float:
    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)
    records = await list_sanctioned_leave_applications(
        db,
        employee_id=employee_id,
        leave_type_code=leave_type_code,
        from_date_lte=year_end.isoformat(),
        to_date_gte=year_start.isoformat(),
    )

    total = 0.0
    for record in records:
        try:
            record_start = _parse_date(record.get("from_date"))
            record_end = _parse_date(record.get("to_date"))
            total += _overlap_days(record_start, record_end, year_start, year_end)
        except Exception:
            continue
    return float(total)


async def _get_total_used_leave_days(db, employee_id: str, leave_type_code: str) -> float:
    records = await list_sanctioned_leave_applications(
        db,
        employee_id=employee_id,
        leave_type_code=leave_type_code,
        from_date_lte=date.max.isoformat(),
        to_date_gte=date.min.isoformat(),
    )

    total = 0.0
    for record in records:
        try:
            total += float(record.get("days_applied", 0) or 0)
        except Exception:
            continue
    return float(total)


async def find_profile(db, employee_id: str) -> Optional[dict[str, Any]]:
    return await find_profile_view(
        db,
        employee_id=employee_id,
        projection={"_id": 0},
    )


async def _resolve_service_start_date(
    db,
    *,
    employee_id: str,
    profile: dict[str, Any] | None,
) -> str | None:
    for field_name in ("date_of_initial_engagement", "initial_appointment_date"):
        value = str((profile or {}).get(field_name) or "").strip()
        if value:
            return value
    return await _get_employee_initial_appointment_date(db, employee_id=employee_id)


async def update_profile_contact(db, employee_id: str, updates: dict[str, Any]) -> None:
    await update_profile_fields(
        db,
        employee_id=employee_id,
        updates=updates,
    )


async def get_service_book_part(
    db,
    employee_id: str,
    part: str,
) -> Optional[dict[str, Any]]:
    return await _get_sb_part(db, employee_id=employee_id, part=part)


async def count_service_book_parts(db, employee_id: str) -> int:
    return await _count_sb_parts(db, employee_id=employee_id)


async def list_servicebook_entries(
    db,
    employee_id: str,
    *,
    part_key: str | None = None,
    active_only: bool = True,
    statuses: list[str] | None = None,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    return await _list_sb_entries(
        db,
        employee_id=employee_id,
        part_key=part_key,
        active_only=active_only,
        statuses=statuses,
        limit=limit,
    )


async def list_projected_service_book_entries(
    db,
    employee_id: str,
    *,
    part_code: str | None = None,
    statuses: list[str] | None = None,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    return await _list_projected_sb_entries(
        db,
        employee_id=employee_id,
        part_code=part_code,
        statuses=statuses,
        limit=limit,
    )


async def get_projected_service_book_part(
    db,
    employee_id: str,
    part_code: str,
) -> Optional[dict[str, Any]]:
    return await _get_projected_sb_part(
        db, employee_id=employee_id, part_code=part_code
    )


async def count_servicebook_entries(
    db,
    employee_id: str,
    *,
    active_only: bool = True,
    statuses: list[str] | None = None,
) -> int:
    return await _count_sb_entries(
        db,
        employee_id=employee_id,
        active_only=active_only,
        statuses=statuses,
    )


async def count_projected_service_book_entries(
    db,
    employee_id: str,
    *,
    statuses: list[str] | None = None,
) -> int:
    return await _count_projected_sb_entries(
        db, employee_id=employee_id, statuses=statuses
    )


async def list_leave_applications(
    db,
    employee_id: str,
    *,
    limit: int = 200,
) -> list[dict[str, Any]]:
    return await list_leave_applications_for_employee(
        db, employee_id=employee_id, limit=limit
    )


async def get_leave_balances(db, employee_id: str) -> dict[str, Any]:
    profile = await find_profile(db, employee_id)
    if not profile:
        return {"employee_id": employee_id, "balances": {}}

    emp_type = _normalize_employment_type_code(
        profile.get("employment_type") or profile.get("employment_type_code")
    )
    if not emp_type or emp_type not in EMPLOYMENT_TYPES_WITH_LEAVE_ACCOUNT:
        return {"employee_id": employee_id, "balances": {}}

    service_start_date = await _resolve_service_start_date(
        db,
        employee_id=employee_id,
        profile=profile,
    )

    results = await get_leave_balances_for_employee(
        db,
        employee_id=employee_id,
        employment_type=emp_type,
        service_start_date=service_start_date,
        leave_types_loader=list_leave_types,
        leave_ledger_loader=get_leave_ledger_entry,
        sanctioned_leave_loader=list_sanctioned_leave_applications,
    )

    return {"employee_id": employee_id, "balances": results}


async def count_leaves_by_status(db, employee_id: str, status: str) -> int:
    return await count_leave_applications_by_status(
        db, employee_id=employee_id, status=status
    )


async def list_notifications(
    db,
    employee_id: str,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    return await _list_notifications(db, employee_id=employee_id, limit=limit)


async def mark_notification_read(db, notification_id: str) -> None:
    await _mark_read(db, notification_id=notification_id)


async def count_unread_notifications(db, employee_id: str) -> int:
    return await _count_unread(db, employee_id=employee_id)
