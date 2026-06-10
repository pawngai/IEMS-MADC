from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from app_platform.db.atomic import call_with_optional_session
from app_platform.outbox.model import OutboxEvent
from app_platform.outbox.repo import OutboxRepository
from contexts.employee_master.profile.contracts.dto import (
    EmployeeWorkflowAuditDTO,
    EmployeeWorkflowEventDTO,
)
from contexts.employee_master.profile.contracts.ports import (
    EmployeeProfileAuditGateway,
    EmployeeProfileReadGateway,
    EmployeeProfileRepositoryGateway,
    EmployeeProfileWorkflowGateway,
    EmployeeWorkflowEventGateway,
)
from contexts.employee_master.profile.contracts.workflow_status_utils import (
    normalize_employee_workflow_status,
)
from contexts.employee_master.profile.domain.identity_layers import (
    EXTENSION_FIELDS,
    IDENTITY_FIELDS,
    compose_employee_record_view,
    extract_extension_patch,
    extract_identity_patch,
    split_employee_payload,
    utc_now_iso,
)
from pydantic import BaseModel, Field


def _has_collection(db, name: str) -> bool:
    return getattr(db, name, None) is not None


def _should_fallback_to_identity_rows(query: dict[str, Any]) -> bool:
    requested_workflow = (query or {}).get("workflow_status")
    if not requested_workflow:
        return True
    return False


def _identity_can_seed_profile(identity: dict[str, Any] | None) -> bool:
    if not identity:
        return False
    workflow_status = str(identity.get("workflow_status") or "").strip().upper()
    return workflow_status in {"", "DRAFT", "SUBMITTED", "VERIFIED", "ACTIVE"}


def _profile_ready_identity_query(query: dict[str, Any]) -> dict[str, Any]:
    ready_query = dict(query or {})
    requested_identity_workflow = ready_query.pop("identity_workflow_status", None)
    requested_workflow = ready_query.get("workflow_status")
    if str(requested_identity_workflow or "").strip().upper() == "ACTIVE":
        ready_query["workflow_status"] = "ACTIVE"
        return ready_query
    if isinstance(requested_workflow, dict):
        values = {
            str(value).strip().upper()
            for value in requested_workflow.get("$in", [])
        }
        if "DRAFT" in values:
            ready_query["workflow_status"] = {"$in": ["DRAFT", "ACTIVE"]}
    elif requested_workflow:
        if str(requested_workflow).strip().upper() == "DRAFT":
            ready_query["workflow_status"] = {"$in": ["DRAFT", "ACTIVE"]}
    else:
        ready_query["workflow_status"] = {"$in": ["DRAFT", "ACTIVE"]}
    return ready_query


async def _ensure_profile_projection(db, employee_id: str) -> bool:
    if not _has_collection(db, "employee_profile_read_models"):
        return False

    existing = await db.employee_profile_read_models.find_one(
        {"employee_id": employee_id},
        {"_id": 0, "employee_id": 1},
    )
    if existing:
        return False

    await _refresh_profile_projection(db, employee_id)
    return True


async def _backfill_missing_profile_projections(db) -> int:
    if not _has_collection(db, "employee_profile_read_models") or not _has_collection(db, "employee_identities"):
        return 0

    projected_ids = {
        str(row.get("employee_id") or "").strip()
        async for row in db.employee_profile_read_models.find(
            {},
            {"_id": 0, "employee_id": 1},
        )
        if row.get("employee_id")
    }

    refreshed = 0
    async for row in db.employee_identities.find(
        {},
        {"_id": 0, "employee_id": 1, "updated_at": 1, "workflow_status": 1},
    ):
        employee_id = str(row.get("employee_id") or "").strip()
        if not employee_id:
            continue
        if not _identity_can_seed_profile(row):
            if employee_id in projected_ids:
                await db.employee_profile_read_models.delete_one({"employee_id": employee_id})
                await db.employee_master.delete_one({"employee_id": employee_id})
            continue
        if employee_id in projected_ids:
            projected = await db.employee_profile_read_models.find_one(
                {"employee_id": employee_id},
                {
                    "_id": 0,
                    "employee_id": 1,
                    "updated_at": 1,
                    "read_model_updated_at": 1,
                    "workflow_status": 1,
                    "identity_workflow_status": 1,
                },
            )
            projected_status = str((projected or {}).get("workflow_status") or "").strip().upper()
            projected_identity_status = (
                str((projected or {}).get("identity_workflow_status") or "")
                .strip()
                .upper()
            )
            identity_status = str(row.get("workflow_status") or "").strip().upper()
            if (
                projected
                and projected.get("updated_at") == row.get("updated_at")
                and projected_status != "ACTIVE"
                and projected_identity_status == identity_status
            ):
                continue
        await _refresh_profile_projection(db, employee_id)
        refreshed += 1
    return refreshed


