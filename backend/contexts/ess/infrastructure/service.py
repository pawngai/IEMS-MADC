"""
ESS (Employee Self-Service) Portal - Business logic / service layer.

Handles permission checks, data aggregation, and delegates to repo.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from contexts.ess.infrastructure import repo
from contexts.identity_access.contracts.models import Permission
from contexts.identity_access.contracts.access_control import require_permissions
from app_platform.reference_data.contracts.employment_rules import (
    get_available_service_book_parts,
)
from contexts.employee_master.contracts.employee_domain import (
    determineEmploymentType,
    isServiceBookEligible,
    normalizeEmployeeRecord,
    updateEmployeeStatus,
)
from contexts.leave_attendance.contracts.leave_commands import ensure_initial_leave_account
from contexts.service_book.contracts.servicebook.part_constants import SB_LEDGER_PART_KEY_BY_ROMAN


SERVICE_BOOK_VISIBLE_STATUSES = ["APPROVED", "LOCKED"]

ESS_EDITABLE_FIELDS = {
    "father_name",
    "mother_name",
    "religion",
    "blood_group",
    "category",
    "marital_status",
    "spouse_name",
    "mobile_primary",
    "mobile_alternate",
    "email_personal",
    "email_official",
    "emergency_name",
    "emergency_phone",
    "emergency_relation",
    "address_line1",
    "address_line2",
    "city",
    "district",
    "state",
    "pincode",
    "present_address_line1",
    "present_address_line2",
    "present_city",
    "present_district",
    "present_state",
    "present_pincode",
    "mobile_number",
    "personal_email",
    "alternate_mobile",
    "emergency_contact_name",
    "emergency_contact_number",
    "current_address_line1",
    "current_address_line2",
    "current_city",
    "current_state_code",
    "current_pincode",
    "aadhaar_number",
    "pan_number",
    "photo_url",
}

AUTO_EMPLOYEE_COMPLETION_FIELDS = {
    "mobile_primary",
    "email_personal",
    "address_line1",
    "city",
    "state",
    "pincode",
    "present_address_line1",
    "present_city",
    "present_state",
    "present_pincode",
}

_FIELD_NAME_ALIASES: dict[str, str] = {
    "mobile_number": "mobile_primary",
    "alternate_mobile": "mobile_alternate",
    "personal_email": "email_personal",
    "emergency_contact_name": "emergency_name",
    "emergency_contact_number": "emergency_phone",
    "emergency_contact_phone": "emergency_phone",
    "emergency_contact_relation": "emergency_relation",
    "current_address_line1": "address_line1",
    "current_address_line2": "address_line2",
    "current_city": "city",
    "current_state_code": "state",
    "current_pincode": "pincode",
}


def _normalize_field_names(updates: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in updates.items():
        canonical = _FIELD_NAME_ALIASES.get(key, key)
        if canonical in out and key in _FIELD_NAME_ALIASES:
            continue
        out[canonical] = value
    return out


def _get_employee_id(current_user: dict) -> str:
    employee_id = current_user.get("employee_id")
    if not employee_id:
        raise HTTPException(
            status_code=400, detail="No employee profile linked to your account"
        )
    return employee_id


def _has_completion_value(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    return value not in (None, False)


def _get_profile_value(profile: dict[str, Any], field: str) -> Any:
    return (
        profile.get(field)
        or (profile.get("contact") or {}).get(field)
        or (profile.get("identifiers") or {}).get(field)
    )


def _derive_employee_section_completed(profile: dict[str, Any]) -> bool:
    return all(
        _has_completion_value(_get_profile_value(profile, field))
        for field in AUTO_EMPLOYEE_COMPLETION_FIELDS
    )


async def get_my_profile(db, *, current_user: dict) -> dict[str, Any]:
    employee_id = _get_employee_id(current_user)
    profile = await repo.find_profile(db, employee_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return normalizeEmployeeRecord(profile)


async def update_my_contact(
    db, updates: dict[str, Any], *, current_user: dict
) -> dict[str, Any]:
    require_permissions(current_user, Permission.PROFILE_UPDATE_OWN_LIMITED)

    employee_id = _get_employee_id(current_user)

    profile = await repo.find_profile(db, employee_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    safe_updates = {k: v for k, v in updates.items() if k in ESS_EDITABLE_FIELDS}
    if not safe_updates:
        raise HTTPException(
            status_code=400, detail="No valid ESS-editable fields provided"
        )

    safe_updates = _normalize_field_names(safe_updates)
    safe_updates.pop("employee_section_completed", None)

    projected_profile = dict(profile)
    projected_contact = dict(profile.get("contact") or {})
    projected_contact.update({key: value for key, value in safe_updates.items() if key in ESS_EDITABLE_FIELDS})
    projected_profile.update(safe_updates)
    projected_profile["contact"] = projected_contact
    safe_updates["employee_section_completed"] = _derive_employee_section_completed(projected_profile)

    safe_updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    safe_updates["updated_by"] = current_user.get("sub") or current_user.get("id", "")

    await repo.update_profile_contact(db, employee_id, safe_updates)

    return {
        "message": "Contact information updated",
        "updated_fields": list(safe_updates.keys()),
        "employee_id": employee_id,
    }


async def get_my_service_book(db, *, current_user: dict) -> dict[str, Any]:
    require_permissions(current_user, Permission.SERVICE_BOOK_READ_OWN)

    employee_id = _get_employee_id(current_user)

    profile = await repo.find_profile(db, employee_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    employment_type = determineEmploymentType(profile)
    if not isServiceBookEligible(employment_type):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Service Book not applicable",
                "message": "Service Book access is allowed only for employment types with Service Book coverage.",
                "employment_type": employment_type,
            },
        )

    available_parts = get_available_service_book_parts(employment_type)
    result: dict[str, Any] = {
        "employee_id": employee_id,
        "employee_name": profile.get("full_name"),
        "available_parts": available_parts,
        "parts": {},
    }

    projected_entries = await repo.list_projected_service_book_entries(
        db,
        employee_id,
        statuses=SERVICE_BOOK_VISIBLE_STATUSES,
    )
    ledger_entries = projected_entries
    roman_by_part_key = {value: key for key, value in SB_LEDGER_PART_KEY_BY_ROMAN.items()}
    for entry in ledger_entries:
        part_key = entry.get("part_key") or entry.get("part_code")
        roman_part = roman_by_part_key.get(part_key or "")
        if not roman_part or roman_part not in available_parts:
            continue
        payload = dict(entry.get("payload") or {})
        payload["id"] = entry.get("id") or entry.get("entry_id")
        payload["schema_key"] = entry.get("schema_key")
        payload["status"] = entry.get("status") or entry.get("workflow_state")
        payload["workflow_state"] = entry.get("workflow_state") or entry.get("status")
        result["parts"].setdefault(roman_part, []).append(payload)

    for part in available_parts:
        if result["parts"].get(part):
            continue
        part_data = await repo.get_projected_service_book_part(db, employee_id, part)
        if part_data:
            result["parts"][part] = part_data

    return result


async def get_my_leaves(db, *, current_user: dict) -> list[dict[str, Any]]:
    require_permissions(current_user, Permission.LEAVE_READ_OWN)
    employee_id = _get_employee_id(current_user)
    return await repo.list_leave_applications(db, employee_id)


async def get_my_leave_balances(db, *, current_user: dict) -> dict[str, Any]:
    require_permissions(current_user, Permission.LEAVE_READ_OWN)
    employee_id = _get_employee_id(current_user)
    await ensure_initial_leave_account(
        db,
        employee_id=employee_id,
        user_id=current_user.get("sub"),
    )
    return await repo.get_leave_balances(db, employee_id)


async def get_my_documents(
    db,
    *,
    current_user: dict,
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
    require_permissions(current_user, Permission.DOCUMENT_READ_OWN)
    employee_id = _get_employee_id(current_user)
    employee_code = str(current_user.get("employee_code") or "").strip() or None
    return await repo.list_subject_documents(
        db,
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
    )


async def download_my_document(filename: str, db, *, current_user: dict):
    require_permissions(current_user, Permission.DOCUMENT_READ_OWN)
    employee_id = _get_employee_id(current_user)
    employee_code = str(current_user.get("employee_code") or "").strip() or None
    return await repo.download_subject_document(
        db,
        filename=filename,
        employee_id=employee_id,
        employee_code=employee_code,
    )


async def get_my_document(filename: str, db, *, current_user: dict):
    require_permissions(current_user, Permission.DOCUMENT_READ_OWN)
    employee_id = _get_employee_id(current_user)
    employee_code = str(current_user.get("employee_code") or "").strip() or None
    return await repo.get_subject_document(
        db,
        filename=filename,
        employee_id=employee_id,
        employee_code=employee_code,
    )


async def get_dashboard(db, *, current_user: dict) -> dict[str, Any]:
    employee_id = _get_employee_id(current_user)

    profile = await repo.find_profile(db, employee_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    pending_leaves = await repo.count_leaves_by_status(db, employee_id, "SUBMITTED")
    recommended_leaves = await repo.count_leaves_by_status(
        db, employee_id, "RECOMMENDED"
    )
    sanctioned_leaves = await repo.count_leaves_by_status(db, employee_id, "SANCTIONED")

    sb_count = 0
    employment_type = profile.get("employment_type") or profile.get(
        "employment_type_code"
    )
    if isServiceBookEligible(employment_type):
        sb_count = await repo.count_projected_service_book_entries(
            db,
            employee_id,
            statuses=SERVICE_BOOK_VISIBLE_STATUSES,
        )

    normalized_profile = updateEmployeeStatus(profile)

    unread = await repo.count_unread_notifications(db, employee_id)

    return {
        "employee_id": employee_id,
        "full_name": profile.get("full_name"),
        "employee_status": normalized_profile.get("employee_status"),
        "service_status": normalized_profile.get("service_status"),
        "workflow_status": normalized_profile.get("workflow_status"),
        "department": profile.get("current_department_id"),
        "designation": profile.get("current_designation_id"),
        "service_book_entries": sb_count,
        "leave_stats": {
            "pending": pending_leaves,
            "recommended": recommended_leaves,
            "sanctioned": sanctioned_leaves,
        },
        "notifications_unread": unread,
    }


async def get_notifications(db, *, current_user: dict) -> dict[str, Any]:
    employee_id = _get_employee_id(current_user)

    notifications = await repo.list_notifications(db, employee_id)
    unread = sum(1 for n in notifications if not n.get("read"))

    derived = await _derive_notifications(db, employee_id)
    all_notifications = derived + notifications

    all_notifications.sort(key=lambda n: n.get("timestamp", ""), reverse=True)

    return {
        "notifications": all_notifications,
        "unread_count": unread + sum(1 for n in derived if not n.get("read")),
    }


async def mark_notification_read(
    db, notification_id: str, *, current_user: dict
) -> dict[str, Any]:
    _get_employee_id(current_user)
    await repo.mark_notification_read(db, notification_id)
    return {"message": "Notification marked as read", "id": notification_id}


async def _derive_notifications(db, employee_id: str) -> list[dict[str, Any]]:
    notifications = []
    now = datetime.now(timezone.utc).isoformat()

    profile = await repo.find_profile(db, employee_id)
    if profile:
        ws = normalizeEmployeeRecord(profile).get("workflow_status", "DRAFT")
        if ws == "REJECTED":
            notifications.append(
                {
                    "id": f"derived-profile-rejected-{employee_id}",
                    "type": "PROFILE_STATUS",
                    "title": "Profile Rejected",
                    "message": "Your profile was rejected. Please review and resubmit.",
                    "level": "error",
                    "timestamp": profile.get("updated_at", now),
                    "read": False,
                    "action_url": "/ess/profile",
                }
            )
        elif ws == "DRAFT":
            notifications.append(
                {
                    "id": f"derived-profile-draft-{employee_id}",
                    "type": "PROFILE_STATUS",
                    "title": "Profile Incomplete",
                    "message": "Your profile is in DRAFT status. Complete and submit for review.",
                    "level": "warning",
                    "timestamp": profile.get("updated_at", now),
                    "read": False,
                    "action_url": "/ess/profile",
                }
            )
        elif ws == "LOCKED":
            notifications.append(
                {
                    "id": f"derived-profile-locked-{employee_id}",
                    "type": "PROFILE_STATUS",
                    "title": "Profile Verified",
                    "message": "Your profile has been fully locked.",
                    "level": "success",
                    "timestamp": profile.get("updated_at", now),
                    "read": True,
                }
            )

    leaves = await repo.list_leave_applications(db, employee_id, limit=10)
    for leave in leaves:
        if leave.get("status") == "REJECTED":
            notifications.append(
                {
                    "id": f"derived-leave-rejected-{leave.get('id', '')}",
                    "type": "LEAVE_STATUS",
                    "title": "Leave Rejected",
                    "message": f"Your leave application ({leave.get('from_date', '')} - {leave.get('to_date', '')}) was rejected.",
                    "level": "error",
                    "timestamp": leave.get("rejected_at")
                    or leave.get("applied_at", now),
                    "read": False,
                    "action_url": "/ess/leave",
                }
            )
        elif leave.get("status") == "SANCTIONED":
            notifications.append(
                {
                    "id": f"derived-leave-sanctioned-{leave.get('id', '')}",
                    "type": "LEAVE_STATUS",
                    "title": "Leave Sanctioned",
                    "message": f"Your leave ({leave.get('from_date', '')} - {leave.get('to_date', '')}) has been sanctioned.",
                    "level": "success",
                    "timestamp": leave.get("sanctioned_at")
                    or leave.get("applied_at", now),
                    "read": True,
                }
            )

    return notifications
