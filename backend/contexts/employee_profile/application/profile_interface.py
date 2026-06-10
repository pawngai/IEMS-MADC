from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from contexts.employee_profile.domain.employment_rules import is_regular_employee
from contexts.employee_profile.domain.identity_layers import (
    compose_employee_record_view,
)


def _has_collection(db, name: str) -> bool:
    return getattr(db, name, None) is not None


async def get_employee_identity(
    db,
    *,
    employee_id: str,
    projection: dict | None = None,
) -> dict[str, Any] | None:
    if not _has_collection(db, "employee_identities"):
        return None
    return await db.employee_identities.find_one(
        {"employee_id": employee_id},
        projection or {"_id": 0},
    )


async def get_employee_profile(
    db,
    *,
    employee_id: str,
    projection: dict | None = None,
) -> dict[str, Any] | None:
    identity = await get_employee_identity(
        db,
        employee_id=employee_id,
        projection={"_id": 0},
    )

    extension: dict[str, Any] | None = None
    if _has_collection(db, "employee_profile_extensions"):
        extension = await db.employee_profile_extensions.find_one(
            {"employee_id": employee_id},
            {"_id": 0},
        )

    profile = compose_employee_record_view(identity, extension)
    if not profile:
        return None
    if projection and projection != {"_id": 0}:
        return {key: value for key, value in profile.items() if key in projection}
    return profile


async def get_employee_profile_view(
    db,
    *,
    employee_id: str,
    projection: dict | None = None,
) -> dict[str, Any] | None:
    if _has_collection(db, "employee_profile_read_models"):
        projected = await db.employee_profile_read_models.find_one(
            {"employee_id": employee_id},
            projection or {"_id": 0},
        )
        if projected:
            return projected
    composed = await get_employee_profile(
        db,
        employee_id=employee_id,
        projection=projection,
    )
    if composed:
        return composed
    return None


async def _list_employee_ids_for_field(
    collection,
    *,
    field_name: str,
    value: str,
    limit: int,
) -> list[str]:
    cursor = collection.find(
        {field_name: value},
        {"_id": 0, "employee_id": 1},
    )
    rows = await cursor.to_list(length=limit)
    return [str(row.get("employee_id")) for row in rows if row.get("employee_id")]


async def require_employee_profile(
    db,
    *,
    employee_id: str,
    projection: dict | None = None,
) -> dict[str, Any]:
    profile = await get_employee_profile_view(
        db,
        employee_id=employee_id,
        projection=projection,
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    return profile


async def resolve_employee_department_code(db, *, employee_id: str) -> str | None:
    profile = await get_employee_profile_view(
        db,
        employee_id=employee_id,
        projection={"_id": 0, "current_department_id": 1},
    )
    if profile and profile.get("current_department_id"):
        return str(profile["current_department_id"]).strip().upper()

    identity = await get_employee_identity(
        db,
        employee_id=employee_id,
        projection={"_id": 0, "current_department_id": 1},
    )
    if not identity:
        return None
    value = identity.get("current_department_id")
    if not value:
        return None
    return str(value).strip().upper()


def is_service_book_eligible_employee(employee_or_type: Any) -> bool:
    return is_regular_employee(employee_or_type)


def require_service_book_eligible_employee(employee_or_type: Any) -> None:
    if is_service_book_eligible_employee(employee_or_type):
        return
    raise HTTPException(
        status_code=403,
        detail={
            "error": "Service Book not applicable",
            "message": "Service Book is only maintained for REGULAR employees.",
            "required_employment_type": "REGULAR",
        },
    )


async def apply_employee_profile_updates(
    db,
    *,
    employee_id: str,
    updates: dict,
    session=None,
) -> None:
    if not _has_collection(db, "employee_profile_extensions"):
        raise RuntimeError(
            "employee_profile_extensions collection is required after the identity split cutover"
        )

    set_fields: dict[str, Any] = {}
    for key, value in updates.items():
        if key in {"mobile_primary", "mobile_alternate", "email_personal", "email_official", "address_line1", "address_line2", "city", "district", "state", "pincode", "present_address_line1", "present_address_line2", "present_city", "present_district", "present_state", "present_pincode", "emergency_name", "emergency_phone", "emergency_relation"}:
            set_fields[f"contact.{key}"] = value
        elif key in {"aadhaar_number", "pan_number"}:
            set_fields[f"identifiers.{key}"] = value
        else:
            set_fields[key] = value
    await db.employee_profile_extensions.update_one(
        {"employee_id": employee_id},
        {"$set": set_fields},
        upsert=True,
        session=session,
    )
    if _has_collection(db, "employee_profile_read_models"):
        profile = await get_employee_profile(db, employee_id=employee_id, projection={"_id": 0})
        if profile:
            await db.employee_profile_read_models.update_one(
                {"employee_id": employee_id},
                {"$set": {**profile, "read_model_updated_at": updates.get("updated_at")}},
                upsert=True,
                session=session,
            )


async def list_employee_ids_by_department(
    db,
    *,
    department_code: str,
    limit: int = 5000,
) -> list[str]:
    normalized_dept = str(department_code or "").strip().upper()
    if not normalized_dept:
        return []

    results: list[str] = []
    seen: set[str] = set()
    for collection_name in (
        "employee_profile_read_models",
        "employee_profile_extensions",
        "employee_identities",
    ):
        collection = getattr(db, collection_name, None)
        if collection is None:
            continue
        employee_ids = await _list_employee_ids_for_field(
            collection,
            field_name="current_department_id",
            value=normalized_dept,
            limit=limit,
        )
        for employee_id in employee_ids:
            if employee_id in seen:
                continue
            seen.add(employee_id)
            results.append(employee_id)
            if len(results) >= limit:
                return results
    return results
