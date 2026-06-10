from __future__ import annotations

import re
from typing import Any

from fastapi import HTTPException
from app_platform.reference_data.contracts.employment_type_master import (
    list_employment_type_master,
)
from app_platform.reference_data.infrastructure import service as reference_data_service
from contexts.service_book.contracts.service_summary_directory import (
    get_employee_current_department_code,
    list_employee_ids_by_service_summary,
)

from contexts.employee_identity.domain.employment_rules import is_regular_employee
from contexts.employee_identity.repository import EmployeeIdentityRepository


def _repo(db) -> EmployeeIdentityRepository:
    return EmployeeIdentityRepository(db=db)


def _has_collection(db, name: str) -> bool:
    return getattr(db, name, None) is not None


async def _cursor_rows(cursor, *, length: int | None = None) -> list[dict[str, Any]]:
    to_list = getattr(cursor, "to_list", None)
    if callable(to_list):
        return await to_list(length=length)

    rows: list[dict[str, Any]] = []
    async for row in cursor:
        rows.append(row)
        if length is not None and len(rows) >= length:
            break
    return rows


def _sanitize_identity(identity: dict[str, Any] | None) -> dict[str, Any] | None:
    if not identity:
        return None
    sanitized = dict(identity)
    sanitized.pop("aadhaar_number", None)
    return sanitized


def _build_identity_query(
    *,
    search: str | None = None,
    employee_ids: list[str] | None = None,
    status: str | list[str] | tuple[str, ...] | set[str] | None = None,
) -> dict[str, Any]:
    query: dict[str, Any] = {}
    if employee_ids is not None:
        query["employee_id"] = {"$in": employee_ids} if employee_ids else {"$in": []}
    if status:
        if isinstance(status, (list, tuple, set)):
            statuses = [str(item).strip().upper() for item in status if str(item).strip()]
            if statuses:
                query["workflow_status"] = {"$in": statuses}
        else:
            query["workflow_status"] = str(status).strip().upper()
    if search:
        safe_search = re.escape(search)
        query["$or"] = [
            {"full_name": {"$regex": safe_search, "$options": "i"}},
            {"employee_id": {"$regex": safe_search, "$options": "i"}},
            {"employee_code": {"$regex": safe_search, "$options": "i"}},
        ]
    return query


