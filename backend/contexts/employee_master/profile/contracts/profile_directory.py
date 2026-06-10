from __future__ import annotations

import re
from typing import Any

from contexts.employee_master.profile.application.profile_interface import (
    get_employee_profile,
    get_employee_profile_view,
    list_employee_ids_by_department,
    require_employee_profile,
    resolve_employee_department_code,
)
from contexts.employee_master.profile.contracts.workflow_status_utils import workflow_status_filter_values


async def find_profile(
    db,
    *,
    employee_id: str,
    projection: dict | None = None,
) -> dict[str, Any] | None:
    return await get_employee_profile(
        db,
        employee_id=employee_id,
        projection=projection,
    )


async def find_profile_view(
    db,
    *,
    employee_id: str,
    projection: dict | None = None,
) -> dict[str, Any] | None:
    return await get_employee_profile_view(
        db,
        employee_id=employee_id,
        projection=projection,
    )


async def list_profile_workflow_statuses(
    db,
    *,
    employee_ids: list[str],
) -> dict[str, str]:
    ids = [str(employee_id).strip() for employee_id in employee_ids if str(employee_id or "").strip()]
    if not ids or not _has_collection(db, "employee_profile_read_models"):
        return {}

    rows = await db.employee_profile_read_models.find(
        {"employee_id": {"$in": ids}},
        {"_id": 0, "employee_id": 1, "workflow_status": 1},
    ).to_list(length=len(ids))

    statuses: dict[str, str] = {}
    for row in rows:
        employee_id = str(row.get("employee_id") or "").strip()
        workflow_status = str(row.get("workflow_status") or "").strip().upper()
        if employee_id and workflow_status:
            statuses[employee_id] = workflow_status
    return statuses


async def list_profile_assignment_fields(
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
        "employee_identities",
    ):
        collection = getattr(db, collection_name, None)
        if collection is None or not remaining_ids:
            continue
        rows = await collection.find(
            {"employee_id": {"$in": remaining_ids}},
            projection,
        ).to_list(length=len(remaining_ids))
        matched_ids: set[str] = set()
        for row in rows:
            employee_id = str(row.get("employee_id") or "").strip()
            if not employee_id:
                continue
            assignment_by_id.setdefault(employee_id, {})
            for field_name in ("employment_type", "date_of_initial_engagement", "current_department_id"):
                value = row.get(field_name)
                if value is not None and value != "":
                    assignment_by_id[employee_id][field_name] = value
            matched_ids.add(employee_id)
        if matched_ids:
            remaining_ids = [employee_id for employee_id in remaining_ids if employee_id not in matched_ids]

    return assignment_by_id


async def require_profile_view(
    db,
    *,
    employee_id: str,
    projection: dict | None = None,
) -> dict[str, Any]:
    return await require_employee_profile(
        db,
        employee_id=employee_id,
        projection=projection,
    )


async def get_employee_department_code(db, *, employee_id: str) -> str | None:
    return await resolve_employee_department_code(db, employee_id=employee_id)


def _has_collection(db, name: str) -> bool:
    return getattr(db, name, None) is not None


async def _find_profile_extension(db, *, employee_id: str) -> dict[str, Any] | None:
    if not _has_collection(db, "employee_profile_extensions"):
        return None
    return await db.employee_profile_extensions.find_one(
        {"employee_id": employee_id},
        {"_id": 0},
    )


def _profiles_collection(db):
    read_models = getattr(db, "employee_profile_read_models", None)
    if read_models is not None:
        return read_models

    identities = getattr(db, "employee_identities", None)
    if identities is not None:
        return identities

    raise AttributeError("Database handle is missing employee profile collections")


async def _count_matching_rows(collection, query: dict[str, Any]) -> int:
    return int(await collection.count_documents(query))


async def _list_matching_rows(
    collection,
    query: dict[str, Any],
    *,
    offset: int,
    limit: int,
    sort_by: str | None = None,
    sort_dir: str = "asc",
) -> list[dict[str, Any]]:
    direction = 1 if sort_dir == "asc" else -1
    cursor = collection.find(query, {"_id": 0}).sort(sort_by or "full_name", direction).skip(offset).limit(limit)
    return await cursor.to_list(limit)


