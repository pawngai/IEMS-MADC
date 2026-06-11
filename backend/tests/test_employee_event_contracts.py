from __future__ import annotations

from contexts.employee_master.identity.contracts.events import (
    EmployeeCreatedEvent,
    EmployeeStatusChangedEvent,
    EmployeeUpdatedEvent,
)


def test_employee_created_contract_payload_is_json_serializable() -> None:
    event = EmployeeCreatedEvent(
        employee_id="EMP-1",
        dept_id="FIN",
        name="Jane Doe",
        dob="1990-01-01",
        doj="2020-01-01",
        designation_id="DES-1",
        created_at="2026-03-03T00:00:00Z",
        version=2,
    )

    payload = event.model_dump(mode="json")
    assert payload["employee_id"] == "EMP-1"
    assert payload["dept_id"] == "FIN"
    assert payload["event_version"] == 1
    assert payload["version"] == 2


def test_employee_updated_contract_keeps_patch() -> None:
    event = EmployeeUpdatedEvent(
        employee_id="EMP-2",
        patch={"full_name": "X", "current_department_id": "EST"},
        updated_at="2026-03-03T00:00:00Z",
        version=3,
    )
    payload = event.model_dump(mode="json")
    assert payload["patch"]["full_name"] == "X"


def test_employee_status_changed_contract_shape() -> None:
    event = EmployeeStatusChangedEvent(
        employee_id="EMP-3",
        old_status="SUBMITTED",
        new_status="VERIFIED",
        effective_date="2026-03-03",
        updated_at="2026-03-03T00:00:00Z",
        version=4,
    )
    assert event.model_dump(mode="json")["new_status"] == "VERIFIED"
