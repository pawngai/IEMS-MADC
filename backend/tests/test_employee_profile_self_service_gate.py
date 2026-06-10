from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from contexts.employee_master.profile.application.update_profile_extension import (
    update_profile_extension_response,
)
from contexts.employee_master.profile.contracts.profile_write import (
    ESS_EDITABLE_FIELDS,
    IMMUTABLE_AFTER_VERIFICATION,
    PROFILE_EXTENSION_EDITABLE_FIELDS,
    EmployeeProfileExtensionUpsert,
)


class _FakeWorkflowService:
    def __init__(self, profile: dict) -> None:
        self.profile = profile
        self.last_update: dict | None = None

    async def get_employee_record(self, *, employee_id: str) -> dict:
        assert employee_id == self.profile["employee_id"]
        return dict(self.profile)

    async def add_domain_violation_log(self, *, log: dict) -> None:
        return None

    async def update_profile_record(self, *, employee_id: str, mongo_update: dict) -> int:
        assert employee_id == self.profile["employee_id"]
        self.last_update = mongo_update
        return 1


async def _allow_scope(*_args, **_kwargs):
    return None


async def _create_audit_log(*_args, **_kwargs):
    return None


def _get_changed_fields(_profile: dict, updates: dict) -> list[str]:
    return list(updates.keys())


def _request() -> SimpleNamespace:
    return SimpleNamespace(
        client=SimpleNamespace(host="127.0.0.1"),
        headers={"user-agent": "pytest"},
    )


def _employee_user() -> dict:
    return {
        "sub": "user-1",
        "id": "user-1",
        "employee_id": "EMP-1",
        "authorities": ["EMPLOYEE"],
        "permissions": ["PROFILE_UPDATE_OWN_LIMITED"],
        "name": "Employee User",
    }


def _data_entry_user() -> dict:
    return {
        "sub": "user-2",
        "id": "user-2",
        "authorities": ["GLOBAL_DATA_ENTRY"],
        "permissions": ["PROFILE_UPDATE_ALL"],
        "name": "Global Data Entry",
    }


@pytest.mark.asyncio
async def test_employee_self_service_updates_work_during_draft() -> None:
    workflow_service = _FakeWorkflowService(
        {
            "employee_id": "EMP-1",
            "workflow_status": "DRAFT",
            "contact": {"mobile_primary": "9999999999"},
            "version": 1,
        }
    )

    result = await update_profile_extension_response(
        employee_id="EMP-1",
        updates_model=EmployeeProfileExtensionUpsert(mobile_primary="8888888888"),
        request=_request(),
        db=object(),
        current_user=_employee_user(),
        user_role="EMPLOYEE",
        user_id="user-1",
        workflow_service=workflow_service,
        enforce_profile_write_scope_or_raise_fn=_allow_scope,
        create_audit_log_fn=_create_audit_log,
        get_changed_fields_fn=_get_changed_fields,
        data_entry_roles={"DEPT_DATA_ENTRY", "GLOBAL_DATA_ENTRY"},
        data_entry_editable_fields=PROFILE_EXTENSION_EDITABLE_FIELDS,
        ess_editable_fields=ESS_EDITABLE_FIELDS,
        immutable_after_verification=IMMUTABLE_AFTER_VERIFICATION,
    )

    assert result["success"] is True
    assert result["workflow_status"] == "DRAFT"
    assert workflow_service.last_update is not None
    assert workflow_service.last_update["$set"]["contact.mobile_primary"] == "8888888888"


