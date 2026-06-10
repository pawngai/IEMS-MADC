from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from contexts.employee_master.identity.contracts.events import (
    EmployeeCreatedEvent,
    EmployeeIdentityCreatedEvent,
    EmployeeStatusChangedEvent,
    EmployeeUpdatedEvent,
)
from app_platform.db.atomic import call_with_optional_session, run_atomic
from app_platform.domain_separation.data_ownership import assert_collection_ownership
from app_platform.event_bus.types import EventName
from app_platform.outbox.model import OutboxEvent
from app_platform.outbox.repo import OutboxRepository
from contexts.employee_master.identity.domain.employee_code import format_employee_code
from contexts.employee_master.identity.schemas.enums import EmployeeStatus

_IDENTITY_WORKFLOW_DRAFT = "DRAFT"
_PROFILE_OWNED_IDENTITY_FIELDS = {
    "employment_type",
    "date_of_initial_engagement",
    "current_department_id",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sanitize_identity_record(identity: dict[str, Any] | None) -> dict[str, Any] | None:
    if not identity:
        return None
    sanitized = dict(identity)
    sanitized.pop("aadhaar_number", None)
    return sanitized


class EmployeeIdentityRepository:
    def __init__(self, *, db, outbox_repo: OutboxRepository | None = None) -> None:
        assert_collection_ownership(
            context="employee_master",
            collection_name="employee_identities",
            write=True,
        )
        assert_collection_ownership(
            context="employee_master",
            collection_name="counters",
            write=True,
        )
        self._db = db
        self._outbox_repo = outbox_repo or OutboxRepository(db)

    async def get_identity(
        self,
        *,
        employee_id: str,
        projection: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        identity = await self._db.employee_identities.find_one(
            {"employee_id": employee_id},
            projection or {"_id": 0},
        )
        return _sanitize_identity_record(identity)

    async def count_identities(self, *, query: dict[str, Any]) -> int:
        return int(await self._db.employee_identities.count_documents(query))

    async def list_identities(
        self, *, query: dict[str, Any], skip: int = 0, limit: int = 20
    ) -> list[dict[str, Any]]:
        identities = await (
            self._db.employee_identities.find(query, {"_id": 0})
            .sort("full_name", 1)
            .skip(skip)
            .limit(limit)
            .to_list(length=limit)
        )
        return [_sanitize_identity_record(identity) or {} for identity in identities]

    async def delete_identity(self, *, employee_id: str) -> dict[str, Any] | None:
        identity = await self.get_identity(employee_id=employee_id)
        if not identity:
            return None
        await self._db.employee_identities.delete_one({"employee_id": employee_id})
        return identity

    async def create_identity(
        self,
        *,
        payload: dict[str, Any],
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        payload = {
            key: value
            for key, value in payload.items()
            if key != "aadhaar_number" and key not in _PROFILE_OWNED_IDENTITY_FIELDS
        }

        employee_id = str(uuid.uuid4())
        async def _operation(session):
            employee_code = await self._generate_employee_code(payload, session=session)
            now = utc_now_iso()

            identity = {
                "employee_id": employee_id,
                "employee_code": employee_code,
                "full_name": payload["full_name"],
                "gender": payload["gender"],
                "date_of_birth": payload["date_of_birth"],
                "current_designation_id": payload.get("current_designation_id"),
                "current_office_id": payload.get("current_office_id"),
                "reporting_officer_id": payload.get("reporting_officer_id"),
                "employee_status": payload.get("employee_status") or EmployeeStatus.ACTIVE.value,
                "mobile_primary": payload.get("mobile_primary"),
                "email_official": payload.get("email_official"),
                "status_effective_date": payload.get("status_effective_date"),
                "status_remarks": payload.get("status_remarks"),
                "workflow_status": _IDENTITY_WORKFLOW_DRAFT,
                "created_at": now,
                "created_by": actor_user_id,
                "updated_at": now,
                "updated_by": actor_user_id,
                "version": 1,
            }
            await call_with_optional_session(
                self._db.employee_identities.insert_one,
                identity,
                session=session,
            )

            await self._publish_identity_created(identity=identity, session=session)
            await self._publish_created(identity=identity, session=session)
            return identity

        # EmployeeCreated starts downstream projections immediately; activation
        # republishes it with ACTIVE workflow metadata for idempotent consumers.
        return await run_atomic(self._db, _operation)

    async def _publish_identity_created(self, *, identity: dict[str, Any], session=None) -> None:
        payload = EmployeeIdentityCreatedEvent(
            employee_id=identity["employee_id"],
            employee_code=identity.get("employee_code"),
            dept_id=identity.get("current_department_id"),
            current_department_id=identity.get("current_department_id"),
            name=identity.get("full_name") or "",
            full_name=identity.get("full_name") or "",
            gender=identity.get("gender"),
            dob=identity.get("date_of_birth"),
            date_of_birth=identity.get("date_of_birth"),
            doj=identity.get("date_of_initial_engagement"),
            date_of_initial_engagement=identity.get("date_of_initial_engagement"),
            employment_type=identity.get("employment_type"),
            designation_id=identity.get("current_designation_id"),
            current_designation_id=identity.get("current_designation_id"),
            current_office_id=identity.get("current_office_id"),
            reporting_officer_id=identity.get("reporting_officer_id"),
            employee_status=identity.get("employee_status"),
            mobile_primary=identity.get("mobile_primary"),
            email_official=identity.get("email_official"),
            identity_workflow_status=identity.get("workflow_status") or _IDENTITY_WORKFLOW_DRAFT,
            workflow_status=identity.get("workflow_status") or _IDENTITY_WORKFLOW_DRAFT,
            status_effective_date=identity.get("status_effective_date"),
            status_remarks=identity.get("status_remarks"),
            created_at=identity.get("created_at") or utc_now_iso(),
            updated_at=identity.get("updated_at"),
            created_by=identity.get("created_by"),
            updated_by=identity.get("updated_by"),
            version=int(identity.get("version") or 1),
        )
        await call_with_optional_session(
            self._outbox_repo.add_event,
            OutboxEvent(
                name=EventName.EMPLOYEE_IDENTITY_CREATED.value,
                payload=payload.model_dump(mode="json"),
                actor_id=identity.get("created_by"),
                department_id=identity.get("current_department_id"),
            ),
            session=session,
        )

    async def update_identity(
        self,
        *,
        employee_id: str,
        patch: dict[str, Any],
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        current = await self.get_identity(employee_id=employee_id)
        if not current:
            raise LookupError(employee_id)

        patch = {
            key: value
            for key, value in patch.items()
            if key != "aadhaar_number" and key not in _PROFILE_OWNED_IDENTITY_FIELDS
        }
        if not patch:
            return current

        next_version = int(current.get("version") or 1) + 1
        updated_at = utc_now_iso()
        mongo_patch = {
            **patch,
            "updated_at": updated_at,
            "updated_by": actor_user_id,
            "version": next_version,
        }
        async def _operation(session):
            await call_with_optional_session(
                self._db.employee_identities.update_one,
                {"employee_id": employee_id},
                {"$set": mongo_patch},
                session=session,
            )
            updated = {**current, **mongo_patch}
            await self._publish_updated(
                employee_id=employee_id,
                patch=patch,
                updated_at=updated_at,
                version=next_version,
                session=session,
            )

            previous_status = current.get("employee_status")
            next_status = patch.get("employee_status")
            if next_status and next_status != previous_status:
                await self._publish_status_changed(
                    employee_id=employee_id,
                    old_status=str(previous_status) if previous_status else None,
                    new_status=str(next_status),
                    effective_date=patch.get("status_effective_date")
                    or updated.get("status_effective_date"),
                    updated_at=updated_at,
                    version=next_version,
                    session=session,
                )
            return updated

        return await run_atomic(self._db, _operation)

    async def transition_workflow(
        self,
        *,
        employee_id: str,
        new_status: str,
        actor_user_id: str | None,
        remarks: str | None = None,
    ) -> dict[str, Any]:
        """Persist a workflow status transition and publish the matching event.

        When new_status is ACTIVE the full EmployeeCreated event is published
        so downstream contexts (EmployeeProfile, ServiceBook) are initialised.
        """
        identity = await self.get_identity(employee_id=employee_id)
        if not identity:
            raise LookupError(employee_id)

        now = utc_now_iso()
        next_version = int(identity.get("version") or 1) + 1
        patch: dict[str, Any] = {
            "workflow_status": new_status,
            "updated_at": now,
            "updated_by": actor_user_id,
            "version": next_version,
        }
        if new_status == "REJECTED" and remarks:
            patch["rejection_remarks"] = remarks
        if new_status == "VERIFIED":
            patch["verified_by"] = actor_user_id
        if new_status == "ACTIVE":
            patch["activated_by"] = actor_user_id

        async def _operation(session):
            await call_with_optional_session(
                self._db.employee_identities.update_one,
                {"employee_id": employee_id},
                {"$set": patch},
                session=session,
            )
            updated = {**identity, **patch}

            event_name_map = {
                "SUBMITTED": EventName.EMPLOYEE_IDENTITY_SUBMITTED.value,
                "VERIFIED": EventName.EMPLOYEE_IDENTITY_VERIFIED.value,
                "REJECTED": EventName.EMPLOYEE_IDENTITY_REJECTED.value,
                "ACTIVE": EventName.EMPLOYEE_IDENTITY_ACTIVATED.value,
            }
            event_name = event_name_map.get(new_status)
            if event_name:
                await self._publish_identity_workflow_event(
                    event_name=event_name,
                    identity=updated,
                    action=new_status,
                    actor_user_id=actor_user_id,
                    remarks=remarks,
                    session=session,
                )

            if new_status == "ACTIVE":
                await self._publish_created(identity=updated, session=session)
            return updated

        return await run_atomic(self._db, _operation)

    async def _generate_employee_code(self, payload: dict[str, Any], session=None) -> str:
        year = datetime.now(timezone.utc).year
        counter_id = "employee_code"
        counter = await call_with_optional_session(
            self._db.counters.find_one_and_update,
            {"_id": counter_id},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True,
            session=session,
        )
        seq = int((counter or {}).get("seq") or 1)
        return format_employee_code(
            year=year,
            employment_type="IDENTITY",
            sequence=seq,
        )

    async def _publish_created(self, *, identity: dict[str, Any], session=None) -> None:
        payload = EmployeeCreatedEvent(
            employee_id=identity["employee_id"],
            employee_code=identity.get("employee_code"),
            dept_id=identity.get("current_department_id"),
            current_department_id=identity.get("current_department_id"),
            name=identity.get("full_name") or "",
            full_name=identity.get("full_name") or "",
            gender=identity.get("gender"),
            dob=identity.get("date_of_birth"),
            date_of_birth=identity.get("date_of_birth"),
            doj=identity.get("date_of_initial_engagement"),
            date_of_initial_engagement=identity.get("date_of_initial_engagement"),
            employment_type=identity.get("employment_type"),
            designation_id=identity.get("current_designation_id"),
            current_designation_id=identity.get("current_designation_id"),
            current_office_id=identity.get("current_office_id"),
            reporting_officer_id=identity.get("reporting_officer_id"),
            employee_status=identity.get("employee_status"),
            mobile_primary=identity.get("mobile_primary"),
            email_official=identity.get("email_official"),
            identity_workflow_status=identity.get("workflow_status"),
            workflow_status=identity.get("workflow_status"),
            status_effective_date=identity.get("status_effective_date"),
            status_remarks=identity.get("status_remarks"),
            created_at=identity.get("created_at") or utc_now_iso(),
            updated_at=identity.get("updated_at"),
            created_by=identity.get("created_by"),
            updated_by=identity.get("updated_by"),
            version=int(identity.get("version") or 1),
        )
        await call_with_optional_session(
            self._outbox_repo.add_event,
            OutboxEvent(
                name=EventName.EMPLOYEE_CREATED.value,
                payload=payload.model_dump(mode="json"),
                actor_id=identity.get("created_by"),
                department_id=identity.get("current_department_id"),
            ),
            session=session,
        )

    async def _publish_updated(
        self,
        *,
        employee_id: str,
        patch: dict[str, Any],
        updated_at: str,
        version: int,
        session=None,
    ) -> None:
        payload = EmployeeUpdatedEvent(
            employee_id=employee_id,
            patch=patch,
            updated_at=updated_at,
            version=version,
        )
        await call_with_optional_session(
            self._outbox_repo.add_event,
            OutboxEvent(
                name=EventName.EMPLOYEE_UPDATED.value,
                payload=payload.model_dump(mode="json"),
                department_id=None,
            ),
            session=session,
        )

    async def _publish_status_changed(
        self,
        *,
        employee_id: str,
        old_status: str | None,
        new_status: str,
        effective_date: str | None,
        updated_at: str,
        version: int,
        session=None,
    ) -> None:
        payload = EmployeeStatusChangedEvent(
            employee_id=employee_id,
            old_status=old_status,
            new_status=new_status,
            effective_date=effective_date,
            updated_at=updated_at,
            version=version,
        )
        await call_with_optional_session(
            self._outbox_repo.add_event,
            OutboxEvent(
                name=EventName.EMPLOYEE_STATUS_CHANGED.value,
                payload=payload.model_dump(mode="json"),
            ),
            session=session,
        )

    async def _publish_identity_workflow_event(
        self,
        *,
        event_name: str,
        identity: dict[str, Any],
        action: str,
        actor_user_id: str | None,
        remarks: str | None = None,
        session=None,
    ) -> None:
        payload: dict[str, Any] = {
            "employee_id": identity["employee_id"],
            "employee_code": identity.get("employee_code"),
            "action": action,
            "workflow_status": identity.get("workflow_status"),
            "actor_user_id": actor_user_id,
            "updated_at": identity.get("updated_at") or utc_now_iso(),
            "version": identity.get("version"),
        }
        if remarks:
            payload["remarks"] = remarks
        await call_with_optional_session(
            self._outbox_repo.add_event,
            OutboxEvent(
                name=event_name,
                payload=payload,
                actor_id=actor_user_id,
                department_id=None,
            ),
            session=session,
        )
