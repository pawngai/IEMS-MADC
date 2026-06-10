from __future__ import annotations

from datetime import date, datetime, timezone
import logging
from typing import Any

from fastapi import HTTPException

from app_platform.db.atomic import call_with_optional_session
from contexts.documents.contracts.document_metadata import (
    get_accessible_document_metadata as _get_accessible_document_metadata,
)
from contexts.employee_master.contracts.identity_directory import get_employee_department_code
from contexts.identity.contracts.user_directory import get_user_department_code
from contexts.leave.contracts.dto import LeaveApplicationCreateDTO
from contexts.leave.domain.leave_accounting import (
    build_account_update,
    build_debit_transaction,
    new_empty_account,
    opening_balance_for,
)
from contexts.leave.domain.leave_rules import (
    DEFAULT_LEAVE_TYPES,
    EMPLOYMENT_TYPES_WITH_LEAVE_ACCOUNT,
    calculate_days,
    compute_leave_balances,
    compute_used_days_from_records,
    compute_used_days_total,
    get_leave_policy_defaults,
    get_required_supporting_document_message,
    normalize_employment_type_code,
    normalize_leave_type_record,
)
from contexts.leave.infrastructure.document_lock import (
    lock_documents_for_finalized_leave as _lock_documents_for_finalized_leave,
)
from contexts.leave.infrastructure.leave_constants import LEAVE_LEDGER_COLLECTION
from contexts.leave.repository.leave_repository import LeaveRuntimeRepository
from contexts.rbac.contracts.access_control import require_permissions
from contexts.rbac.contracts.authorization_service import EMPLOYEE, resolveScopeAccess
from contexts.service_book.contracts.service_book_directory import (
    get_employee_initial_appointment_date,
)

logger = logging.getLogger(__name__)

# ── Thin infrastructure helpers (no business logic) ─────────────────

async def _find_employee_profile(
    repository: LeaveRuntimeRepository, employee_id: str
) -> dict[str, Any] | None:
    return await repository.find_employee_profile(employee_id)


async def _get_leave_type(
    repository: LeaveRuntimeRepository, leave_type_code: str
) -> dict[str, Any]:
    record = await repository.find_leave_type_record(leave_type_code)
    if record:
        return normalize_leave_type_record(record)

    for leave_type in DEFAULT_LEAVE_TYPES:
        if (
            leave_type.get("code") == leave_type_code
            or leave_type.get("leave_code") == leave_type_code
        ):
            return normalize_leave_type_record(leave_type)

    raise HTTPException(
        status_code=400, detail=f"Unknown leave type: {leave_type_code}"
    )


def _normalize_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"true", "1", "yes", "y"}:
            return True
        if text in {"false", "0", "no", "n"}:
            return False
    return bool(value)


