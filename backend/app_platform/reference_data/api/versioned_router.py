# Master Data Versioning API
# ===========================
#
# GOVERNANCE RULES:
# - DELETE operations = FORBIDDEN
# - UPDATE = creates NEW VERSION only
# - is_active must be mutually exclusive per master
# - Old versions remain referenceable forever
# - All changes must write to audit_log
#
# SYSTEM_MANAGED_MASTERS:
# - employment_type, pay_level, service_event_type
# - document_type, qualification, role, workflow_stage

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from app_platform.reference_data.api.versioning_helpers import (
    actor_identity,
    build_deprecated_version_record,
    build_initial_record,
    build_updated_version_record,
    supersede_active_record,
)
from app_platform.reference_data.infrastructure.versioned_validation import (
    MasterMetadataValidationError,
    validate_and_normalize_master_metadata,
)
from app_platform.reference_data.contracts.employment_type_master import (
    RETAINED_EMPLOYMENT_TYPE_CODES,
    normalize_employment_type_code as normalize_employment_type_master_code,
)
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

masters_router = APIRouter(prefix="/masters", tags=["Policy Masters (Versioned)"])

COMPAT_CREATED_BY = "compat_migration"


def normalize_record_code(code: str) -> str:
    return str(code or "").strip().upper()


def active_record_query(code: str) -> Dict[str, Any]:
    normalized_code = normalize_record_code(code)
    return {
        "code": normalized_code,
        "$or": [
            {"is_active": True},
            {"is_active": {"$exists": False}},
        ],
    }


def normalize_master_record(record: Dict[str, Any]) -> Dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()
    code = normalize_record_code(record.get("code"))
    name = record.get("name") or record.get("description")
    if not code or not name:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INVALID_MASTER_RECORD_SHAPE",
                "message": "Master record is missing mandatory identity fields.",
                "record_hint": str(record.get("code") or record.get("id") or "unknown"),
            },
        )

    record_id = record.get("id") or f"compat::{code}"
    version = int(record.get("version") or 1)
    is_active = bool(record.get("is_active", True))
    created_at = record.get("created_at") or record.get("updated_at") or now_iso
    created_by = (
        record.get("created_by") or record.get("updated_by") or COMPAT_CREATED_BY
    )
    return {
        "id": record_id,
        "code": code,
        "name": name,
        "description": record.get("description"),
        "metadata": record.get("metadata") or {},
        "version": version,
        "is_active": is_active,
        "created_at": created_at,
        "created_by": created_by,
        "superseded_by": record.get("superseded_by"),
        "superseded_at": record.get("superseded_at"),
    }


class MasterType(str, Enum):
    EMPLOYMENT_TYPE = "employment_type"
    PAY_LEVEL = "pay_level"
    SERVICE_EVENT_TYPE = "service_event_type"
    LEAVE_TYPE = "leave_type"
    DOCUMENT_TYPE = "document_type"
    QUALIFICATION = "qualification"
    ROLE = "role"
    WORKFLOW_STAGE = "workflow_stage"
    DEPARTMENT = "department"
    DESIGNATION = "designation"
    CASTE_CATEGORY = "caste_category"
    SERVICE_GROUP = "service_group"
    SERVICE = "service"


MASTER_COLLECTIONS = {
    MasterType.EMPLOYMENT_TYPE: "employment_types",
    MasterType.PAY_LEVEL: "pay_levels",
    MasterType.SERVICE_EVENT_TYPE: "service_event_types",
    MasterType.LEAVE_TYPE: "leave_types",
    MasterType.DOCUMENT_TYPE: "document_types",
    MasterType.QUALIFICATION: "qualifications",
    MasterType.ROLE: "roles",
    MasterType.WORKFLOW_STAGE: "workflow_stages",
    MasterType.DEPARTMENT: "departments",
    MasterType.DESIGNATION: "designations",
    MasterType.CASTE_CATEGORY: "caste_categories",
    MasterType.SERVICE_GROUP: "service_groups",
    MasterType.SERVICE: "services",
}

READ_ONLY_DERIVED_MASTER_TYPES = {MasterType.WORKFLOW_STAGE}


def ensure_master_type_is_mutable(master_type: MasterType) -> None:
    if master_type in READ_ONLY_DERIVED_MASTER_TYPES:
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "READ_ONLY_MASTER_TYPE",
                "message": "This master type is a read-only derived view and cannot be modified here.",
                "master_type": master_type.value,
            },
        )


class MasterRecordBase(BaseModel):
    code: str = Field(..., description="Unique code for this master item")
    name: str = Field(..., description="Display name")
    description: Optional[str] = Field(None, description="Optional description")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional type-specific fields"
    )


class MasterRecordCreate(MasterRecordBase):
    pass


class MasterRecordUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    reason: str = Field(
        ..., min_length=10, description="Reason for update (mandatory for audit)"
    )


class MasterRecordResponse(MasterRecordBase):
    id: str
    version: int
    is_active: bool
    created_at: str
    created_by: str
    superseded_by: Optional[str] = None
    superseded_at: Optional[str] = None