async def _find_identity_doc(db, employee_id: str) -> dict | None:
    if not _has_collection(db, "employee_identities"):
        return None
    return await db.employee_identities.find_one({"employee_id": employee_id}, {"_id": 0})


async def _find_extension_doc(db, employee_id: str) -> dict | None:
    if not _has_collection(db, "employee_profile_extensions"):
        return None
    return await db.employee_profile_extensions.find_one({"employee_id": employee_id}, {"_id": 0})


async def _compose_live_profile(
    db,
    employee_id: str,
    *,
    allow_identity_workflow: bool = False,
) -> dict | None:
    identity = await _find_identity_doc(db, employee_id)
    if identity is not None and not allow_identity_workflow and not _identity_can_seed_profile(identity):
        return None
    extension = await _find_extension_doc(db, employee_id)
    composed = compose_employee_record_view(identity, extension)
    return composed or None


async def _refresh_profile_projection(
    db,
    employee_id: str,
    *,
    allow_identity_workflow: bool = False,
) -> None:
    if not _has_collection(db, "employee_profile_read_models"):
        return

    composed = await _compose_live_profile(
        db,
        employee_id,
        allow_identity_workflow=allow_identity_workflow,
    )
    if not composed:
        await db.employee_profile_read_models.delete_one({"employee_id": employee_id})
        await db.employee_master.delete_one({"employee_id": employee_id})
        return

    payload = dict(composed)
    payload["read_model_updated_at"] = utc_now_iso()
    created_at = payload.pop("created_at", None) or utc_now_iso()
    await db.employee_profile_read_models.update_one(
        {"employee_id": employee_id},
        {"$set": payload, "$setOnInsert": {"created_at": created_at}},
        upsert=True,
    )


async def _get_refreshed_profile_projection(
    db,
    employee_id: str,
    *,
    allow_identity_workflow: bool = False,
) -> dict | None:
    if not _has_collection(db, "employee_profile_read_models"):
        return None

    existing = await db.employee_profile_read_models.find_one(
        {"employee_id": employee_id},
        {"_id": 0},
    )
    if existing and await _find_identity_doc(db, employee_id) is None:
        return existing

    await _refresh_profile_projection(
        db,
        employee_id,
        allow_identity_workflow=allow_identity_workflow,
    )
    return await db.employee_profile_read_models.find_one(
        {"employee_id": employee_id},
        {"_id": 0},
    )