@pytest.mark.asyncio
async def test_employee_self_service_updates_blocked_during_submitted_review() -> None:
    workflow_service = _FakeWorkflowService(
        {
            "employee_id": "EMP-1",
            "workflow_status": "SUBMITTED",
            "contact": {"mobile_primary": "9999999999"},
            "version": 1,
        }
    )

    with pytest.raises(HTTPException) as exc_info:
        await update_profile_extension_response(
            employee_id="EMP-1",
            updates_model=EmployeeProfileExtensionUpsert(mobile_primary="8888888888"),
            request=_request(),
            db=object(),
            current_user=_employee_user(),
            user_role="EMPLOYEE",
            user_id="user-1",
            workflow_service=workflow_service,
            enforce_profile_write_scope_or_raise_fn=_allow_scope,
            create_audit_log_fn=_create_audit_log,
            get_changed_fields_fn=_get_changed_fields,
            data_entry_roles={"DEPT_DATA_ENTRY", "GLOBAL_DATA_ENTRY"},
            data_entry_editable_fields=PROFILE_EXTENSION_EDITABLE_FIELDS,
            ess_editable_fields=ESS_EDITABLE_FIELDS,
            immutable_after_verification=IMMUTABLE_AFTER_VERIFICATION,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["error_code"] == "SELF_SERVICE_NOT_READY"


@pytest.mark.asyncio
async def test_employee_self_service_updates_work_after_approval() -> None:
    workflow_service = _FakeWorkflowService(
        {
            "employee_id": "EMP-1",
            "workflow_status": "APPROVED",
            "contact": {"mobile_primary": "9999999999"},
            "version": 1,
        }
    )

    result = await update_profile_extension_response(
        employee_id="EMP-1",
        updates_model=EmployeeProfileExtensionUpsert(mobile_primary="8888888888"),
        request=_request(),
        db=object(),
        current_user=_employee_user(),
        user_role="EMPLOYEE",
        user_id="user-1",
        workflow_service=workflow_service,
        enforce_profile_write_scope_or_raise_fn=_allow_scope,
        create_audit_log_fn=_create_audit_log,
        get_changed_fields_fn=_get_changed_fields,
        data_entry_roles={"DEPT_DATA_ENTRY", "GLOBAL_DATA_ENTRY"},
        data_entry_editable_fields=PROFILE_EXTENSION_EDITABLE_FIELDS,
        ess_editable_fields=ESS_EDITABLE_FIELDS,
        immutable_after_verification=IMMUTABLE_AFTER_VERIFICATION,
    )

    assert result["success"] is True
    assert result["workflow_status"] == "APPROVED"
    assert result["updated_fields"] == ["mobile_primary"]
    assert workflow_service.last_update is not None
    assert workflow_service.last_update["$set"]["contact.mobile_primary"] == "8888888888"


@pytest.mark.asyncio
async def test_employee_profile_update_ignores_client_completion_flags_and_derives_them() -> None:
    workflow_service = _FakeWorkflowService(
        {
            "employee_id": "EMP-1",
            "workflow_status": "DRAFT",
            "employment_type": "REGULAR",
            "contact": {
                "mobile_primary": "9999999999",
                "email_personal": "employee@example.com",
                "address_line1": "123 Main Street",
                "city": "Mumbai",
                "state": "MH",
                "pincode": "400001",
                "present_address_line1": "123 Main Street",
                "present_city": "Mumbai",
                "present_state": "MH",
                "present_pincode": "400001",
                "emergency_name": "Contact Person",
                "emergency_phone": "8888888888",
                "emergency_relation": "Sibling",
            },
            "version": 1,
        }
    )

    result = await update_profile_extension_response(
        employee_id="EMP-1",
        updates_model=EmployeeProfileExtensionUpsert(
            mobile_primary="8888888888",
            employee_section_completed=False,
            data_entry_section_completed=False,
        ),
        request=_request(),
        db=object(),
        current_user=_employee_user(),
        user_role="EMPLOYEE",
        user_id="user-1",
        workflow_service=workflow_service,
        enforce_profile_write_scope_or_raise_fn=_allow_scope,
        create_audit_log_fn=_create_audit_log,
        get_changed_fields_fn=_get_changed_fields,
        data_entry_roles={"DEPT_DATA_ENTRY", "GLOBAL_DATA_ENTRY"},
        data_entry_editable_fields=PROFILE_EXTENSION_EDITABLE_FIELDS,
        ess_editable_fields=ESS_EDITABLE_FIELDS,
        immutable_after_verification=IMMUTABLE_AFTER_VERIFICATION,
    )

    assert result["success"] is True
    assert workflow_service.last_update is not None
    assert workflow_service.last_update["$set"]["employee_section_completed"] is True
    assert workflow_service.last_update["$set"]["data_entry_section_completed"] is True


@pytest.mark.asyncio
async def test_data_entry_can_update_profile_extension_fields() -> None:
    workflow_service = _FakeWorkflowService(
        {
            "employee_id": "EMP-1",
            "workflow_status": "DRAFT",
            "employment_type": "REGULAR",
            "contact": {
                "mobile_primary": "9999999999",
                "email_personal": "employee@example.com",
                "address_line1": "123 Main Street",
                "city": "Mumbai",
                "state": "MH",
                "pincode": "400001",
                "present_address_line1": "123 Main Street",
                "present_city": "Mumbai",
                "present_state": "MH",
                "present_pincode": "400001",
                "emergency_name": "Contact Person",
                "emergency_phone": "8888888888",
                "emergency_relation": "Sibling",
            },
            "version": 1,
        }
    )

    result = await update_profile_extension_response(
        employee_id="EMP-1",
        updates_model=EmployeeProfileExtensionUpsert(
            father_name="Parent Name",
            email_official="official@gov.in",
        ),
        request=_request(),
        db=object(),
        current_user=_data_entry_user(),
        user_role="GLOBAL_DATA_ENTRY",
        user_id="user-2",
        workflow_service=workflow_service,
        enforce_profile_write_scope_or_raise_fn=_allow_scope,
        create_audit_log_fn=_create_audit_log,
        get_changed_fields_fn=_get_changed_fields,
        data_entry_roles={"DEPT_DATA_ENTRY", "GLOBAL_DATA_ENTRY"},
        data_entry_editable_fields=PROFILE_EXTENSION_EDITABLE_FIELDS,
        ess_editable_fields=ESS_EDITABLE_FIELDS,
        immutable_after_verification=IMMUTABLE_AFTER_VERIFICATION,
    )

    assert result["success"] is True
    assert workflow_service.last_update is not None
    assert workflow_service.last_update["$set"]["father_name"] == "Parent Name"
    assert workflow_service.last_update["$set"]["contact.email_official"] == "official@gov.in"
    assert workflow_service.last_update["$set"]["data_entry_section_completed"] is True


@pytest.mark.asyncio
async def test_employee_profile_update_completion_does_not_require_emergency_contact() -> None:
    workflow_service = _FakeWorkflowService(
        {
            "employee_id": "EMP-1",
            "workflow_status": "DRAFT",
            "employment_type": "REGULAR",
            "contact": {
                "mobile_primary": "9999999999",
                "email_personal": "employee@example.com",
                "address_line1": "123 Main Street",
                "city": "Mumbai",
                "state": "MH",
                "pincode": "400001",
                "present_address_line1": "123 Main Street",
                "present_city": "Mumbai",
                "present_state": "MH",
                "present_pincode": "400001",
            },
            "version": 1,
        }
    )

    result = await update_profile_extension_response(
        employee_id="EMP-1",
        updates_model=EmployeeProfileExtensionUpsert(mobile_primary="8888888888"),
        request=_request(),
        db=object(),
        current_user=_employee_user(),
        user_role="EMPLOYEE",
        user_id="user-1",
        workflow_service=workflow_service,
        enforce_profile_write_scope_or_raise_fn=_allow_scope,
        create_audit_log_fn=_create_audit_log,
        get_changed_fields_fn=_get_changed_fields,
        data_entry_roles={"DEPT_DATA_ENTRY", "GLOBAL_DATA_ENTRY"},
        data_entry_editable_fields=PROFILE_EXTENSION_EDITABLE_FIELDS,
        ess_editable_fields=ESS_EDITABLE_FIELDS,
        immutable_after_verification=IMMUTABLE_AFTER_VERIFICATION,
    )

    assert result["success"] is True
    assert workflow_service.last_update is not None
    assert workflow_service.last_update["$set"]["employee_section_completed"] is True
    assert workflow_service.last_update["$set"]["data_entry_section_completed"] is True

