from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from contexts.employee_identity.domain.employee_code import parse_employee_code
from contexts.employee_identity.application.identity_interface import get_employee_identity
from contexts.employee_identity.repository.identity_repository import EmployeeIdentityRepository
from contexts.employee_identity.schemas.commands import EmployeeIdentityCreate, EmployeeIdentityUpdate
from contexts.employee_identity.schemas.enums import Gender


class _FakeEmployeeIdentitiesCollection:
    def __init__(self) -> None:
        self.docs: list[dict] = []

    def find(self, query, projection=None):
        docs = []
        for doc in self.docs:
            matched = True
            for key, value in query.items():
                if doc.get(key) != value:
                    matched = False
                    break
            if not matched:
                continue
            if projection:
                included_fields = [
                    key for key, enabled in projection.items() if key != "_id" and enabled
                ]
                if included_fields:
                    docs.append({key: doc.get(key) for key in included_fields if key in doc})
                else:
                    docs.append(dict(doc))
            else:
                docs.append(dict(doc))
        return _FakeCursor(docs)

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            matched = True
            for key, value in query.items():
                if doc.get(key) != value:
                    matched = False
                    break
            if matched:
                if projection:
                    included_fields = [
                        key for key, enabled in projection.items() if key != "_id" and enabled
                    ]
                    if included_fields:
                        return {key: doc.get(key) for key in included_fields if key in doc}
                    return dict(doc)
                return dict(doc)
        return None

    async def insert_one(self, doc):
        self.docs.append(dict(doc))

    async def update_one(self, query, update):
        for index, doc in enumerate(self.docs):
            if doc.get("employee_id") != query.get("employee_id"):
                continue

            next_doc = dict(doc)
            for key, value in update.get("$set", {}).items():
                next_doc[key] = value
            self.docs[index] = next_doc
            return

        raise AssertionError("employee identity not found for update")


class _FakeCountersCollection:
    def __init__(self) -> None:
        self.seqs: dict[str, int] = {}

    async def find_one_and_update(self, query, _update, upsert=False, return_document=True):
        counter_id = str(query.get("_id"))
        self.seqs[counter_id] = self.seqs.get(counter_id, 0) + 1
        return {"_id": counter_id, "seq": self.seqs[counter_id]}


class _FakeOutboxRepo:
    def __init__(self) -> None:
        self.events = []

    async def add_event(self, event):
        self.events.append(event)


class _FakeCursor:
    def __init__(self, docs: list[dict]) -> None:
        self._docs = docs

    def sort(self, *_args, **_kwargs):
        return self

    def skip(self, count):
        self._docs = self._docs[count:]
        return self

    def limit(self, count):
        self._docs = self._docs[:count]
        return self

    async def to_list(self, *, length):
        return self._docs[:length]


class _FakeDb:
    def __init__(self) -> None:
        self.employee_identities = _FakeEmployeeIdentitiesCollection()
        self.counters = _FakeCountersCollection()


def test_employee_identity_create_rejects_aadhaar_number_as_non_identity_field() -> None:
    with pytest.raises(ValidationError) as exc_info:
        EmployeeIdentityCreate(
            full_name="Test Employee",
            gender=Gender.MALE,
            date_of_birth="1990-01-15",
            aadhaar_number="12345",
        )

    assert "aadhaar_number" in str(exc_info.value)
    assert "Move non-identity fields to their owning context" in str(exc_info.value)


def test_employee_identity_create_rejects_profile_owned_assignment_fields() -> None:
    with pytest.raises(ValidationError, match="core identity fields"):
        EmployeeIdentityCreate(
            full_name="Test Employee",
            gender=Gender.MALE,
            date_of_birth="1990-01-15",
            employment_type="REGULAR",
            current_department_id="FIN",
        )


def test_employee_identity_update_rejects_invalid_status_effective_date() -> None:
    with pytest.raises(ValidationError, match="Date must be in YYYY-MM-DD format"):
        EmployeeIdentityUpdate(status_effective_date="01-04-2020")


def test_employee_identity_accepts_provisioning_contact_fields() -> None:
    model = EmployeeIdentityCreate(
        full_name="Contact Employee",
        gender=Gender.MALE,
        date_of_birth="1990-01-15",
        mobile_primary="9862000001",
        email_official="Contact.Employee@MADC.GOV.IN",
    )

    assert model.mobile_primary == "9862000001"
    assert model.email_official == "contact.employee@madc.gov.in"


