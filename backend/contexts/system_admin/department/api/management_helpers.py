from __future__ import annotations

from typing import Any

from fastapi import HTTPException


def active_query(code: str) -> dict[str, Any]:
    return {
        "code": code,
        "$or": [
            {"is_active": True},
            {"is_active": {"$exists": False}},
        ],
    }


def serialize_department(record: dict[str, Any]) -> dict[str, Any]:
    metadata = record.get("metadata") or {}
    return {
        "id": record.get("id", ""),
        "code": record.get("code", ""),
        "name": record.get("name", ""),
        "description": record.get("description"),
        "hod_employee_id": metadata.get("hod_employee_id"),
        "data_entry_employee_id": metadata.get("data_entry_employee_id"),
        "assigned_authorities": metadata.get("assigned_authorities", []),
        "is_active": record.get("is_active", True),
        "created_at": record.get("created_at"),
        "created_by": record.get("created_by"),
        "updated_at": record.get("updated_at"),
        "updated_by": record.get("updated_by"),
    }


def normalize_employee_ref(value: str | None) -> str | None:
    return (value or "").strip() or None


def ensure_distinct_role_holders(*, hod_employee_id: str | None, data_entry_employee_id: str | None) -> None:
    if hod_employee_id and data_entry_employee_id and hod_employee_id == data_entry_employee_id:
        raise HTTPException(
            status_code=400,
            detail="The same employee cannot hold both HOD and Data Entry Operator roles in a department.",
        )


def build_department_metadata(
    *,
    hod_employee_id: str | None,
    data_entry_employee_id: str | None,
) -> dict[str, Any]:
    assigned_authorities: list[str] = []
    if hod_employee_id:
        assigned_authorities.append("HOD")
    if data_entry_employee_id:
        assigned_authorities.append("DEPT_DATA_ENTRY")

    return {
        "hod_employee_id": hod_employee_id,
        "data_entry_employee_id": data_entry_employee_id,
        "assigned_authorities": assigned_authorities,
        "allowed_authorities": assigned_authorities,
    }