class MasterVersionHistory(BaseModel):
    code: str
    versions: List[MasterRecordResponse]
    total_versions: int


def get_db():
    from app_platform.db.runtime import mongo_state

    db = mongo_state.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    return db


def get_master_collection(db, master_type: MasterType):
    collection_name = MASTER_COLLECTIONS.get(master_type)
    if not collection_name:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown master type: {master_type}",
        )
    return db[collection_name]


async def get_required_active_record(collection, code: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
    current_record_raw = await collection.find_one(
        active_record_query(code),
        sort=[("version", -1), ("created_at", -1)],
    )
    if not current_record_raw:
        raise HTTPException(
            status_code=404,
            detail=f"Active master record not found: {code}",
        )
    return current_record_raw, normalize_master_record(current_record_raw)


from contexts.rbac.application.access_control import require_system_admin
from app_platform.auth.current_user import get_current_user


async def log_master_change(
    db,
    master_type: str,
    action: str,
    record_code: str,
    user_id: str,
    user_email: str,
    before_state: Optional[Dict] = None,
    after_state: Optional[Dict] = None,
    reason: Optional[str] = None,
):
    log_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entity_type": "MASTER_DATA",
        "master_type": master_type,
        "action": action,
        "record_code": record_code,
        "actor_id": user_id,
        "actor_email": user_email,
        "before_state": before_state,
        "after_state": after_state,
        "reason": reason,
    }
    await db.master_audit_logs.insert_one(log_entry)
    return log_entry["id"]


@masters_router.get("/{master_type}", response_model=Dict)
async def list_master_records(
    master_type: MasterType,
    include_inactive: bool = False,
    current_user: dict = Depends(get_current_user),
):
    require_system_admin(current_user)
    db = get_db()
    collection = get_master_collection(db, master_type)

    cursor = collection.find({}, {"_id": 0}).sort("code", 1)
    raw_records = await cursor.to_list(length=1000)
    records = [normalize_master_record(r) for r in raw_records]
    if not include_inactive:
        records = [r for r in records if r.get("is_active", False)]
    if master_type == MasterType.EMPLOYMENT_TYPE:
        retained_codes = set(RETAINED_EMPLOYMENT_TYPE_CODES)
        records_by_code = {
            code: record
            for record in records
            if (code := normalize_employment_type_master_code(record.get("code"))) in retained_codes
        }
        records = [records_by_code[code] for code in RETAINED_EMPLOYMENT_TYPE_CODES if code in records_by_code]

    return {
        "master_type": master_type.value,
        "records": records,
        "total": len(records),
        "include_inactive": include_inactive,
    }


@masters_router.get("/{master_type}/{code}", response_model=Dict)
async def get_master_record(
    master_type: MasterType,
    code: str,
    current_user: dict = Depends(get_current_user),
):
    require_system_admin(current_user)
    db = get_db()
    collection = get_master_collection(db, master_type)
    normalized_code = normalize_record_code(code)

    record = await collection.find_one(active_record_query(normalized_code), {"_id": 0})

    if not record:
        raise HTTPException(status_code=404, detail=f"Master record not found: {normalized_code}")

    return {"record": normalize_master_record(record)}


@masters_router.get("/{master_type}/{code}/history", response_model=MasterVersionHistory)
async def get_version_history(
    master_type: MasterType,
    code: str,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    require_system_admin(current_user)
    collection = get_master_collection(db, master_type)
    normalized_code = normalize_record_code(code)

    cursor = collection.find({"code": normalized_code}, {"_id": 0}).sort("version", -1)
    raw_versions = await cursor.to_list(length=100)
    versions = [normalize_master_record(v) for v in raw_versions]

    if not versions:
        raise HTTPException(status_code=404, detail=f"No versions found for: {normalized_code}")

    return MasterVersionHistory(
        code=normalized_code,
        versions=versions,
        total_versions=len(versions),
    )


@masters_router.post("/{master_type}", response_model=Dict)
async def create_master_record(
    master_type: MasterType,
    data: MasterRecordCreate,
    current_user: dict = Depends(get_current_user),
):
    ensure_master_type_is_mutable(master_type)
    db = get_db()
    require_system_admin(current_user)
    collection = get_master_collection(db, master_type)
    normalized_code = normalize_record_code(data.code)

    existing = await collection.find_one(active_record_query(normalized_code))
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Master record with code '{normalized_code}' already exists",
        )

    try:
        normalized_metadata = validate_and_normalize_master_metadata(
            master_type.value,
            normalized_code,
            data.metadata,
        )
    except MasterMetadataValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    user_id, user_email = actor_identity(current_user)

    record = build_initial_record(
        code=normalized_code,
        name=data.name.strip(),
        description=data.description.strip() if data.description else None,
        metadata=normalized_metadata,
        created_by=user_email,
    )

    await collection.insert_one(record)

    await log_master_change(
        db=db,
        master_type=master_type.value,
        action="CREATE",
        record_code=normalized_code,
        user_id=user_id,
        user_email=user_email,
        after_state=record,
        reason="Initial creation",
    )

    record.pop("_id", None)

    return {
        "success": True,
        "message": f"Master record created: {normalized_code}",
        "record": record,
    }


