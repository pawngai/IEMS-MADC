"""
Department Management — Direct CRUD with audit logging (no versioning).

Records are updated in-place. All changes are written to an append-only
`department_change_logs` collection for full traceability.

Prefix: /departments/manage
RBAC: SYSTEM_ADMIN only
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app_platform.db.runtime import get_db
from contexts.system_admin.department.api.management_helpers import (
    active_query,
    build_department_metadata,
    ensure_distinct_role_holders,
    normalize_employee_ref,
    serialize_department,
)
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from contexts.identity.contracts.department_authority_commands import (
    revoke_department_authority,
    sync_department_authority,
)
from contexts.rbac.application.access_control import require_system_admin
from app_platform.auth.current_user import get_current_user


async def _sync_role_holders(
    db,
    *,
    department_code: str,
    old_hod: str | None,
    new_hod: str | None,
    old_de: str | None,
    new_de: str | None,
    actor_sub: str,
) -> dict:
    """Sync user authorities when department role holders change.

    Returns a dict with sync results for the audit trail.
    """
    results: dict = {}

    # --- HOD ---
    # Always sync when a holder is set (idempotent) so pre-existing
    # assignments that were never synced get self-healed.
    if new_hod:
        try:
            results["hod_sync"] = await sync_department_authority(
                db,
                employee_id=new_hod,
                authority="HOD",
                department_code=department_code,
                actor_sub=actor_sub,
            )
        except ValueError as exc:
            results["hod_sync_error"] = str(exc)
    elif old_hod:
        # Cleared — revoke from the old holder
        try:
            results["hod_revoke"] = await revoke_department_authority(
                db,
                employee_id=old_hod,
                authority="HOD",
                actor_sub=actor_sub,
            )
        except ValueError as exc:
            results["hod_revoke_error"] = str(exc)

    # --- DEPT_DATA_ENTRY ---
    if new_de:
        try:
            results["de_sync"] = await sync_department_authority(
                db,
                employee_id=new_de,
                authority="DEPT_DATA_ENTRY",
                department_code=department_code,
                actor_sub=actor_sub,
            )
        except ValueError as exc:
            results["de_sync_error"] = str(exc)
    elif old_de:
        try:
            results["de_revoke"] = await revoke_department_authority(
                db,
                employee_id=old_de,
                authority="DEPT_DATA_ENTRY",
                actor_sub=actor_sub,
            )
        except ValueError as exc:
            results["de_revoke_error"] = str(exc)

    return results

dept_management_router = APIRouter(
    prefix="/departments/manage",
    tags=["Department Management"],
)

COLLECTION = "departments"
LOG_COLLECTION = "department_change_logs"


def _actor_identity(current_user: dict) -> tuple[str, str]:
    return current_user.get("sub", "unknown"), current_user.get("email", "unknown")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _list_logs(db, *, query: Dict[str, Any], limit: int) -> list[Dict[str, Any]]:
    cursor = db[LOG_COLLECTION].find(query, {"_id": 0}).sort("timestamp", -1).limit(limit)
    return await cursor.to_list(length=limit)


class DepartmentCreate(BaseModel):
    code: str = Field(..., description="Unique department code")
    name: str = Field(..., description="Department name")
    description: Optional[str] = None
    hod_employee_id: Optional[str] = None
    data_entry_employee_id: Optional[str] = None


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    hod_employee_id: Optional[str] = None
    data_entry_employee_id: Optional[str] = None
    is_active: Optional[bool] = None
    reason: str = Field(
        ..., min_length=3, description="Reason for change (audit trail)"
    )


async def _write_log(
    db,
    *,
    action: str,
    department_code: str,
    actor_id: str,
    actor_email: str,
    before: Optional[Dict[str, Any]] = None,
    after: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
):
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": _utc_now_iso(),
        "action": action,
        "department_code": department_code,
        "actor_id": actor_id,
        "actor_email": actor_email,
        "before_state": before,
        "after_state": after,
        "changes": changes,
        "reason": reason,
    }
    await db[LOG_COLLECTION].insert_one(entry)


@dept_management_router.get("/")
async def list_departments(
    include_inactive: bool = Query(default=False),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_system_admin(current_user)

    query: Dict[str, Any] = {}
    if not include_inactive:
        query["$or"] = [
            {"is_active": True},
            {"is_active": {"$exists": False}},
        ]

    cursor = db[COLLECTION].find(query, {"_id": 0}).sort("code", 1)
    raw = await cursor.to_list(length=1000)
    records = [serialize_department(r) for r in raw]
    active_count = sum(1 for r in records if r.get("is_active", True))
    return {
        "records": records,
        "total": len(records),
        "active_count": active_count,
    }


@dept_management_router.get("/logs/all")
async def get_all_department_logs(
    limit: int = Query(default=100, ge=1, le=500),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_system_admin(current_user)

    logs = await _list_logs(db, query={}, limit=limit)
    return {"logs": logs, "total": len(logs)}


@dept_management_router.get("/{code}")
async def get_department(
    code: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_system_admin(current_user)

    record = await db[COLLECTION].find_one(active_query(code), {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail=f"Department not found: {code}")
    return {"record": serialize_department(record)}


@dept_management_router.post("/")
async def create_department(
    data: DepartmentCreate,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_system_admin(current_user)

    code = data.code.strip().upper()
    existing = await db[COLLECTION].find_one(active_query(code), {"_id": 0})
    if existing:
        raise HTTPException(
            status_code=409, detail=f"Department '{code}' already exists"
        )

    hod_id = normalize_employee_ref(data.hod_employee_id)
    de_id = normalize_employee_ref(data.data_entry_employee_id)
    ensure_distinct_role_holders(
        hod_employee_id=hod_id,
        data_entry_employee_id=de_id,
    )

    actor_id, user_email = _actor_identity(current_user)
    now = _utc_now_iso()

    record = {
        "id": str(uuid.uuid4()),
        "code": code,
        "name": data.name.strip(),
        "description": (data.description or "").strip() or None,
        "metadata": build_department_metadata(
            hod_employee_id=hod_id,
            data_entry_employee_id=de_id,
        ),
        "version": 1,
        "is_active": True,
        "created_at": now,
        "created_by": user_email,
        "updated_at": now,
        "updated_by": user_email,
    }

    await db[COLLECTION].insert_one(record)
    record.pop("_id", None)
    serialized_record = serialize_department(record)

    # Auto-sync user authorities for initial HOD / Data Entry assignments
    sync_results = await _sync_role_holders(
        db,
        department_code=code,
        old_hod=None,
        new_hod=hod_id,
        old_de=None,
        new_de=de_id,
        actor_sub=actor_id,
    )

    await _write_log(
        db,
        action="CREATE",
        department_code=code,
        actor_id=actor_id,
        actor_email=user_email,
        after=serialized_record,
        reason="Initial creation",
        changes={"authority_sync": sync_results} if sync_results else None,
    )

    return {
        "success": True,
        "message": f"Department created: {code}",
        "record": serialized_record,
        "authority_sync": sync_results,
    }


@dept_management_router.put("/{code}")
async def update_department(
    code: str,
    data: DepartmentUpdate,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_system_admin(current_user)

    record = await db[COLLECTION].find_one({"code": code})
    if not record:
        raise HTTPException(status_code=404, detail=f"Department not found: {code}")

    before = serialize_department(record)
    actor_id, user_email = _actor_identity(current_user)
    now = _utc_now_iso()
    metadata = dict(record.get("metadata") or {})

    final_hod = (
        data.hod_employee_id.strip() if data.hod_employee_id is not None else None
    ) or metadata.get("hod_employee_id")
    final_de = (
        data.data_entry_employee_id.strip()
        if data.data_entry_employee_id is not None
        else None
    ) or metadata.get("data_entry_employee_id")
    ensure_distinct_role_holders(
        hod_employee_id=final_hod,
        data_entry_employee_id=final_de,
    )

    updates: Dict[str, Any] = {"updated_at": now, "updated_by": user_email}
    changes: Dict[str, Any] = {}

    if data.name is not None:
        updates["name"] = data.name.strip()
        if updates["name"] != record.get("name"):
            changes["name"] = {"from": record.get("name"), "to": updates["name"]}
    if data.description is not None:
        updates["description"] = data.description.strip() or None
        if updates["description"] != record.get("description"):
            changes["description"] = {
                "from": record.get("description"),
                "to": updates["description"],
            }
    if data.is_active is not None:
        updates["is_active"] = data.is_active
        if data.is_active != record.get("is_active", True):
            changes["is_active"] = {
                "from": record.get("is_active", True),
                "to": data.is_active,
            }

    if data.hod_employee_id is not None:
        val = data.hod_employee_id.strip() or None
        if val != metadata.get("hod_employee_id"):
            metadata["hod_employee_id"] = val
            changes["hod_employee_id"] = {
                "from": before.get("hod_employee_id"),
                "to": val,
            }
    if data.data_entry_employee_id is not None:
        val = data.data_entry_employee_id.strip() or None
        if val != metadata.get("data_entry_employee_id"):
            metadata["data_entry_employee_id"] = val
            changes["data_entry_employee_id"] = {
                "from": before.get("data_entry_employee_id"),
                "to": val,
            }

    rebuilt_metadata = build_department_metadata(
        hod_employee_id=metadata.get("hod_employee_id"),
        data_entry_employee_id=metadata.get("data_entry_employee_id"),
    )
    metadata["assigned_authorities"] = rebuilt_metadata["assigned_authorities"]
    metadata["allowed_authorities"] = rebuilt_metadata["allowed_authorities"]

    updates["metadata"] = metadata

    await db[COLLECTION].update_one({"_id": record["_id"]}, {"$set": updates})

    # Auto-sync user authorities when HOD / Data Entry assignments change
    sync_results = await _sync_role_holders(
        db,
        department_code=code,
        old_hod=before.get("hod_employee_id"),
        new_hod=metadata.get("hod_employee_id"),
        old_de=before.get("data_entry_employee_id"),
        new_de=metadata.get("data_entry_employee_id"),
        actor_sub=actor_id,
    )
    if sync_results:
        changes["authority_sync"] = sync_results

    updated = await db[COLLECTION].find_one({"_id": record["_id"]}, {"_id": 0})
    serialized_updated = serialize_department(updated)

    await _write_log(
        db,
        action="UPDATE",
        department_code=code,
        actor_id=actor_id,
        actor_email=user_email,
        before=before,
        after=serialized_updated,
        reason=data.reason,
        changes=changes if changes else None,
    )

    return {
        "success": True,
        "message": f"Department updated: {code}",
        "record": serialized_updated,
        "changes": changes,
        "authority_sync": sync_results,
        "reason": data.reason,
    }


@dept_management_router.get("/{code}/logs")
async def get_department_logs(
    code: str,
    limit: int = Query(default=50, ge=1, le=500),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_system_admin(current_user)

    logs = await _list_logs(db, query={"department_code": code}, limit=limit)
    return {"department_code": code, "logs": logs, "total": len(logs)}
