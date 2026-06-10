from __future__ import annotations

from typing import Any

from contexts.employee_master.profile.domain.identity_layers import compose_employee_record_view
from contexts.employee_master.profile.read_model.infrastructure.repository import (
    EmployeeProfileReadModelRepository,
)


class EmployeeProfileReadModelService:
    def __init__(self, *, repo: EmployeeProfileReadModelRepository) -> None:
        self._repo = repo

    async def project_employee_identity_created(self, payload: dict[str, Any]) -> None:
        await self.project_employee_created({
            **payload,
            "identity_workflow_status": payload.get("identity_workflow_status") or payload.get("workflow_status") or "DRAFT",
            "workflow_status": "DRAFT",
        })

    async def project_employee_created(self, payload: dict[str, Any]) -> None:
        employee_id = str(payload.get("employee_id") or "").strip()
        if not employee_id:
            return

        projection = {
            "employee_id": employee_id,
            "employee_code": payload.get("employee_code"),
            "full_name": payload.get("full_name") or payload.get("name"),
            "gender": payload.get("gender"),
            "current_department_id": payload.get("current_department_id")
            or payload.get("dept_id"),
            "current_designation_id": payload.get("current_designation_id")
            or payload.get("designation_id"),
            "current_office_id": payload.get("current_office_id"),
            "reporting_officer_id": payload.get("reporting_officer_id"),
            "date_of_birth": payload.get("date_of_birth") or payload.get("dob"),
            "date_of_initial_engagement": payload.get("date_of_initial_engagement")
            or payload.get("doj"),
            "employment_type": payload.get("employment_type"),
            "employee_status": payload.get("employee_status") or "ACTIVE",
            "mobile_primary": payload.get("mobile_primary"),
            "email_official": payload.get("email_official"),
            "identity_workflow_status": payload.get("identity_workflow_status")
            or payload.get("workflow_status"),
            "status_effective_date": payload.get("status_effective_date"),
            "status_remarks": payload.get("status_remarks"),
            "workflow_status": "DRAFT",
            "version": payload.get("version") or 1,
            "created_at": payload.get("created_at"),
            "created_by": payload.get("created_by"),
            "updated_at": payload.get("updated_at") or payload.get("created_at"),
            "updated_by": payload.get("updated_by") or payload.get("created_by"),
        }
        await self._repo.upsert_projection(employee_id=employee_id, projection=projection)

    async def project_employee_updated(self, payload: dict[str, Any]) -> None:
        employee_id = str(payload.get("employee_id") or "").strip()
        if not employee_id:
            return

        patch = dict(payload.get("patch") or {})
        patch["updated_at"] = payload.get("updated_at")
        patch["version"] = payload.get("version")
        await self._repo.patch_projection(employee_id=employee_id, patch=patch)

    async def project_employee_status_changed(self, payload: dict[str, Any]) -> None:
        employee_id = str(payload.get("employee_id") or "").strip()
        if not employee_id:
            return

        await self._repo.patch_projection(
            employee_id=employee_id,
            patch={
                "employee_status": payload.get("new_status"),
                "status_effective_date": payload.get("effective_date"),
                "updated_at": payload.get("updated_at"),
                "version": payload.get("version"),
            },
        )

    async def get_profile(self, *, employee_id: str) -> dict[str, Any] | None:
        return await self._repo.get_profile(employee_id=employee_id)

    async def count_profiles(self, *, query: dict[str, Any]) -> int:
        return await self._repo.count_profiles(query=query)

    async def list_profiles(self, *, query: dict[str, Any], skip: int = 0, limit: int = 20) -> list[dict[str, Any]]:
        return await self._repo.list_profiles(query=query, skip=skip, limit=limit)

    async def rebuild_projection_from_identity(self, *, db) -> int:
        """Rebuild all profile read-models from canonical employee_identities.

        Safe to call repeatedly — uses upsert_projection which is idempotent.
        Returns the number of profiles rebuilt.
        """
        cursor = db.employee_identities.find({}, {"_id": 0})
        rebuilt = 0
        async for identity in cursor:
            employee_id = identity.get("employee_id")
            if not employee_id:
                continue
            payload = dict(identity)
            extension = None
            if getattr(db, "employee_profile_extensions", None) is not None:
                extension = await db.employee_profile_extensions.find_one(
                    {"employee_id": employee_id},
                    {"_id": 0},
                )
            if extension:
                payload = compose_employee_record_view(identity, extension)
                payload["identity_workflow_status"] = identity.get("workflow_status") or "DRAFT"
                payload["workflow_status"] = extension.get("workflow_status") or "DRAFT"
            await self.project_employee_created(payload)
            rebuilt += 1
        return rebuilt