async def _normalize_leave_attachments(
    attachments: list,
    *,
    current_user: dict,
    db=None,
    metadata_loader=_get_accessible_document_metadata,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen_filenames: set[str] = set()

    for attachment in attachments or []:
        filename = str(getattr(attachment, "filename", "") or "").strip()
        if not filename:
            raise HTTPException(
                status_code=400,
                detail="Supporting documents must reference an uploaded document filename",
            )
        if filename in seen_filenames:
            continue

        try:
            metadata = await metadata_loader(
                filename,
                current_user=current_user,
                db=db,
            )
        except HTTPException as exc:
            if exc.status_code in {403, 404}:
                raise HTTPException(
                    status_code=400,
                    detail=f"Supporting document is not accessible: {filename}",
                ) from exc
            raise

        normalized.append(
            {
                "url": str(metadata.get("url") or f"/api/documents/files/{filename}"),
                "filename": filename,
                "original_name": metadata.get("original_name") or filename,
                "file_size": metadata.get("file_size"),
                "content_type": metadata.get("content_type"),
            }
        )
        seen_filenames.add(filename)

    return normalized


async def _resolve_service_start_date(
    repository: LeaveRuntimeRepository,
    *,
    employee_id: str,
    profile: dict[str, Any] | None = None,
) -> str | None:
    profile = profile or await _find_employee_profile(repository, employee_id)
    for field_name in ("date_of_initial_engagement", "initial_appointment_date"):
        value = str((profile or {}).get(field_name) or "").strip()
        if value:
            return value

    db = getattr(repository, "_db", None)
    if db is None:
        return None
    return await get_employee_initial_appointment_date(db, employee_id=employee_id)


async def _ensure_initial_leave_account(
    repository: LeaveRuntimeRepository,
    *,
    employee_id: str,
    user_id: str | None,
    employment_type_code: str,
    service_start_date: str | None,
) -> dict[str, Any] | None:
    if employment_type_code not in EMPLOYMENT_TYPES_WITH_LEAVE_ACCOUNT:
        return None

    account = await repository.find_leave_account(employee_id)
    if account is not None:
        return account

    if not service_start_date or not user_id:
        return None

    account = await _build_initial_leave_account(
        repository,
        employee_id=employee_id,
        user_id=user_id,
    )
    await repository.update_leave_account(
        employee_id,
        {"$set": account},
        upsert=True,
    )
    return account


async def _build_leave_application_context(
    repository: LeaveRuntimeRepository,
    payload: LeaveApplicationCreateDTO,
    *,
    current_user: dict,
) -> dict[str, Any]:
    require_permissions(current_user, "LEAVE_APPLY_OWN")
    employee_id = current_user.get("employee_id")
    if not employee_id:
        raise HTTPException(status_code=400, detail="Employee identity not found")

    scope = resolveScopeAccess(current_user, target_employee_id=employee_id)
    if scope.get("scope") != EMPLOYEE or not scope.get("allowed"):
        raise HTTPException(
            status_code=403,
            detail="Leave can only be applied from employee self-service account",
        )

    profile = await _find_employee_profile(repository, employee_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    emp_type = normalize_employment_type_code(
        profile.get("employment_type") or profile.get("employment_type_code")
    )
    if not emp_type:
        raise HTTPException(status_code=400, detail="Invalid employment type")
    if emp_type not in EMPLOYMENT_TYPES_WITH_LEAVE_ACCOUNT:
        raise HTTPException(
            status_code=403,
            detail="Leave account not applicable for employment type",
        )

    await _ensure_initial_leave_account(
        repository,
        employee_id=employee_id,
        user_id=current_user.get("sub"),
        employment_type_code=emp_type,
        service_start_date=await _resolve_service_start_date(
            repository,
            employee_id=employee_id,
            profile=profile,
        ),
    )

    leave_type = await _get_leave_type(repository, payload.leave_type_code)
    if emp_type not in (leave_type.get("applicable_employment_types") or []):
        raise HTTPException(
            status_code=400, detail="Leave type not applicable for employment type"
        )

    try:
        days_applied = calculate_days(payload.from_date, payload.to_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    overlap = await repository.find_overlapping_leave_application(
        employee_id=employee_id,
        from_date=payload.from_date,
        to_date=payload.to_date,
        statuses=["SUBMITTED", "RECOMMENDED", "SANCTIONED"],
    )
    if overlap:
        raise HTTPException(
            status_code=400, detail="Overlapping leave application exists"
        )

    service_start = await _resolve_service_start_date(
        repository,
        employee_id=employee_id,
        profile=profile,
    )
    balances = await _fetch_leave_balances(
        repository, employee_id, emp_type, service_start_date=service_start
    )
    balance_info = balances.get(payload.leave_type_code, {})
    available = balance_info.get("available_days")
    if available is not None and days_applied > available:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient leave balance. Available: {available} days",
        )

    return {
        "employee_id": employee_id,
        "profile": profile,
        "employment_type_code": emp_type,
        "leave_type": leave_type,
        "days_applied": days_applied,
        "balance_info": balance_info,
    }


async def _resolve_user_department(db, current_user: dict) -> str | None:
    dept = current_user.get("department_code") or current_user.get("department_id")
    if dept:
        return str(dept).strip().upper() or None

    user_id = current_user.get("sub") or current_user.get("user_id") or current_user.get("id")
    if user_id:
        dept_code = await get_user_department_code(db, user_id=user_id)
        if dept_code:
            return str(dept_code).strip().upper() or None

    employee_id = current_user.get("employee_id")
    if employee_id:
        profile = await _find_employee_profile(LeaveRuntimeRepository(db=db), employee_id)
        if profile:
            return str(profile.get("current_department_id") or "").strip().upper() or None

    return None


async def _fetch_leave_balances(
    repository: LeaveRuntimeRepository,
    employee_id: str,
    employment_type_code: str,
    service_start_date: str | None = None,
) -> dict[str, Any]:
    """Gather data from the repository and delegate to domain balance computation."""
    leave_types_raw = await repository.list_leave_types(limit=100)
    if not leave_types_raw:
        leave_types_raw = DEFAULT_LEAVE_TYPES
    normalized = [
        normalize_leave_type_record(lt)
        for lt in leave_types_raw
        if lt.get("is_active", True)
    ]
    applicable = [
        lt for lt in normalized
        if employment_type_code in (lt.get("applicable_employment_types") or [])
    ]

    account = await repository.find_leave_account(employee_id)
    year = date.today().year
    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)

    year_used: dict[str, float] = {}
    total_used: dict[str, float] = {}
    for lt in applicable:
        code = lt.get("leave_code") or lt.get("code")
        is_accumulative = lt.get("is_accumulative", False)
        has_lifetime_cap = lt.get("max_days_lifetime") is not None

        if is_accumulative and code in ("EL", "HPL") and not account:
            records = await repository.list_sanctioned_leave_applications(
                employee_id=employee_id, leave_type_code=code, limit=10000,
            )
            total_used[code] = compute_used_days_total(records)
        elif has_lifetime_cap:
            records = await repository.list_sanctioned_leave_applications(
                employee_id=employee_id, leave_type_code=code, limit=10000,
            )
            total_used[code] = compute_used_days_total(records)
        elif code == "CL" or (not is_accumulative and code not in ("CML", "LND")):
            records = await repository.list_sanctioned_leave_applications_for_year(
                employee_id=employee_id, leave_type_code=code,
                year_start_iso=year_start.isoformat(), year_end_iso=year_end.isoformat(),
                limit=5000,
            )
            year_used[code] = compute_used_days_from_records(records, year_start, year_end)

    return compute_leave_balances(
        leave_types=normalized,
        employment_type_code=employment_type_code,
        account=account,
        service_start_date=service_start_date,
        year_used=year_used,
        total_used=total_used,
    )


async def _build_initial_leave_account(
    repository: LeaveRuntimeRepository,
    *,
    employee_id: str,
    user_id: str,
    find_employee_profile_func=_find_employee_profile,
    fetch_leave_balances_func=_fetch_leave_balances,
) -> dict[str, Any]:
    account = new_empty_account(employee_id, user_id)

    try:
        profile = await find_employee_profile_func(repository, employee_id)
    except AttributeError:
        return account
    if not profile:
        return account

    employment_type_code = normalize_employment_type_code(
        profile.get("employment_type") or profile.get("employment_type_code")
    )
    if not employment_type_code:
        return account

    try:
        balances = await fetch_leave_balances_func(
            repository,
            employee_id,
            employment_type_code,
            service_start_date=await _resolve_service_start_date(
                repository,
                employee_id=employee_id,
                profile=profile,
            ),
        )
    except AttributeError:
        return account

    initial_balances: dict[str, float] = {}
    for leave_code, balance_field in {
        "EL": "earned_leave_balance",
        "HPL": "half_pay_leave_balance",
        "CML": "commuted_leave_balance",
        "LND": "leave_not_due_balance",
        "CL": "casual_leave_balance",
    }.items():
        available = (balances.get(leave_code) or {}).get("available_days")
        if available is None:
            continue
        initial_balances[balance_field] = float(available)

    return new_empty_account(
        employee_id,
        user_id,
        initial_balances=initial_balances,
    )


async def _record_leave_debit(
    repository: LeaveRuntimeRepository,
    db,
    *,
    employee_id: str,
    leave_type_code: str,
    from_date: str,
    to_date: str,
    days: float,
    user_id: str,
    available_days: float | None = None,
    order_number: str | None = None,
    order_date: str | None = None,
    remarks: str | None = None,
    session=None,
    append_revision_func=None,
    find_employee_profile_func=_find_employee_profile,
    fetch_leave_balances_func=_fetch_leave_balances,
) -> None:
    if append_revision_func is None:
        raise RuntimeError("append_revision_func is required")

    account = await repository.find_leave_account(employee_id)
    account_exists = account is not None
    if not account_exists:
        account = await _build_initial_leave_account(
            repository,
            employee_id=employee_id,
            user_id=user_id,
            find_employee_profile_func=find_employee_profile_func,
            fetch_leave_balances_func=fetch_leave_balances_func,
        )

    policy_defaults = get_leave_policy_defaults(leave_type_code)
    balance_strategy = policy_defaults.get("balance_strategy")
    debit_multiplier = float(policy_defaults.get("debit_multiplier") or 1.0)
    debit_source_leave_code = policy_defaults.get("debit_source_leave_code")
    display_opening = opening_balance_for(account, leave_type_code)
    if available_days is not None and balance_strategy in {"annual_cap", "hpl_half", "lifetime_cap"}:
        display_opening = float(available_days)
    if leave_type_code == "CL" and available_days is not None:
        display_opening = float(available_days)

    source_leave_code = debit_source_leave_code or leave_type_code
    source_opening = opening_balance_for(account, source_leave_code)
    if source_leave_code == "CL" and available_days is not None:
        source_opening = float(available_days)
    source_closing = source_opening - (days * debit_multiplier)
    if policy_defaults.get("debits_leave_account") and source_closing < -0.001:
        raise HTTPException(status_code=400, detail="Insufficient leave balance at sanction time")

    try:
        transaction, closing = build_debit_transaction(
            leave_type_code=leave_type_code,
            from_date=from_date,
            to_date=to_date,
            days=days,
            opening_balance=display_opening,
            user_id=user_id,
            days_debited=days * debit_multiplier,
            debit_source_leave_type=source_leave_code if source_leave_code != leave_type_code else None,
            order_number=order_number,
            order_date=order_date,
            remarks=remarks,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    balance_updates: dict[str, float] = {}
    if leave_type_code == "CML":
        balance_updates["half_pay_leave_balance"] = source_closing
        balance_updates["commuted_leave_balance"] = closing
    elif leave_type_code == "LND":
        balance_updates["leave_not_due_balance"] = closing
    else:
        balance_field = {
            "EL": "earned_leave_balance",
            "HPL": "half_pay_leave_balance",
            "CL": "casual_leave_balance",
        }.get(source_leave_code)
        if balance_field:
            balance_updates[balance_field] = source_closing
    update_fields = build_account_update(
        transaction,
        from_date,
        leave_type_code,
        balance_updates=balance_updates,
    )

    if not account_exists:
        await call_with_optional_session(
            repository.insert_leave_account,
            account,
            session=session,
        )
    await call_with_optional_session(
        repository.update_leave_account,
        employee_id,
        update_fields,
        upsert=True,
        session=session,
    )
    await call_with_optional_session(
        append_revision_func,
        db,
        part_code="SB_PART_VI",
        employee_id=employee_id,
        payload={"transaction": transaction, "update": update_fields},
        actor_user_id=user_id,
        session=session,
    )


async def _lock_leave_attachments_if_finalized(
    db,
    leave_doc: dict,
    *,
    document_lock_func=_lock_documents_for_finalized_leave,
) -> None:
    status = str(leave_doc.get("status") or "").upper()
    attachments = leave_doc.get("attachments") or []
    if status not in {"SANCTIONED", "REJECTED"} or not attachments:
        return

    try:
        await document_lock_func(
            attachments,
            leave_id=str(leave_doc.get("id") or ""),
            status=status,
            db=db,
        )
    except Exception:
        logger.exception(
            "Failed to lock attachment metadata after leave finalization",
            extra={
                "leave_id": leave_doc.get("id"),
                "attachment_count": len(attachments),
                "status": status,
            },
        )

