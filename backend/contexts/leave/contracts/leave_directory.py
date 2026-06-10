"""Leave context read-only contracts for cross-context consumers."""
from __future__ import annotations

from datetime import date
from typing import Any

from contexts.leave.domain.leave_rules import (
    DEFAULT_LEAVE_TYPES,
    EMPLOYMENT_TYPES_WITH_LEAVE_ACCOUNT,
    compute_leave_balances,
    normalize_employment_type_code,
    normalize_leave_type_record,
)


async def list_leave_applications_for_employee(
    db,
    *,
    employee_id: str,
    limit: int = 200,
) -> list[dict[str, Any]]:
    return (
        await db.leave_applications.find(
            {"employee_id": employee_id},
            {"_id": 0},
        )
        .sort("applied_at", -1)
        .to_list(limit)
    )


async def count_leave_applications_by_status(
    db,
    *,
    employee_id: str,
    status: str,
) -> int:
    return await db.leave_applications.count_documents(
        {"employee_id": employee_id, "status": status}
    )


async def list_sanctioned_leave_applications(
    db,
    *,
    employee_id: str,
    leave_type_code: str,
    from_date_lte: str,
    to_date_gte: str,
    limit: int = 5000,
) -> list[dict[str, Any]]:
    return (
        await db.leave_applications.find(
            {
                "employee_id": employee_id,
                "leave_type_code": leave_type_code,
                "status": "SANCTIONED",
                "from_date": {"$lte": from_date_lte},
                "to_date": {"$gte": to_date_gte},
            },
            {"_id": 0},
        )
        .to_list(limit)
    )


async def list_leave_types(
    db,
    *,
    limit: int = 100,
) -> list[dict[str, Any]]:
    return await db.leave_types.find({}, {"_id": 0}).to_list(limit)


async def get_leave_ledger_entry(
    db,
    *,
    employee_id: str,
) -> dict[str, Any] | None:
    return await db.leave_ledger_entries.find_one(
        {"employee_id": employee_id}, {"_id": 0}
    )


async def get_leave_balances_for_employee(
    db,
    *,
    employee_id: str,
    employment_type: str | None,
    service_start_date: str | None = None,
    leave_types_loader=None,
    leave_ledger_loader=None,
    sanctioned_leave_loader=None,
) -> dict[str, Any]:
    employment_type_code = normalize_employment_type_code(employment_type)
    if (
        not employment_type_code
        or employment_type_code not in EMPLOYMENT_TYPES_WITH_LEAVE_ACCOUNT
    ):
        return {}

    leave_types_loader = leave_types_loader or list_leave_types
    leave_ledger_loader = leave_ledger_loader or get_leave_ledger_entry
    sanctioned_leave_loader = (
        sanctioned_leave_loader or list_sanctioned_leave_applications
    )

    leave_types_data = await leave_types_loader(db)
    if not leave_types_data:
        leave_types_data = DEFAULT_LEAVE_TYPES

    normalized = [
        normalize_leave_type_record(leave_type)
        for leave_type in leave_types_data
        if leave_type.get("is_active", True)
    ]
    applicable = [
        leave_type
        for leave_type in normalized
        if employment_type_code in (leave_type.get("applicable_employment_types") or [])
    ]

    account = await leave_ledger_loader(db, employee_id=employee_id)
    year = date.today().year
    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)

    year_used: dict[str, float] = {}
    total_used: dict[str, float] = {}

    for leave_type in applicable:
        code = leave_type.get("leave_code") or leave_type.get("code")
        if not code:
            continue
        is_accumulative = bool(leave_type.get("is_accumulative", False))
        has_lifetime_cap = leave_type.get("max_days_lifetime") is not None

        if is_accumulative and code in ("EL", "HPL") and not account:
            total_used[code] = await _get_total_used_leave_days(
                db,
                employee_id,
                code,
                sanctioned_leave_loader=sanctioned_leave_loader,
            )
        elif has_lifetime_cap:
            total_used[code] = await _get_total_used_leave_days(
                db,
                employee_id,
                code,
                sanctioned_leave_loader=sanctioned_leave_loader,
            )
        elif code == "CL" or (not is_accumulative and code not in ("CML", "LND")):
            year_used[code] = await _get_used_leave_days(
                db,
                employee_id,
                code,
                year,
                sanctioned_leave_loader=sanctioned_leave_loader,
            )

    return compute_leave_balances(
        leave_types=normalized,
        employment_type_code=employment_type_code,
        account=account,
        service_start_date=service_start_date,
        year_used=year_used,
        total_used=total_used,
    )


