from __future__ import annotations

import pytest

from contexts.leave_attendance.application.command_service import LeaveCommandService
from contexts.pay_benefits.application.service import PayApplicationService
from contexts.change_requests.application.service import ChangeRequestApplicationService
from contexts.employee_master.identity.repository.identity_repository import EmployeeIdentityRepository


class _FakeSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def start_transaction(self):
        return self


class _FakeClient:
    def __init__(self, session: _FakeSession) -> None:
        self.session = session

    async def start_session(self):
        return self.session


class _FakeDb:
    def __init__(self, session: _FakeSession) -> None:
        self.client = _FakeClient(session)


class _IdentityCollection:
    def __init__(self) -> None:
        self.sessions: list[object | None] = []
        self.doc = {
            "employee_id": "EMP-1",
            "employee_code": "MADC/2026/REG/0001",
            "full_name": "Test Employee",
            "gender": "FEMALE",
            "date_of_birth": "1990-01-01",
            "date_of_initial_engagement": "2026-01-01",
            "employee_status": "ACTIVE",
            "version": 1,
        }

    async def find_one(self, query, projection=None):
        if query.get("employee_id") == "EMP-1":
            return dict(self.doc)
        return None

    async def update_one(self, query, update, *, session=None):
        self.sessions.append(session)
        self.doc.update(update.get("$set", {}))


class _IdentityDb(_FakeDb):
    def __init__(self, session: _FakeSession) -> None:
        super().__init__(session)
        self.employee_identities = _IdentityCollection()


class _IdentityOutbox:
    def __init__(self) -> None:
        self.sessions: list[object | None] = []

    async def add_event(self, event, *, session=None):
        self.sessions.append(session)


class _LeaveGateway:
    def __init__(self, db) -> None:
        self._db = db
        self.sessions: list[object | None] = []

    async def apply_leave(self, payload, *, current_user: dict, session=None):
        self.sessions.append(session)
        return {
            "id": "L-1",
            "employee_id": "EMP-1",
            "status": "SUBMITTED",
            "leave_type_code": "EL",
            "days_applied": 1,
        }


class _LeavePublisher:
    def __init__(self) -> None:
        self.sessions: list[object | None] = []

    async def publish(self, **kwargs):
        self.sessions.append(kwargs.get("session"))


class _PayGateway:
    def __init__(self, db) -> None:
        self._db = db
        self.sessions: list[object | None] = []

    async def revise_pay(self, payload, *, current_user: dict, session=None):
        self.sessions.append(session)
        return {
            "entry_id": "PAY-1",
            "employee_id": "EMP-1",
            "payload": {
                "effective_date": "2026-01-01",
                "basic_pay": 1000,
                "pay_level": "L1",
                "remarks": "ok",
            },
        }


class _PayOutbox:
    def __init__(self) -> None:
        self.sessions: list[object | None] = []

    async def add_event(self, event, *, session=None):
        self.sessions.append(session)


class _ChangeRequestGateway:
    def __init__(self, db) -> None:
        self._db = db
        self.sessions: list[object | None] = []

    async def create_change_request(self, payload, *, current_user: dict, session=None):
        self.sessions.append(session)
        return {
            "request_id": "CR-1",
            "employee_id": "EMP-1",
            "status": "PENDING",
            "request_type": "PROFILE",
            "category": "CONTACT",
        }


class _ChangeRequestOutbox:
    def __init__(self) -> None:
        self.sessions: list[object | None] = []

    async def add_event(self, event, *, session=None):
        self.sessions.append(session)


@pytest.mark.asyncio
async def test_leave_apply_uses_same_session_for_write_and_outbox() -> None:
    session = _FakeSession()
    gateway = _LeaveGateway(_FakeDb(session))
    publisher = _LeavePublisher()
    service = LeaveCommandService(gateway=gateway, event_publisher=publisher)

    await service.apply_leave(object(), current_user={"sub": "actor", "department_code": "D1"})

    assert gateway.sessions == [session]
    assert publisher.sessions == [session]


@pytest.mark.asyncio
async def test_pay_revision_uses_same_session_for_write_and_outbox() -> None:
    session = _FakeSession()
    gateway = _PayGateway(_FakeDb(session))
    outbox = _PayOutbox()
    service = PayApplicationService(gateway=gateway, outbox_repo=outbox)

    await service.revise_pay(object(), current_user={"sub": "actor", "department_code": "D1"})

    assert gateway.sessions == [session]
    assert outbox.sessions == [session]


@pytest.mark.asyncio
async def test_identity_update_uses_same_session_for_write_and_outbox() -> None:
    session = _FakeSession()
    db = _IdentityDb(session)
    outbox = _IdentityOutbox()
    repo = EmployeeIdentityRepository(db=db, outbox_repo=outbox)

    await repo.update_identity(
        employee_id="EMP-1",
        patch={"full_name": "Updated Employee"},
        actor_user_id="actor",
    )

    assert db.employee_identities.sessions == [session]
    assert outbox.sessions == [session]


@pytest.mark.asyncio
async def test_change_request_create_uses_same_session_for_write_and_outbox() -> None:
    session = _FakeSession()
    gateway = _ChangeRequestGateway(_FakeDb(session))
    outbox = _ChangeRequestOutbox()
    service = ChangeRequestApplicationService(gateway=gateway, outbox_repo=outbox)

    await service.create_change_request(
        object(),
        current_user={"sub": "actor", "department_code": "D1"},
    )

    assert gateway.sessions == [session]
    assert outbox.sessions == [session]