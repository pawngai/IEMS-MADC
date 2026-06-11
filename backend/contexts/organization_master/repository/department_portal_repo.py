"""
Department Portal repository layer.

Pure contract delegations scoped by department_code / department employee IDs.
No business logic. No direct cross-context DB access.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app_platform.reference_data.infrastructure import service as reference_data_service
from app_platform.domain_separation.data_ownership import assert_collection_ownership
from contexts.audit.contracts.audit_directory import list_audit_logs
from contexts.employee_master.contracts.identity_directory import (
    get_employee_ids_for_department as get_employee_ids_for_dept,
    get_employee_name_map as _employee_name_map,
)
from contexts.employee_master.contracts.profile_directory import (
    count_profiles_by_department,
    list_profiles_by_department,
)
from contexts.employee_master.contracts.workflow_status_utils import workflow_status_filter_values
from contexts.leave_attendance.contracts.leave_directory import (
    count_pending_leave_applications,
    list_pending_leave_applications,
)


ESTABLISHMENT_COLLECTION = "department_establishments"
ESTABLISHMENT_LOG_COLLECTION = "department_establishment_logs"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def list_employees(
    db,
    department_code: str,
    *,
    search: Optional[str] = None,
    workflow_status: Optional[str] = None,
    employment_type: Optional[str] = None,
    designation_id: Optional[str] = None,
    office_id: Optional[str] = None,
    employee_status: Optional[str] = None,
    recruitment_mode: Optional[str] = None,
    pay_level: Optional[str] = None,
    service: Optional[str] = None,
    service_group: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 500,
    offset: int = 0,
    sort_by: Optional[str] = None,
    sort_dir: str = "asc",
) -> list[dict[str, Any]]:
    return await list_profiles_by_department(
        db,
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
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


async def count_employees(
    db,
    department_code: str,
    *,
    search: Optional[str] = None,
    workflow_status: Optional[str] = None,
    employment_type: Optional[str] = None,
    designation_id: Optional[str] = None,
    office_id: Optional[str] = None,
    employee_status: Optional[str] = None,
    recruitment_mode: Optional[str] = None,
    pay_level: Optional[str] = None,
    service: Optional[str] = None,
    service_group: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> int:
    return await count_profiles_by_department(
        db,
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


async def count_employees_by_status(db, department_code: str, status: str) -> int:
    return await count_profiles_by_department(
        db,
        department_code=department_code,
        extra_filter={"employee_status": status},
    )


async def count_employees_by_workflow(db, department_code: str, workflow_status: str) -> int:
    status_values = workflow_status_filter_values(workflow_status)
    status_query = status_values[0] if len(status_values) == 1 else {"$in": status_values}
    return await count_profiles_by_department(
        db,
        department_code=department_code,
        extra_filter={"workflow_status": status_query},
    )


async def count_employees_by_employment_type(db, department_code: str, emp_type: str) -> int:
    return await count_profiles_by_department(
        db,
        department_code=department_code,
        extra_filter={"employment_type": emp_type},
    )


async def get_employee_ids_for_department(db, department_code: str) -> list[str]:
    return await get_employee_ids_for_dept(db, department_code=department_code)


async def get_employee_name_map(db, employee_ids: list[str]) -> dict[str, str]:
    return await _employee_name_map(db, employee_ids=employee_ids)


async def list_pending_leaves(
    db,
    employee_ids: list[str],
    statuses: list[str],
    *,
    limit: int = 500,
) -> list[dict[str, Any]]:
    return await list_pending_leave_applications(
        db,
        employee_ids=employee_ids,
        statuses=statuses,
        limit=limit,
    )


async def count_pending_leaves(db, employee_ids: list[str], statuses: list[str]) -> int:
    return await count_pending_leave_applications(
        db,
        employee_ids=employee_ids,
        statuses=statuses,
    )


async def list_department_activity(
    db,
    employee_ids: list[str],
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    if not employee_ids:
        return []
    query = {
        "$or": [
            {"resource_id": {"$in": employee_ids}},
            {"details.employee_id": {"$in": employee_ids}},
        ]
    }
    return await list_audit_logs(db, query=query, limit=limit)


async def get_department_info(db, department_code: str) -> Optional[dict[str, Any]]:
    departments = await reference_data_service.get_departments(db)
    normalized_department_code = str(department_code or "").strip().upper()
    for department in departments:
        if str((department or {}).get("code") or "").strip().upper() != normalized_department_code:
            continue
        return {
            "code": department.get("code"),
            "name": department.get("name"),
            "status": department.get("status"),
        }
    return None


async def get_department_establishment_record(
    db,
    department_code: str,
) -> Optional[dict[str, Any]]:
    assert_collection_ownership(
        context="organization_master",
        collection_name=ESTABLISHMENT_COLLECTION,
        write=False,
    )
    return await db[ESTABLISHMENT_COLLECTION].find_one(
        {"department_code": department_code},
        {"_id": 0},
    )


async def get_department_establishment_rows(
    db,
    department_code: str,
) -> list[dict[str, Any]]:
    record = await get_department_establishment_record(db, department_code)
    rows = (record or {}).get("items") or []
    return rows if isinstance(rows, list) else []


async def upsert_department_establishment(
    db,
    department_code: str,
    *,
    items: list[dict[str, Any]],
    reason: str,
    actor_id: str,
    actor_email: str,
) -> dict[str, Any]:
    assert_collection_ownership(
        context="organization_master",
        collection_name=ESTABLISHMENT_COLLECTION,
        write=True,
    )
    assert_collection_ownership(
        context="organization_master",
        collection_name=ESTABLISHMENT_LOG_COLLECTION,
        write=True,
    )

    before = await get_department_establishment_record(db, department_code)
    now = _utc_now_iso()

    if before:
        document = {
            "department_code": department_code,
            "items": items,
            "updated_at": now,
            "updated_by": actor_email,
            "created_at": before.get("created_at") or now,
            "created_by": before.get("created_by") or actor_email,
        }
        await db[ESTABLISHMENT_COLLECTION].update_one(
            {"department_code": department_code},
            {"$set": document},
        )
        action = "UPDATE"
    else:
        document = {
            "id": str(uuid.uuid4()),
            "department_code": department_code,
            "items": items,
            "created_at": now,
            "created_by": actor_email,
            "updated_at": now,
            "updated_by": actor_email,
        }
        await db[ESTABLISHMENT_COLLECTION].insert_one(document)
        action = "CREATE"

    await db[ESTABLISHMENT_LOG_COLLECTION].insert_one(
        {
            "id": str(uuid.uuid4()),
            "timestamp": now,
            "action": action,
            "department_code": department_code,
            "actor_id": actor_id,
            "actor_email": actor_email,
            "reason": reason,
            "before_state": before,
            "after_state": document,
        }
    )

    return document


async def count_active_employees_for_establishment_row(
    db,
    department_code: str,
    *,
    designation_code: str,
    employment_type: str | None = None,
) -> int:
    return await count_profiles_by_department(
        db,
        department_code=department_code,
        designation_id=designation_code,
        employment_type=employment_type,
        employee_status="ACTIVE",
    )