def _identity_fallback_query(profile_query: dict[str, Any]) -> dict[str, Any] | None:
    query = dict(profile_query or {})
    requested_workflow = query.pop("workflow_status", None)
    if requested_workflow is not None:
        if isinstance(requested_workflow, dict):
            values = {str(value).strip().upper() for value in requested_workflow.get("$in", [])}
            if "DRAFT" not in values:
                return None
        elif str(requested_workflow).strip().upper() != "DRAFT":
            return None
    query["workflow_status"] = "ACTIVE"
    return query


async def _directory_counts(db, query: dict[str, Any]) -> tuple[int, int]:
    projected_count = 0
    identity_count = 0
    if _has_collection(db, "employee_profile_read_models"):
        projected_count = await _count_matching_rows(db.employee_profile_read_models, query)
    identity_query = _identity_fallback_query(query)
    if identity_query is not None and _has_collection(db, "employee_identities"):
        identity_count = await _count_matching_rows(db.employee_identities, identity_query)
    return projected_count, identity_count


async def _list_directory_rows(
    db,
    *,
    query: dict[str, Any],
    offset: int,
    limit: int,
    sort_by: str | None = None,
    sort_dir: str = "asc",
) -> list[dict[str, Any]]:
    projected_count, identity_count = await _directory_counts(db, query)
    if projected_count >= identity_count and _has_collection(db, "employee_profile_read_models"):
        return await _list_matching_rows(
            db.employee_profile_read_models,
            query,
            offset=offset,
            limit=limit,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
    identity_query = _identity_fallback_query(query)
    if identity_query is not None and _has_collection(db, "employee_identities"):
        return await _list_matching_rows(
            db.employee_identities,
            identity_query,
            offset=offset,
            limit=limit,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
    if _has_collection(db, "employee_profile_read_models"):
        return await _list_matching_rows(
            db.employee_profile_read_models,
            query,
            offset=offset,
            limit=limit,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
    raise AttributeError("Database handle is missing employee profile collections")


async def _count_directory_rows(db, query: dict[str, Any]) -> int:
    projected_count, identity_count = await _directory_counts(db, query)
    if projected_count or identity_count:
        return max(projected_count, identity_count)
    if _has_collection(db, "employee_profile_read_models") or _has_collection(db, "employee_identities"):
        return 0
    raise AttributeError("Database handle is missing employee profile collections")


def _build_profile_query(
    *,
    department_code: str | None = None,
    search: str | None = None,
    workflow_status: str | None = None,
    employment_type: str | None = None,
    designation_id: str | None = None,
    office_id: str | None = None,
    employee_status: str | None = None,
    recruitment_mode: str | None = None,
    pay_level: str | None = None,
    service: str | None = None,
    service_group: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    extra_filter: dict[str, Any] | None = None,
) -> dict[str, Any]:
    query: dict[str, Any] = {}
    if department_code:
        query["current_department_id"] = department_code
    if workflow_status:
        status_values = workflow_status_filter_values(workflow_status)
        query["workflow_status"] = (
            status_values[0] if len(status_values) == 1 else {"$in": status_values}
        )
    if employment_type:
        query["employment_type"] = employment_type
    if designation_id:
        query["current_designation_id"] = designation_id
    if office_id:
        query["current_office_id"] = office_id
    if employee_status:
        query["employee_status"] = employee_status
    if recruitment_mode:
        query["mode_of_recruitment"] = recruitment_mode
    if pay_level:
        query["pay_level"] = pay_level
    if service:
        query["service"] = service
    if service_group:
        query["group"] = service_group
    if date_from or date_to:
        date_cond: dict[str, str] = {}
        if date_from:
            date_cond["$gte"] = date_from
        if date_to:
            date_cond["$lte"] = date_to
        query["date_of_initial_engagement"] = date_cond
    if search:
        safe_search = re.escape(search)
        query["$or"] = [
            {"full_name": {"$regex": safe_search, "$options": "i"}},
            {"employee_id": {"$regex": safe_search, "$options": "i"}},
            {"employee_code": {"$regex": safe_search, "$options": "i"}},
            {"current_department_id": {"$regex": safe_search, "$options": "i"}},
            {"current_designation_id": {"$regex": safe_search, "$options": "i"}},
            {"current_office_id": {"$regex": safe_search, "$options": "i"}},
        ]
    if extra_filter:
        query.update(extra_filter)
    return query


async def list_profiles_by_department(
    db,
    *,
    department_code: str,
    search: str | None = None,
    workflow_status: str | None = None,
    employment_type: str | None = None,
    designation_id: str | None = None,
    office_id: str | None = None,
    employee_status: str | None = None,
    recruitment_mode: str | None = None,
    pay_level: str | None = None,
    service: str | None = None,
    service_group: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 500,
    offset: int = 0,
    sort_by: str | None = None,
    sort_dir: str = "asc",
) -> list[dict[str, Any]]:
    query = _build_profile_query(
        department_code=department_code,
        search=search,
        workflow_status=workflow_status,
        employment_type=employment_type,
        designation_id=designation_id,
        office_id=office_id,
        employee_status=employee_status,
        recruitment_mode=recruitment_mode,
        pay_level=pay_level,
        service=service,
        service_group=service_group,
        date_from=date_from,
        date_to=date_to,
    )
    return await _list_directory_rows(
        db,
        query=query,
        offset=offset,
        limit=limit,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


async def list_profiles(
    db,
    *,
    search: str | None = None,
    workflow_status: str | None = None,
    employment_type: str | None = None,
    department_code: str | None = None,
    designation_id: str | None = None,
    office_id: str | None = None,
    employee_status: str | None = None,
    recruitment_mode: str | None = None,
    pay_level: str | None = None,
    service: str | None = None,
    service_group: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 500,
    offset: int = 0,
    sort_by: str | None = None,
    sort_dir: str = "asc",
) -> list[dict[str, Any]]:
    query = _build_profile_query(
        department_code=department_code,
        search=search,
        workflow_status=workflow_status,
        employment_type=employment_type,
        designation_id=designation_id,
        office_id=office_id,
        employee_status=employee_status,
        recruitment_mode=recruitment_mode,
        pay_level=pay_level,
        service=service,
        service_group=service_group,
        date_from=date_from,
        date_to=date_to,
    )
    return await _list_directory_rows(
        db,
        query=query,
        offset=offset,
        limit=limit,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


async def count_profiles_by_department(
    db,
    *,
    department_code: str,
    search: str | None = None,
    workflow_status: str | None = None,
    employment_type: str | None = None,
    designation_id: str | None = None,
    office_id: str | None = None,
    employee_status: str | None = None,
    recruitment_mode: str | None = None,
    pay_level: str | None = None,
    service: str | None = None,
    service_group: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    extra_filter: dict[str, Any] | None = None,
) -> int:
    query = _build_profile_query(
        department_code=department_code,
        search=search,
        workflow_status=workflow_status,
        employment_type=employment_type,
        designation_id=designation_id,
        office_id=office_id,
        employee_status=employee_status,
        recruitment_mode=recruitment_mode,
        pay_level=pay_level,
        service=service,
        service_group=service_group,
        date_from=date_from,
        date_to=date_to,
        extra_filter=extra_filter,
    )
    return await _count_directory_rows(db, query)


async def count_profiles(
    db,
    *,
    search: str | None = None,
    workflow_status: str | None = None,
    employment_type: str | None = None,
    department_code: str | None = None,
    designation_id: str | None = None,
    office_id: str | None = None,
    employee_status: str | None = None,
    recruitment_mode: str | None = None,
    pay_level: str | None = None,
    service: str | None = None,
    service_group: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> int:
    query = _build_profile_query(
        department_code=department_code,
        search=search,
        workflow_status=workflow_status,
        employment_type=employment_type,
        designation_id=designation_id,
        office_id=office_id,
        employee_status=employee_status,
        recruitment_mode=recruitment_mode,
        pay_level=pay_level,
        service=service,
        service_group=service_group,
        date_from=date_from,
        date_to=date_to,
    )
    return await _count_directory_rows(db, query)


async def get_employee_ids_for_department(
    db,
    *,
    department_code: str,
    limit: int = 5000,
) -> list[str]:
    return await list_employee_ids_by_department(
        db, department_code=department_code, limit=limit,
    )


async def get_employee_name_map(
    db,
    *,
    employee_ids: list[str],
) -> dict[str, str]:
    collection = getattr(db, "employee_identities", None)
    if collection is None:
        return {}
    cursor = collection.find(
        {"employee_id": {"$in": employee_ids}},
        {"_id": 0, "employee_id": 1, "full_name": 1},
    )
    return {
        doc["employee_id"]: doc.get("full_name", doc["employee_id"])
        async for doc in cursor
    }