async def _get_used_leave_days(
    db,
    employee_id: str,
    leave_type_code: str,
    year: int,
    *,
    sanctioned_leave_loader,
) -> float:
    applications = await sanctioned_leave_loader(
        db,
        employee_id=employee_id,
        leave_type_code=leave_type_code,
        from_date_lte=f"{year}-12-31",
        to_date_gte=f"{year}-01-01",
    )
    return float(sum(float(app.get("days_applied", 0) or 0) for app in applications))


async def _get_total_used_leave_days(
    db,
    employee_id: str,
    leave_type_code: str,
    *,
    sanctioned_leave_loader,
) -> float:
    applications = await sanctioned_leave_loader(
        db,
        employee_id=employee_id,
        leave_type_code=leave_type_code,
        from_date_lte="9999-12-31",
        to_date_gte="0001-01-01",
    )
    return float(sum(float(app.get("days_applied", 0) or 0) for app in applications))


async def list_pending_leave_applications(
    db,
    *,
    employee_ids: list[str],
    statuses: list[str],
    limit: int = 500,
) -> list[dict[str, Any]]:
    if not employee_ids or not statuses:
        return []
    return (
        await db.leave_applications.find(
            {
                "employee_id": {"$in": employee_ids},
                "status": {"$in": statuses},
            },
            {"_id": 0},
        )
        .sort("applied_at", -1)
        .to_list(limit)
    )


async def count_pending_leave_applications(
    db,
    *,
    employee_ids: list[str],
    statuses: list[str],
) -> int:
    if not employee_ids or not statuses:
        return 0
    return await db.leave_applications.count_documents(
        {
            "employee_id": {"$in": employee_ids},
            "status": {"$in": statuses},
        }
    )


async def list_leave_applications(
    db,
    *,
    employee_ids: list[str] | None = None,
    status: str | None = None,
    leave_type_code: str | None = None,
    limit: int = 500,
    offset: int = 0,
) -> list[dict[str, Any]]:
    query: dict[str, Any] = {}
    if employee_ids is not None:
        if not employee_ids:
            return []
        query["employee_id"] = {"$in": employee_ids}
    if status:
        query["status"] = status
    if leave_type_code:
        query["leave_type_code"] = leave_type_code

    cursor = db.leave_applications.find(query, {"_id": 0}).sort("applied_at", -1).skip(offset).limit(limit)
    return await cursor.to_list(limit)


async def count_leave_applications(
    db,
    *,
    employee_ids: list[str] | None = None,
    status: str | None = None,
    leave_type_code: str | None = None,
) -> int:
    query: dict[str, Any] = {}
    if employee_ids is not None:
        if not employee_ids:
            return 0
        query["employee_id"] = {"$in": employee_ids}
    if status:
        query["status"] = status
    if leave_type_code:
        query["leave_type_code"] = leave_type_code
    return int(await db.leave_applications.count_documents(query))


async def get_leave_application_by_id(
    db,
    *,
    leave_id: str,
) -> dict[str, Any] | None:
    return await db.leave_applications.find_one({"id": leave_id}, {"_id": 0})


async def leave_application_exists(
    db,
    *,
    leave_id: str,
) -> bool:
    normalized_leave_id = str(leave_id or "").strip()
    if not normalized_leave_id:
        return False
    return bool(
        await db.leave_applications.find_one(
            {"id": normalized_leave_id},
            {"_id": 0, "id": 1},
        )
    )