def _split_mongo_update(mongo_update: dict) -> tuple[dict, dict]:
    set_fields = dict(mongo_update.get("$set") or {})
    unset_fields = dict(mongo_update.get("$unset") or {})
    common_field_names = {"updated_at", "updated_by", "version"}

    identity_set = {
        key: value
        for key, value in extract_identity_patch(set_fields).items()
        if key not in common_field_names
    }
    extension_set = extract_extension_patch(set_fields)
    identity_unset: dict[str, Any] = {}
    extension_unset: dict[str, Any] = {}

    common_fields = {key: value for key, value in set_fields.items() if key in common_field_names}

    for key in unset_fields:
        if key in IDENTITY_FIELDS:
            identity_unset[key] = ""
        elif key in EXTENSION_FIELDS or key.startswith("contact.") or key.startswith("identifiers."):
            extension_unset[key] = ""

    if identity_set and not extension_set:
        identity_set.update(common_fields)
    elif extension_set and not identity_set:
        extension_set.update(common_fields)
    elif identity_set and extension_set:
        identity_set.update(common_fields)
        extension_set.update(common_fields)

    identity_update: dict[str, Any] = {}
    extension_update: dict[str, Any] = {}
    if identity_set:
        identity_update["$set"] = identity_set
    if identity_unset:
        identity_update["$unset"] = identity_unset
    if extension_set:
        extension_update["$set"] = extension_set
    if extension_unset:
        extension_update["$unset"] = extension_unset
    return identity_update, extension_update


class ProfileAuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    action: str
    performed_by_id: str
    performed_by_name: str
    performed_by_role: str
    previous_data: dict | None = None
    new_data: dict | None = None
    changed_fields: list[str] = Field(default_factory=list)
    workflow_status_before: str | None = None
    workflow_status_after: str | None = None
    remarks: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    integrity_hash: str | None = None


class EmployeeWorkflowEventOutboxGateway(EmployeeWorkflowEventGateway):
    def __init__(self, *, outbox_repo: OutboxRepository | None) -> None:
        self._outbox_repo = outbox_repo

    async def publish(self, *, event_name: str, payload: EmployeeWorkflowEventDTO, session=None) -> None:
        if self._outbox_repo is None:
            return

        await call_with_optional_session(
            self._outbox_repo.add_event,
            OutboxEvent(
                name=event_name,
                payload={
                    "employee_id": payload.employee_id,
                    "status": payload.status,
                    "remarks": payload.remarks,
                },
                actor_id=payload.actor_id,
                department_id=payload.department_id,
            ),
            session=session,
        )

    async def publish_raw(self, *, event_name: str, payload: dict, session=None) -> None:
        if self._outbox_repo is None:
            return

        await call_with_optional_session(
            self._outbox_repo.add_event,
            OutboxEvent(
                name=event_name,
                payload=payload,
                actor_id=payload.get("actor_id"),
                department_id=payload.get("dept_id") or payload.get("department_id"),
            ),
            session=session,
        )


