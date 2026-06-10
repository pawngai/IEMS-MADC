from __future__ import annotations

import pytest

from contexts.rbac.domain.models import Permission
from contexts.service_book.opening.api import router as opening_router


class _Cursor:
    def __init__(self, rows):
        self.rows = list(rows)

    def sort(self, *_args, **_kwargs):
        return self

    def limit(self, _limit):
        return self

    async def to_list(self, length=None):
        return self.rows[:length] if length else self.rows


class _Collection:
    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.updates = []

    async def find_one(self, query, projection=None):
        for row in self.rows:
            if all(row.get(key) == value for key, value in query.items()):
                if projection and projection.get("_id") == 0:
                    return {key: value for key, value in row.items() if key != "_id"}
                return dict(row)
        return None

    def find(self, query, projection=None):
        rows = []
        for row in self.rows:
            if all(row.get(key) == value for key, value in query.items()):
                rows.append({key: value for key, value in row.items() if key != "_id"})
        return _Cursor(rows)

    async def update_one(self, query, update, upsert=False):
        self.updates.append((query, update, upsert))
        existing = await self.find_one(query)
        payload = dict(update.get("$setOnInsert") or {})
        payload.update(update.get("$set") or {})
        if existing:
            existing.update(payload)
            self.rows = [existing if all(row.get(key) == value for key, value in query.items()) else row for row in self.rows]
        elif upsert:
            self.rows.append({**query, **payload})


class _Db:
    def __init__(self, *, identity, profile=None, opening=None):
        self.employee_identities = _Collection([identity])
        self.employee_profile_read_models = _Collection([profile or {}] if profile else [])
        self.employee_profile_extensions = _Collection([])
        self.service_book_openings = _Collection([opening] if opening else [])
        self.service_book_entries = _Collection([])
        self.employee_service_summaries = _Collection([])


def _user(*permissions):
    return {
        "sub": "actor-1",
        "authorities": ["GLOBAL_DATA_ENTRY"],
        "permissions": [permission.value if hasattr(permission, "value") else permission for permission in permissions],
    }


@pytest.mark.asyncio
async def test_opening_defaults_prefill_from_identity_profile_without_profile_write():
    db = _Db(
        identity={
            "employee_id": "EMP-1",
            "employee_code": "MADC-1",
            "full_name": "Identity Name",
            "employment_type": "REGULAR",
            "date_of_birth": "1990-01-01",
        },
        profile={"employee_id": "EMP-1", "father_name": "Profile Father"},
    )

    result = await opening_router.get_part_i_defaults(
        "EMP-1",
        current_user=_user(Permission.SERVICE_BOOK_READ_ALL),
        db=db,
    )

    assert result["part_i"]["name_in_block_letters"] == "IDENTITY NAME"
    assert result["part_i"]["father_name"] == "Profile Father"
    assert db.employee_profile_read_models.updates == []
    assert db.employee_profile_extensions.updates == []


@pytest.mark.asyncio
async def test_opening_workflow_returns_normalized_status_after_actions():
    complete_parts = {
        "part_i": {
            "employee_id": "EMP-1",
            "employee_code": "MADC-1",
            "name_in_block_letters": "DEMO",
            "father_name": "Demo Father",
            "marital_status": "SINGLE",
            "caste_category": "GENERAL",
            "date_of_birth_christian": "1990-01-01",
        },
        "part_iia": {
            "medical_fitness_certificate": True,
            "character_verification_done": True,
            "entries_confirmed": True,
        },
        "part_iib": {},
        "part_iii": {
            "previous_services": "[]",
            "foreign_services": "[]",
        },
    }
    db = _Db(
        identity={"employee_id": "EMP-1", "employee_code": "MADC-1", "employment_type": "REGULAR"},
        opening={"employee_id": "EMP-1", "status": "DRAFT", "parts": complete_parts, "documents": []},
    )

    submitted = await opening_router.submit_service_book_opening(
        "EMP-1",
        opening_router.OpeningRemarks(remarks="submit"),
        current_user=_user(Permission.SERVICE_BOOK_OPENING_SUBMIT),
        db=db,
    )
    assert submitted["status"] == "SUBMITTED"

    verified = await opening_router.verify_service_book_opening(
        "EMP-1",
        opening_router.OpeningRemarks(remarks="verify"),
        current_user=_user(Permission.SERVICE_BOOK_OPENING_VERIFY),
        db=db,
    )
    assert verified["status"] == "VERIFIED"

    approved = await opening_router.approve_service_book_opening(
        "EMP-1",
        opening_router.OpeningRemarks(remarks="approve"),
        current_user=_user(Permission.SERVICE_BOOK_OPENING_APPROVE),
        db=db,
    )
    assert approved["status"] == "LOCKED"
    projected_keys = {row.get("schema_key") for row in db.service_book_entries.rows}
    assert {"SB_I_BIODATA", "SB_IIA_IMMUTABLE_CERTS", "SB_III_TOTAL_QS_SUMMARY"}.issubset(projected_keys)
    assert db.employee_service_summaries.rows[0]["eligible_for_service_book"] is True