@masters_router.put("/{master_type}/{code}", response_model=Dict)
async def update_master_record(
    master_type: MasterType,
    code: str,
    data: MasterRecordUpdate,
    current_user: dict = Depends(get_current_user),
):
    ensure_master_type_is_mutable(master_type)
    db = get_db()
    require_system_admin(current_user)
    collection = get_master_collection(db, master_type)
    normalized_code = normalize_record_code(code)
    current_record_raw, current_record = await get_required_active_record(
        collection,
        normalized_code,
    )

    normalized_metadata = None
    if data.metadata is not None:
        try:
            normalized_metadata = validate_and_normalize_master_metadata(
                master_type.value,
                normalized_code,
                data.metadata,
                current_metadata=current_record.get("metadata") or {},
            )
        except MasterMetadataValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    user_id, user_email = actor_identity(current_user)
    new_record, new_version, now = build_updated_version_record(
        code=normalized_code,
        current_record=current_record,
        updated_name=data.name.strip() if data.name is not None else None,
        updated_description=data.description.strip() if data.description is not None else None,
        updated_metadata=normalized_metadata,
        created_by=user_email,
    )

    # Insert new version FIRST so a failed insert never orphans the old record
    await collection.insert_one(new_record)

    await supersede_active_record(
        collection=collection,
        current_record_raw=current_record_raw,
        code=code,
        new_record_id=new_record["id"],
        now=now,
        active_record_query=active_record_query,
    )

    await log_master_change(
        db=db,
        master_type=master_type.value,
        action="UPDATE_VERSION",
        record_code=normalized_code,
        user_id=user_id,
        user_email=user_email,
        before_state=current_record,
        after_state=new_record,
        reason=data.reason,
    )

    new_record.pop("_id", None)

    return {
        "success": True,
        "message": f"Master record updated: {normalized_code} (v{current_record.get('version', 1)} -> v{new_version})",
        "previous_version": current_record.get("version", 1),
        "new_version": new_version,
        "record": new_record,
        "reason": data.reason,
    }


@masters_router.delete("/{master_type}/{code}")
async def delete_master_record(
    master_type: MasterType,
    code: str,
    current_user: dict = Depends(get_current_user),
):
    raise HTTPException(
        status_code=403,
        detail={
            "error_code": "DELETE_FORBIDDEN",
            "message": "DELETE operations are FORBIDDEN for master data.",
            "governance_rule": "Master records cannot be deleted. Use versioned updates to deprecate records.",
            "alternative": f"Use PUT /{master_type}/{code} with metadata.deprecated=true",
        },
    )


@masters_router.post("/{master_type}/{code}/deprecate", response_model=Dict)
async def deprecate_master_record(
    master_type: MasterType,
    code: str,
    reason: str,
    current_user: dict = Depends(get_current_user),
):
    ensure_master_type_is_mutable(master_type)
    db = get_db()
    require_system_admin(current_user)
    normalized_code = normalize_record_code(code)

    if len(reason) < 10:
        raise HTTPException(
            status_code=400, detail="Reason must be at least 10 characters"
        )

    collection = get_master_collection(db, master_type)
    current_record_raw, current_record = await get_required_active_record(
        collection,
        normalized_code,
    )

    user_id, user_email = actor_identity(current_user)
    new_record, new_version, now = build_deprecated_version_record(
        code=normalized_code,
        current_record=current_record,
        reason=reason,
        created_by=user_email,
    )

    # Insert new version FIRST so a failed insert never orphans the old record
    await collection.insert_one(new_record)

    await supersede_active_record(
        collection=collection,
        current_record_raw=current_record_raw,
        code=code,
        new_record_id=new_record["id"],
        now=now,
        active_record_query=active_record_query,
    )

    await log_master_change(
        db=db,
        master_type=master_type.value,
        action="DEPRECATE",
        record_code=normalized_code,
        user_id=user_id,
        user_email=user_email,
        before_state=current_record,
        after_state=new_record,
        reason=reason,
    )

    new_record.pop("_id", None)

    return {
        "success": True,
        "message": f"Master record deprecated: {normalized_code}",
        "record": new_record,
        "reason": reason,
    }


@masters_router.get("/{master_type}/audit/logs", response_model=Dict)
async def get_master_audit_logs(
    master_type: MasterType,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    require_system_admin(current_user)

    cursor = (
        db.master_audit_logs.find({"master_type": master_type.value}, {"_id": 0})
        .sort("timestamp", -1)
        .limit(limit)
    )

    logs = await cursor.to_list(length=limit)

    return {
        "master_type": master_type.value,
        "logs": logs,
        "total": len(logs),
    }