class EmployeeProfileWorkflowMongoGateway(EmployeeProfileWorkflowGateway):
    def __init__(self, *, db) -> None:
        self._db = db

    async def persist_transition(
        self,
        *,
        employee_id: str,
        new_status: str,
        remarks: str | None,
        actor_user_id: str,
        transition: str,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        set_fields = {
            "workflow_status": new_status,
            "workflow_remarks": remarks,
            "updated_at": now,
            "updated_by": actor_user_id,
        }

        transition_upper = transition.upper()
        if transition_upper == "VERIFY":
            set_fields["verified_at"] = now
            set_fields["verified_by"] = actor_user_id
        elif transition_upper == "APPROVE":
            set_fields["approved_at"] = now
            set_fields["approved_by"] = actor_user_id
        elif transition_upper == "LOCK":
            set_fields["locked_at"] = now
            set_fields["locked_by"] = actor_user_id

        await self._db.employee_profile_extensions.update_one(
            {"employee_id": employee_id},
            {"$set": set_fields, "$setOnInsert": {"employee_id": employee_id, "created_at": now, "created_by": actor_user_id, "version": 1}},
            upsert=True,
        )
        await _refresh_profile_projection(
            self._db,
            employee_id,
            allow_identity_workflow=True,
        )


class EmployeeProfileRepositoryMongoGateway(EmployeeProfileRepositoryGateway):
    def __init__(self, *, db) -> None:
        self._db = db

    async def get_profile(self, *, employee_id: str) -> dict | None:
        projected = await _get_refreshed_profile_projection(
            self._db,
            employee_id,
            allow_identity_workflow=True,
        )
        if projected:
            return normalize_employee_workflow_status(projected)
        profile = await _compose_live_profile(
            self._db,
            employee_id,
            allow_identity_workflow=True,
        )
        return normalize_employee_workflow_status(profile) if profile else None

    async def insert_profile(self, *, profile: dict) -> None:
        identity, extension = split_employee_payload(profile)
        forbidden_identity_fields = {
            key for key in identity.keys() if key not in {"employee_id"}
        }
        if forbidden_identity_fields:
            raise PermissionError(
                "employee_profile cannot create employee identity records directly"
            )
        await self._db.employee_profile_extensions.insert_one(extension)
        await _refresh_profile_projection(
            self._db,
            profile.get("employee_id"),
            allow_identity_workflow=True,
        )

    async def update_profile(self, *, employee_id: str, mongo_update: dict) -> int:
        identity_update, extension_update = _split_mongo_update(mongo_update)
        modified = 0
        if identity_update:
            raise PermissionError(
                "employee_profile cannot update employee identity records directly"
            )
        if extension_update:
            result = await self._db.employee_profile_extensions.update_one(
                {"employee_id": employee_id},
                extension_update,
                upsert=True,
            )
            modified += int(result.modified_count or result.upserted_id is not None)

        await _refresh_profile_projection(
            self._db,
            employee_id,
            allow_identity_workflow=True,
        )
        return modified

    async def archive_and_delete_profile(
        self, *, profile: dict, actor_user_id: str
    ) -> None:
        archived = dict(profile)
        archived["deleted_at"] = datetime.now(timezone.utc).isoformat()
        archived["deleted_by"] = actor_user_id
        if _has_collection(self._db, "employee_profiles_deleted"):
            await self._db.employee_profiles_deleted.insert_one(archived)

        employee_id = profile.get("employee_id")
        if _has_collection(self._db, "employee_profile_extensions"):
            await self._db.employee_profile_extensions.delete_one({"employee_id": employee_id})
        if _has_collection(self._db, "employee_profile_read_models"):
            await self._db.employee_profile_read_models.delete_one({"employee_id": employee_id})
            await self._db.employee_master.delete_one({"employee_id": employee_id})

    async def count_profiles(self, *, query: dict) -> int:
        if _has_collection(self._db, "employee_profile_read_models"):
            await _backfill_missing_profile_projections(self._db)
            return int(await self._db.employee_profile_read_models.count_documents(query))
        return int(await self._db.employee_identities.count_documents(_profile_ready_identity_query(query)))

    async def list_profiles(
        self, *, query: dict, skip: int = 0, limit: int = 20, sort: list | None = None
    ) -> list[dict]:
        if _has_collection(self._db, "employee_profile_read_models"):
            await _backfill_missing_profile_projections(self._db)
            cursor = self._db.employee_profile_read_models.find(query, {"_id": 0})
            if sort:
                cursor = cursor.sort(sort)
            projected = await (
                cursor
                .skip(skip)
                .limit(limit)
                .to_list(length=limit)
            )
            return [normalize_employee_workflow_status(item) for item in projected]
        cursor = self._db.employee_identities.find(_profile_ready_identity_query(query), {"_id": 0})
        if sort:
            cursor = cursor.sort(sort)
        items = await cursor.skip(skip).limit(limit).to_list(length=limit)
        results: list[dict] = []
        for identity in items:
            profile = await _compose_live_profile(self._db, identity.get("employee_id"))
            results.append(normalize_employee_workflow_status(profile or identity))
        return results

    async def list_profiles_for_completion(
        self, *, query: dict, limit: int = 5000
    ) -> list[dict]:
        return await self.list_profiles(query=query, skip=0, limit=limit)

    async def list_audit_trail(
        self, *, employee_id: str, limit: int = 100
    ) -> list[dict]:
        cursor = self._db.profile_audit_logs_v2.find(
            {"employee_id": employee_id}, {"_id": 0}
        ).sort("timestamp", -1)
        return await cursor.to_list(length=limit)

    async def add_domain_violation_log(self, *, log: dict) -> None:
        await self._db.domain_violation_logs.insert_one(log)

    async def get_user_department_code(self, *, user_id: str) -> str | None:
        user_doc = await self._db.users.find_one(
            {"id": user_id}, {"_id": 0, "department_code": 1}
        )
        return (user_doc or {}).get("department_code")

    async def get_profile_department_code(self, *, employee_id: str) -> str | None:
        identity = await _find_identity_doc(self._db, employee_id)
        return (identity or {}).get("current_department_id")

    async def get_officer_profile_for_attestation(
        self, *, employee_id: str
    ) -> dict | None:
        identity = await _find_identity_doc(self._db, employee_id)
        if not identity:
            return None
        return {
            "full_name": identity.get("full_name"),
            "current_designation_id": identity.get("current_designation_id"),
            "employment_type": identity.get("employment_type"),
        }

    async def get_designation_name(self, *, code: str) -> str | None:
        designation = await self._db.designations.find_one(
            {"code": code}, {"_id": 0, "name": 1}
        )
        return (designation or {}).get("name")


class EmployeeProfileReadMongoGateway(EmployeeProfileReadGateway):
    def __init__(self, *, db) -> None:
        self._db = db

    async def get_profile(self, *, employee_id: str) -> dict | None:
        projected = await _get_refreshed_profile_projection(
            self._db,
            employee_id,
        )
        if projected:
            return normalize_employee_workflow_status(projected)
        profile = await _compose_live_profile(self._db, employee_id)
        return normalize_employee_workflow_status(profile) if profile else None

    async def count_profiles(self, *, query: dict) -> int:
        await _backfill_missing_profile_projections(self._db)
        projected_count = int(
            await self._db.employee_profile_read_models.count_documents(query)
        )
        if projected_count > 0 or not _should_fallback_to_identity_rows(query):
            return projected_count
        return int(await self._db.employee_identities.count_documents(_profile_ready_identity_query(query)))

    async def list_profiles(
        self, *, query: dict, skip: int = 0, limit: int = 20, sort: list | None = None
    ) -> list[dict]:
        await _backfill_missing_profile_projections(self._db)
        cursor = self._db.employee_profile_read_models.find(query, {"_id": 0})
        if sort:
            cursor = cursor.sort(sort)
        projected = await (
            cursor
            .skip(skip)
            .limit(limit)
            .to_list(length=limit)
        )
        if projected or not _should_fallback_to_identity_rows(query):
            return [normalize_employee_workflow_status(item) for item in projected]

        cursor = self._db.employee_identities.find(_profile_ready_identity_query(query), {"_id": 0})
        if sort:
            cursor = cursor.sort(sort)
        items = await cursor.skip(skip).limit(limit).to_list(length=limit)
        results: list[dict] = []
        for identity in items:
            profile = await _compose_live_profile(self._db, identity.get("employee_id"))
            results.append(normalize_employee_workflow_status(profile or identity))
        return results


class EmployeeProfileAuditMongoGateway(EmployeeProfileAuditGateway):
    def __init__(self, *, db) -> None:
        self._db = db

    async def write_workflow_audit(self, *, payload: EmployeeWorkflowAuditDTO) -> str:
        log = ProfileAuditLog(
            employee_id=payload.employee_id,
            action=payload.action,
            performed_by_id=payload.user_id,
            performed_by_name=payload.user_name,
            performed_by_role=payload.user_role,
            previous_data=payload.previous_data,
            new_data=payload.new_data,
            changed_fields=payload.changed_fields,
            workflow_status_before=payload.status_before,
            workflow_status_after=payload.status_after,
            remarks=payload.remarks,
            ip_address=payload.ip_address,
            user_agent=payload.user_agent,
        )
        data = log.model_dump()
        hash_str = f"{data.get('id')}:{data.get('employee_id')}:{data.get('action')}:{data.get('timestamp')}"
        log.integrity_hash = hashlib.sha256(hash_str.encode()).hexdigest()

        await self._db.profile_audit_logs_v2.insert_one(log.model_dump())
        return log.id