@pytest.mark.asyncio
async def test_opening_attach_document_persists_snapshot_document_reference():
    db = _Db(
        identity={"employee_id": "EMP-1", "employee_code": "MADC-1", "employment_type": "REGULAR"},
        opening={"employee_id": "EMP-1", "status": "DRAFT", "parts": {}, "documents": []},
    )

    result = await opening_router.attach_service_book_opening_document(
        "EMP-1",
        opening_router.OpeningDocumentLink(
            document_id="DOC-1",
            document_type="appointment",
            name="Appointment order",
            field_key="medical_fitness_certificate",
            field_label="Medical Fitness Certificate",
            part_id="part_iia",
        ),
        current_user=_user(Permission.SERVICE_BOOK_OPENING_UPDATE),
        db=db,
    )

    assert result["documents"][0]["document_id"] == "DOC-1"
    assert result["documents"][0]["name"] == "Appointment order"
    assert result["documents"][0]["field_key"] == "medical_fitness_certificate"
    assert result["documents"][0]["part_id"] == "part_iia"


@pytest.mark.asyncio
async def test_opening_response_preserves_part_iii_payload():
    db = _Db(
        identity={"employee_id": "EMP-1", "employee_code": "MADC-1", "employment_type": "REGULAR"},
        opening={
            "employee_id": "EMP-1",
            "status": "DRAFT",
            "parts": {
                "part_i": {},
                "part_iia": {},
                "part_iib": {},
                "part_iii": {
                    "previous_services": "[{\"post_held\": \"Assistant\"}]",
                    "foreign_services": "[]",
                    "part_iii_verified": True,
                },
            },
            "documents": [],
        },
    )

    result = await opening_router.get_service_book_opening(
        "EMP-1",
        current_user=_user(Permission.SERVICE_BOOK_READ_ALL),
        db=db,
    )

    assert result["parts"]["part_iii"]["previous_services"] == "[{\"post_held\": \"Assistant\"}]"
    assert result["parts"]["part_iii"]["part_iii_verified"] is True


@pytest.mark.asyncio
async def test_update_opening_draft_does_not_set_created_at_on_existing_record():
    db = _Db(
        identity={"employee_id": "EMP-1", "employee_code": "MADC-1", "employment_type": "REGULAR"},
        opening={
            "employee_id": "EMP-1",
            "status": "DRAFT",
            "workflow_status": "DRAFT",
            "created_at": "2026-06-01T00:00:00+00:00",
            "parts": {"part_i": {}, "part_iia": {}, "part_iib": {}, "part_iii": {}},
            "documents": [],
        },
    )

    payload = opening_router.ServiceBookOpeningPayload(
        employee_id="EMP-1",
        parts={"part_iia": {"medical_fitness_certificate": True}},
        documents=[],
    )

    await opening_router.update_service_book_opening_draft(
        "EMP-1",
        payload,
        current_user=_user(Permission.SERVICE_BOOK_OPENING_UPDATE),
        db=db,
    )

    _query, update, _upsert = db.service_book_openings.updates[-1]
    assert "created_at" not in update["$set"]
    assert update["$setOnInsert"]["created_at"] == "2026-06-01T00:00:00+00:00"
