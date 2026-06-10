from __future__ import annotations

from typing import Any

from contexts.employee_identity.contracts.identity_directory import (
    find_identity,
    find_identities_by_ids,
    resolve_identity_ref,
)
from contexts.employee_profile.contracts.profile_directory import find_profile_view
from contexts.rbac.application.access_control import (
    require_owner_or_permissions,
    require_permissions,
)
from contexts.rbac.domain.models import Permission
from contexts.service_book.application.dto.filters import ServiceBookFilter
from contexts.service_book.application.errors import not_found
from contexts.service_book.application.service import (
    rebuildServiceBookProjection,
    validateServiceBookEligibility,
)
from contexts.service_book.repository.ports import ServiceBookEntryRepositoryPort
from contexts.service_book.records.contracts.service_summary_directory import (
    get_employee_service_summary,
)
from shared_kernel.events import utc_now_iso


IDENTITY_PROJECTION = {
    "_id": 0,
    "full_name": 1,
    "date_of_birth": 1,
    "employee_code": 1,
    "employment_type": 1,
}

PROFILE_PROJECTION = {
    "_id": 0,
    "father_name": 1,
    "mother_name": 1,
    "spouse_name": 1,
    "marital_status": 1,
    "category": 1,
    "nationality": 1,
    "date_of_birth_saka": 1,
    "height_cm": 1,
    "identification_marks": 1,
    "educational_qualifications_initial": 1,
    "educational_qualifications_acquired": 1,
    "professional_qualifications": 1,
    "photo_url": 1,
    "signature_url": 1,
    "thumb_impression_url": 1,
}


async def resolve_employee_identity(db, employee_ref: str) -> dict[str, Any] | None:
    return await resolve_identity_ref(db, ref=employee_ref)


def build_opening_part_i_defaults(
    identity: dict[str, Any] | None,
    profile: dict[str, Any] | None,
) -> dict[str, Any]:
    def coalesce(*values: Any) -> Any:
        for value in values:
            if value is not None and str(value).strip() != "":
                return value
        return ""

    ident = identity or {}
    prof = profile or {}
    return {
        "employee_id": coalesce(ident.get("employee_id"), prof.get("employee_id")),
        "employee_code": coalesce(ident.get("employee_code"), prof.get("employee_code")),
        "name_in_block_letters": str(
            coalesce(
                ident.get("name_in_block_letters"),
                ident.get("full_name"),
                prof.get("name_in_block_letters"),
                prof.get("full_name"),
                prof.get("name"),
            )
        ).upper(),
        "date_of_birth_christian": coalesce(
            ident.get("date_of_birth_christian"),
            ident.get("date_of_birth"),
            prof.get("date_of_birth_christian"),
            prof.get("date_of_birth"),
        ),
        "father_name": coalesce(ident.get("father_name"), prof.get("father_name")),
        "mother_name": coalesce(ident.get("mother_name"), prof.get("mother_name")),
        "spouse_name": coalesce(ident.get("spouse_name"), prof.get("spouse_name")),
        "marital_status": coalesce(ident.get("marital_status"), prof.get("marital_status")),
        "nationality": coalesce(ident.get("nationality"), prof.get("nationality")),
        "caste_category": coalesce(
            ident.get("caste_category"),
            ident.get("category"),
            prof.get("caste_category"),
            prof.get("category"),
        ),
        "religion": coalesce(ident.get("religion"), prof.get("religion")),
        "blood_group": coalesce(ident.get("blood_group"), prof.get("blood_group")),
        "place_of_birth": coalesce(ident.get("place_of_birth"), prof.get("place_of_birth")),
        "height_cm": coalesce(ident.get("height_cm"), prof.get("height_cm")),
        "identification_marks": coalesce(ident.get("identification_marks"), prof.get("identification_marks")),
        "permanent_address_line1": coalesce(
            ident.get("permanent_address_line1"),
            prof.get("permanent_address_line1"),
        ),
        "permanent_address_line2": coalesce(
            ident.get("permanent_address_line2"),
            prof.get("permanent_address_line2"),
        ),
        "educational_qualifications_initial": coalesce(
            ident.get("educational_qualifications_initial"),
            prof.get("educational_qualifications_initial"),
        ),
        "educational_qualifications_acquired": coalesce(
            ident.get("educational_qualifications_acquired"),
            prof.get("educational_qualifications_acquired"),
        ),
        "professional_qualifications": coalesce(
            ident.get("professional_qualifications"),
            prof.get("professional_qualifications"),
        ),
        "attesting_officer_name": coalesce(
            ident.get("attesting_officer_name"),
            prof.get("attesting_officer_name"),
        ),
        "attesting_officer_designation": coalesce(
            ident.get("attesting_officer_designation"),
            prof.get("attesting_officer_designation"),
        ),
    }