def test_employee_identity_rejects_invalid_provisioning_contact_fields() -> None:
    with pytest.raises(ValidationError, match="Invalid Indian mobile number"):
        EmployeeIdentityCreate(
            full_name="Contact Employee",
            gender=Gender.MALE,
            date_of_birth="1990-01-15",
            mobile_primary="12345",
        )

    with pytest.raises(ValidationError, match="Invalid email address"):
        EmployeeIdentityUpdate(email_official="not-an-email")


def test_employee_identity_update_rejects_aadhaar_number_as_non_identity_field() -> None:
    with pytest.raises(ValidationError) as exc_info:
        EmployeeIdentityUpdate(aadhaar_number="123456789012")

    assert "aadhaar_number" in str(exc_info.value)
    assert "Move non-identity fields to their owning context" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_identity_generates_madc_code_with_global_serials() -> None:
    db = _FakeDb()
    repo = EmployeeIdentityRepository(db=db, outbox_repo=_FakeOutboxRepo())

    first = await repo.create_identity(
        payload={
            "full_name": "One User",
            "gender": "Male",
            "date_of_birth": "1990-01-15",
        },
        actor_user_id="u1",
    )
    second = await repo.create_identity(
        payload={
            "full_name": "Two User",
            "gender": "Female",
            "date_of_birth": "1991-01-15",
        },
        actor_user_id="u2",
    )
    third = await repo.create_identity(
        payload={
            "full_name": "Three User",
            "gender": "Male",
            "date_of_birth": "1992-01-15",
        },
        actor_user_id="u3",
    )

    assert first["employee_code"] == "MADC-0001"
    assert second["employee_code"] == "MADC-0002"
    assert third["employee_code"] == "MADC-0003"


def test_parse_employee_code_accepts_current_and_legacy_formats() -> None:
    assert parse_employee_code("MADC-0007") == (None, None, 7)
    assert parse_employee_code("MADC-2026-I0007") == (2026, "I", 7)


@pytest.mark.asyncio
async def test_create_identity_ignores_aadhaar_number_payload() -> None:
    db = _FakeDb()
    repo = EmployeeIdentityRepository(db=db, outbox_repo=_FakeOutboxRepo())

    created = await repo.create_identity(
        payload={
            "full_name": "Draft Projection User",
            "gender": "Female",
            "date_of_birth": "1990-01-15",
            "aadhaar_number": "123456789012",
        },
        actor_user_id="u1",
    )

    assert "aadhaar_number" not in created
    assert "aadhaar_number" not in db.employee_identities.docs[0]


@pytest.mark.asyncio
async def test_update_identity_ignores_aadhaar_number_patch() -> None:
    db = _FakeDb()
    repo = EmployeeIdentityRepository(db=db, outbox_repo=_FakeOutboxRepo())

    created = await repo.create_identity(
        payload={
            "full_name": "One User",
            "gender": "Male",
            "date_of_birth": "1990-01-15",
        },
        actor_user_id="u1",
    )

    updated = await repo.update_identity(
        employee_id=created["employee_id"],
        patch={"aadhaar_number": "123456789012"},
        actor_user_id="u2",
    )

    assert "aadhaar_number" not in updated
    assert "aadhaar_number" not in db.employee_identities.docs[0]


@pytest.mark.asyncio
async def test_get_identity_strips_legacy_aadhaar_number() -> None:
    db = _FakeDb()
    db.employee_identities.docs.append(
        {
            "employee_id": "EMP-1",
            "employee_code": "MADC-2024-R0001",
            "full_name": "Legacy User",
            "aadhaar_number": "123456789012",
        }
    )

    repo = EmployeeIdentityRepository(db=db, outbox_repo=_FakeOutboxRepo())
    identity = await repo.get_identity(employee_id="EMP-1")

    assert identity is not None
    assert "aadhaar_number" not in identity


@pytest.mark.asyncio
async def test_get_employee_identity_by_employee_code_strips_legacy_aadhaar_number() -> None:
    db = _FakeDb()
    db.employee_identities.docs.append(
        {
            "employee_id": "EMP-2",
            "employee_code": "MADC-2024-R0002",
            "full_name": "Legacy Ref User",
            "aadhaar_number": "123456789012",
        }
    )

    identity = await get_employee_identity(db, employee_id="MADC-2024-R0002")

    assert identity is not None
    assert "aadhaar_number" not in identity