def _dedupe_ids(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = str(value or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


PROFILE_ASSIGNMENT_FIELDS = (
    "employment_type",
    "date_of_initial_engagement",
    "current_department_id",
)


def _merge_profile_assignment_fields(
    identity: dict[str, Any] | None,
    assignment_fields: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not identity:
        return None
    merged = dict(identity)
    for field_name in PROFILE_ASSIGNMENT_FIELDS:
        value = (assignment_fields or {}).get(field_name)
        if value is not None and value != "":
            merged[field_name] = value
    return merged


async def _attach_profile_assignment_fields(db, identities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not identities:
        return identities

    assignment_by_id = await _list_profile_assignment_fields(
        db,
        employee_ids=[str(identity.get("employee_id") or "") for identity in identities],
    )
    return [
        _merge_profile_assignment_fields(
            identity,
            assignment_by_id.get(str(identity.get("employee_id") or "")),
        )
        or {}
        for identity in identities
    ]


async def _legacy_employee_ids_for_filters(
    db,
    *,
    employment_type: str | None = None,
    department_code: str | None = None,
    limit: int = 50000,
) -> list[str]:
    query: dict[str, Any] = {}
    if employment_type:
        query["employment_type"] = str(employment_type).strip().upper()
    if department_code:
        query["current_department_id"] = str(department_code).strip().upper()
    if not query:
        return []
    profile_rows = await list_profiles(
        db,
        employment_type=query.get("employment_type"),
        department_code=query.get("current_department_id"),
        limit=limit,
    )
    legacy_rows = await _repo(db).list_identities(query=query, limit=limit)
    return _dedupe_ids(
        [
            *[str(row.get("employee_id")) for row in profile_rows if row.get("employee_id")],
            *[str(row.get("employee_id")) for row in legacy_rows if row.get("employee_id")],
        ]
    )


async def list_profiles(
    db,
    *,
    employment_type: str | None = None,
    department_code: str | None = None,
    limit: int = 500,
    **_kwargs,
) -> list[dict[str, Any]]:
    query: dict[str, Any] = {}
    if employment_type:
        query["employment_type"] = str(employment_type).strip().upper()
    if department_code:
        query["current_department_id"] = str(department_code).strip().upper()
    if not query:
        return []

    rows_by_id: dict[str, dict[str, Any]] = {}
    for collection_name in ("employee_profile_read_models", "employee_profile_extensions"):
        collection = getattr(db, collection_name, None)
        if collection is None:
            continue
        rows = await _cursor_rows(
            collection.find(
                query,
                {
                    "_id": 0,
                    "employee_id": 1,
                    "employment_type": 1,
                    "date_of_initial_engagement": 1,
                    "current_department_id": 1,
                },
            ),
            length=limit,
        )
        for row in rows:
            employee_id = str(row.get("employee_id") or "").strip()
            if not employee_id:
                continue
            rows_by_id.setdefault(employee_id, {"employee_id": employee_id})
            rows_by_id[employee_id].update(
                {
                    key: value
                    for key, value in row.items()
                    if key != "employee_id" and value is not None and value != ""
                }
            )
            if len(rows_by_id) >= limit:
                return list(rows_by_id.values())
    return list(rows_by_id.values())


async def _list_profile_assignment_fields(
    db,
    *,
    employee_ids: list[str],
) -> dict[str, dict[str, Any]]:
    ids = [str(employee_id).strip() for employee_id in employee_ids if str(employee_id or "").strip()]
    if not ids:
        return {}

    projection = {
        "_id": 0,
        "employee_id": 1,
        "employment_type": 1,
        "date_of_initial_engagement": 1,
        "current_department_id": 1,
    }
    remaining_ids = list(dict.fromkeys(ids))
    assignment_by_id: dict[str, dict[str, Any]] = {}

    for collection_name in (
        "employee_profile_read_models",
        "employee_profile_extensions",
    ):
        collection = getattr(db, collection_name, None)
        if collection is None or not remaining_ids:
            continue
        find = getattr(collection, "find", None)
        if callable(find):
            rows = await _cursor_rows(
                find(
                    {"employee_id": {"$in": remaining_ids}},
                    projection,
                ),
                length=len(remaining_ids),
            )
        else:
            find_one = getattr(collection, "find_one", None)
            if not callable(find_one):
                continue
            rows = []
            for employee_id in remaining_ids:
                row = await find_one(
                    {"employee_id": employee_id},
                    projection,
                )
                if row:
                    rows.append(row)
        matched_ids: set[str] = set()
        for row in rows:
            employee_id = str(row.get("employee_id") or "").strip()
            if not employee_id:
                continue
            assignment_by_id.setdefault(employee_id, {})
            for field_name in PROFILE_ASSIGNMENT_FIELDS:
                value = row.get(field_name)
                if value is not None and value != "":
                    assignment_by_id[employee_id][field_name] = value
            matched_ids.add(employee_id)
        if matched_ids:
            remaining_ids = [employee_id for employee_id in remaining_ids if employee_id not in matched_ids]

    return assignment_by_id


async def _find_profile_assignment_view(
    db,
    *,
    employee_id: str,
) -> dict[str, Any] | None:
    if not employee_id:
        return None
    assignment_by_id = await _list_profile_assignment_fields(db, employee_ids=[employee_id])
    assignment_fields = assignment_by_id.get(employee_id)
    if not assignment_fields:
        return None
    return {
        "employee_id": employee_id,
        **assignment_fields,
    }


async def _list_profile_employee_ids_for_filters(
    db,
    *,
    employment_type: str | None = None,
    department_code: str | None = None,
    limit: int = 50000,
) -> list[str]:
    rows = await list_profiles(
        db,
        employment_type=employment_type,
        department_code=department_code,
        limit=limit,
    )
    return [str(row.get("employee_id")) for row in rows if row.get("employee_id")]


async def _employee_ids_for_service_filters(
    db,
    *,
    employment_type: str | None = None,
    department_code: str | None = None,
    limit: int = 50000,
) -> list[str]:
    summary_ids = await list_employee_ids_by_service_summary(
        db,
        employment_type=employment_type,
        department_code=department_code,
        limit=limit,
    )
    legacy_ids = await _legacy_employee_ids_for_filters(
        db,
        employment_type=employment_type,
        department_code=department_code,
        limit=limit,
    )
    return _dedupe_ids([*summary_ids, *legacy_ids])


async def get_employee_identity(
    db,
    *,
    employee_id: str,
    projection: dict | None = None,
) -> dict[str, Any] | None:
    identity = await _repo(db).get_identity(employee_id=employee_id, projection=projection)
    if not identity:
        proj = projection or {"_id": 0}
        identity = await db.employee_identities.find_one({"employee_code": employee_id}, proj)
    identity = _sanitize_identity(identity)
    if not identity:
        return None

    profile_view = await _find_profile_assignment_view(
        db,
        employee_id=str(identity.get("employee_id") or employee_id),
    )
    return _merge_profile_assignment_fields(identity, profile_view)


async def require_employee_identity(
    db,
    *,
    employee_id: str,
    projection: dict | None = None,
) -> dict[str, Any]:
    identity = await get_employee_identity(
        db,
        employee_id=employee_id,
        projection=projection,
    )
    if not identity:
        raise HTTPException(status_code=404, detail="Employee identity not found")
    return identity


async def resolve_employee_department_code(db, *, employee_id: str) -> str | None:
    summary_department = await get_employee_current_department_code(db, employee_id=employee_id)
    if summary_department:
        return summary_department

    profile_view = await _find_profile_assignment_view(db, employee_id=employee_id)
    value = (profile_view or {}).get("current_department_id")
    if value:
        return str(value).strip().upper()

    identity = await _repo(db).get_identity(
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


async def list_employee_ids_by_department(
    db,
    *,
    department_code: str,
    limit: int = 5000,
) -> list[str]:
    normalized_dept = str(department_code or "").strip().upper()
    if not normalized_dept:
        return []
    summary_ids = await list_employee_ids_by_service_summary(
        db,
        department_code=normalized_dept,
        limit=limit,
    )
    legacy_ids = await _legacy_employee_ids_for_filters(
        db,
        department_code=normalized_dept,
        limit=limit,
    )
    return _dedupe_ids([*summary_ids, *legacy_ids])[:limit]


async def list_employee_identities(
    db,
    *,
    search: str | None = None,
    employment_type: str | None = None,
    department_code: str | None = None,
    status: str | list[str] | tuple[str, ...] | set[str] | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[dict[str, Any]]:
    employee_ids = None
    if employment_type or department_code:
        employee_ids = await _employee_ids_for_service_filters(
            db,
            employment_type=employment_type,
            department_code=department_code,
            limit=50000,
        )
    identities = await _repo(db).list_identities(
        query=_build_identity_query(
            search=search,
            employee_ids=employee_ids,
            status=status,
        ),
        skip=skip,
        limit=limit,
    )
    return await _attach_profile_assignment_fields(db, identities)


async def get_employee_name_map(
    db,
    *,
    employee_ids: list[str],
) -> dict[str, str]:
    if not employee_ids:
        return {}
    identities = await _repo(db).list_identities(
        query={"employee_id": {"$in": employee_ids}},
        limit=max(len(employee_ids), 1),
    )
    return {
        doc["employee_id"]: doc.get("full_name", doc["employee_id"])
        for doc in identities
        if doc.get("employee_id")
    }


async def count_employee_identities(
    db,
    *,
    search: str | None = None,
    employment_type: str | None = None,
    department_code: str | None = None,
    status: str | list[str] | tuple[str, ...] | set[str] | None = None,
) -> int:
    employee_ids = None
    if employment_type or department_code:
        employee_ids = await _employee_ids_for_service_filters(
            db,
            employment_type=employment_type,
            department_code=department_code,
            limit=50000,
        )
    return await _repo(db).count_identities(
        query=_build_identity_query(
            search=search,
            employee_ids=employee_ids,
            status=status,
        )
    )


async def get_identity_editor_bootstrap(db) -> dict[str, Any]:
    departments = await reference_data_service.get_departments(db)
    designations = await reference_data_service.get_designations(db)
    employment_types = [
        {
            **record,
            "label": record["name"],
            "description": record["name"],
        }
        for record in list_employment_type_master()
    ]
    return {
        "departments": departments,
        "designations": designations,
        "employment_types": employment_types,
    }