async def get_opening_part_i_defaults(
    db,
    *,
    employee_ref: str,
    identity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_identity = identity or await resolve_employee_identity(db, employee_ref)
    if not resolved_identity:
        return {}
    employee_id = str(resolved_identity.get("employee_id") or employee_ref).strip()
    profile = await find_profile_view(db, employee_id=employee_id)
    defaults = build_opening_part_i_defaults(resolved_identity, profile)
    defaults["employee_id"] = employee_id
    return defaults


def build_part_i_defaults(
    identity: dict[str, Any] | None,
    profile: dict[str, Any] | None,
) -> dict[str, Any]:
    ident = identity or {}
    prof = profile or {}
    defaults: dict[str, Any] = {}

    full_name = str(ident.get("full_name") or "").strip()
    if full_name:
        defaults["name_in_block_letters"] = full_name.upper()
    if ident.get("date_of_birth"):
        defaults["date_of_birth_christian"] = ident["date_of_birth"]
    if ident.get("employee_code"):
        defaults["employee_code"] = ident["employee_code"]

    direct_fields = {
        "father_name": "father_name",
        "spouse_name": "spouse_name",
        "marital_status": "marital_status",
        "nationality": "nationality",
        "date_of_birth_saka": "date_of_birth_saka",
        "height_cm": "height_cm",
        "identification_marks": "identification_marks",
        "educational_qualifications_initial": "educational_qualifications_initial",
        "educational_qualifications_acquired": "educational_qualifications_acquired",
        "professional_qualifications": "professional_qualifications",
        "signature_url": "signature_url",
        "thumb_impression_url": "thumb_impression_url",
    }
    for src_key, dest_key in direct_fields.items():
        value = prof.get(src_key)
        if value is not None and value != "" and value != []:
            defaults[dest_key] = value

    if prof.get("category"):
        defaults["caste_category"] = prof["category"]
    if prof.get("photo_url"):
        defaults["photograph_url"] = prof["photo_url"]
    if defaults.get("father_name"):
        defaults["parent_name"] = defaults["father_name"]

    return defaults


class ServiceBookQueryUseCases:
    def __init__(self, *, db, read_service, entry_repo: ServiceBookEntryRepositoryPort) -> None:
        self._db = db
        self._read_service = read_service
        self._entry_repo = entry_repo

    async def resolve_employee(self, employee_ref: str) -> tuple[str, dict[str, Any]]:
        identity = await resolve_identity_ref(self._db, ref=employee_ref)
        if not identity:
            raise not_found("Employee not found")
        return identity["employee_id"], identity

    async def eligibility_subject(self, *, employee_id: str, identity: dict[str, Any]) -> dict[str, Any]:
        summary = await get_employee_service_summary(self._db, employee_id=employee_id)
        if summary is not None:
            return summary
        return identity

    def require_read_access(self, current_user: dict, employee_id: str) -> None:
        require_owner_or_permissions(
            current_user,
            employee_id,
            Permission.SERVICE_BOOK_READ_OWN,
            Permission.SERVICE_BOOK_READ_ALL,
        )

    async def get_service_book(self, *, employee_ref: str, current_user: dict) -> dict:
        resolved_id, identity = await self.resolve_employee(employee_ref)
        self.require_read_access(current_user, resolved_id)
        subject = await self.eligibility_subject(employee_id=resolved_id, identity=identity)
        validateServiceBookEligibility(subject)
        return await rebuildServiceBookProjection(
            db=self._db,
            employee_id=resolved_id,
            employee_or_type=subject,
        )

    async def get_part(self, *, employee_ref: str, part_code: str, current_user: dict) -> dict | None:
        resolved_id, identity = await self.resolve_employee(employee_ref)
        self.require_read_access(current_user, resolved_id)
        validateServiceBookEligibility(
            await self.eligibility_subject(employee_id=resolved_id, identity=identity)
        )
        resolved_part_code = self._read_service.normalize_part_code(part_code)
        if not resolved_part_code:
            return None
        return await self._read_service.get_service_book_part(
            employee_id=resolved_id,
            part_code=resolved_part_code,
        )

    async def list_entries(
        self,
        *,
        employee_ref: str,
        filters: ServiceBookFilter,
        current_user: dict,
    ) -> list[dict]:
        resolved_id, identity = await self.resolve_employee(employee_ref)
        self.require_read_access(current_user, resolved_id)
        validateServiceBookEligibility(
            await self.eligibility_subject(employee_id=resolved_id, identity=identity)
        )
        return await self._read_service.list_service_book_entries(
            employee_id=resolved_id,
            filters=filters.model_dump(exclude_none=True),
        )

    async def list_queue(
        self,
        *,
        workflow_state: str | None,
        page_size: int,
        current_user: dict,
        workflow_states: list[str] | None = None,
    ) -> dict:
        require_permissions(current_user, Permission.SERVICE_BOOK_READ_ALL)
        entries = await self._entry_repo.list_queue_entries(
            workflow_state=workflow_state,
            page_size=page_size,
            workflow_states=workflow_states,
        )
        if not entries:
            return {"entries": []}

        employee_ids = list({entry["employee_id"] for entry in entries})
        identities = await find_identities_by_ids(
            self._db,
            employee_ids=employee_ids,
            projection={"_id": 0, "employee_id": 1, "full_name": 1, "employee_code": 1},
        )
        id_map = {identity["employee_id"]: identity for identity in identities}
        enriched_entries = []
        for entry in entries:
            ident = id_map.get(entry["employee_id"])
            if not ident:
                continue
            enriched = dict(entry)
            enriched["full_name"] = ident.get("full_name", "")
            enriched["employee_code"] = ident.get("employee_code", "")
            enriched_entries.append(enriched)
        return {"entries": enriched_entries}

    async def get_schema(self, *, part_key: str, current_user: dict) -> dict:
        require_permissions(
            current_user,
            Permission.SERVICE_BOOK_READ_ALL,
            Permission.AUDIT_READ_ALL,
        )
        schema = await self._read_service.get_part_schema(part_key=part_key)
        schema["generated_at"] = utc_now_iso()
        return schema

    async def get_part_i_defaults(self, *, employee_ref: str, current_user: dict) -> dict:
        resolved_id, _identity = await self.resolve_employee(employee_ref)
        self.require_read_access(current_user, resolved_id)
        identity = await find_identity(
            self._db,
            employee_id=resolved_id,
            projection=IDENTITY_PROJECTION,
        )
        validateServiceBookEligibility(identity)
        profile = await find_profile_view(
            self._db,
            employee_id=resolved_id,
            projection=PROFILE_PROJECTION,
        )
        defaults = build_part_i_defaults(identity, profile)
        defaults["employee_id"] = resolved_id
        return defaults
