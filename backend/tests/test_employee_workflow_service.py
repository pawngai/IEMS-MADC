from __future__ import annotations

import os
import sys

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app_platform.event_bus.types import EventName
from contexts.employee_master.profile.application.access_scope import enforce_profile_write_scope_or_raise
from contexts.employee_master.profile.application.services.workflow_engine import EmployeeWorkflowApplicationService
from contexts.employee_master.profile.contracts.dto import (
    EmployeeWorkflowAuditDTO,
    EmployeeWorkflowEventDTO,
)
from contexts.employee_master.profile.infrastructure.gateway import EmployeeWorkflowEventOutboxGateway


class _FakeOutboxRepo:
    def __init__(self) -> None:
        self.events: list[dict] = []

    async def add_event(self, event):
        self.events.append(event.to_document())


class _FakeProfileGateway:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def persist_transition(
        self, *, employee_id, new_status, remarks, actor_user_id, transition
    ):
        self.calls.append(
            {
                "employee_id": employee_id,
                "new_status": new_status,
                "remarks": remarks,
                "actor_user_id": actor_user_id,
                "transition": transition,
            }
        )


class _FakeAuditGateway:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def write_workflow_audit(self, *, payload):
        self.calls.append(payload.model_dump())
        return "audit-123"


class _FakeProfileRepoGateway:
    def __init__(self) -> None:
        self.profile = {"employee_id": "EMP-R1", "workflow_status": "DRAFT"}
        self.inserted: list[dict] = []
        self.updated: list[dict] = []
        self.archived: list[dict] = []
        self.count_query: dict | None = None
        self.list_args: dict | None = None
        self.completion_query: dict | None = None
        self.audit_employee_id: str | None = None
        self.domain_logs: list[dict] = []

    async def get_profile(self, *, employee_id: str):
        if self.profile.get("employee_id") == employee_id:
            return dict(self.profile)
        return None

    async def insert_profile(self, *, profile: dict):
        self.inserted.append(profile)

    async def update_profile(self, *, employee_id: str, mongo_update: dict):
        self.updated.append({"employee_id": employee_id, "mongo_update": mongo_update})
        return 1

    async def archive_and_delete_profile(self, *, profile: dict, actor_user_id: str):
        self.archived.append({"profile": profile, "actor_user_id": actor_user_id})

    async def count_profiles(self, *, query: dict):
        self.count_query = query
        return 3

    async def list_profiles(self, *, query: dict, skip: int = 0, limit: int = 20, sort: list | None = None):
        self.list_args = {"query": query, "skip": skip, "limit": limit, "sort": sort}
        return [dict(self.profile)]

    async def list_profiles_for_completion(self, *, query: dict, limit: int = 5000):
        self.completion_query = {"query": query, "limit": limit}
        return [dict(self.profile)]

    async def list_audit_trail(self, *, employee_id: str, limit: int = 100):
        self.audit_employee_id = employee_id
        return [{"employee_id": employee_id, "action": "UPDATE"}]

    async def add_domain_violation_log(self, *, log: dict):
        self.domain_logs.append(log)


@pytest.mark.asyncio
async def test_publish_submitted_emits_expected_event() -> None:
    repo = _FakeOutboxRepo()
    gateway = EmployeeWorkflowEventOutboxGateway(outbox_repo=repo)
    service = EmployeeWorkflowApplicationService(gateway=gateway)

    await service.publish_submitted(
        EmployeeWorkflowEventDTO(
            employee_id="EMP-1001",
            status="SUBMITTED",
            remarks="submitted",
            actor_id="user-1",
            department_id="FIN",
        )
    )

    assert len(repo.events) == 1
    event = repo.events[0]
    assert event["name"] == EventName.EMPLOYEE_PROFILE_SUBMITTED.value
    assert event["payload"]["employee_id"] == "EMP-1001"
    assert event["payload"]["status"] == "SUBMITTED"


@pytest.mark.asyncio
async def test_publish_approved_emits_expected_event() -> None:
    repo = _FakeOutboxRepo()
    gateway = EmployeeWorkflowEventOutboxGateway(outbox_repo=repo)
    service = EmployeeWorkflowApplicationService(gateway=gateway)

    await service.publish_approved(
        EmployeeWorkflowEventDTO(
            employee_id="EMP-2002",
            status="APPROVED",
            remarks="ok",
            actor_id="approver-1",
            department_id="HR",
        )
    )

    assert len(repo.events) == 1
    event = repo.events[0]
    assert event["name"] == EventName.EMPLOYEE_PROFILE_APPROVED.value
    assert event["payload"]["employee_id"] == "EMP-2002"
    assert event["department_id"] == "HR"


def test_validate_submit_transition_requires_data_entry_completion() -> None:
    service = EmployeeWorkflowApplicationService(gateway=None)

    with pytest.raises(HTTPException) as exc:
        service.validate_submit_transition(
            current_status="DRAFT",
            user_role="DEPARTMENT_DATA_ENTRY",
            employee_section_completed=True,
            data_entry_section_completed=False,
        )

    assert exc.value.status_code == 400
    assert "Data Entry must mark their section complete" in str(exc.value.detail)


def test_validate_submit_transition_allows_employee_when_both_sections_complete() -> None:
    service = EmployeeWorkflowApplicationService(gateway=None)

    status = service.validate_submit_transition(
        current_status="DRAFT",
        user_role="EMPLOYEE",
        employee_section_completed=True,
        data_entry_section_completed=True,
    )

    assert status == "SUBMITTED"


@pytest.mark.asyncio
async def test_employee_write_scope_allows_own_profile() -> None:
    result = await enforce_profile_write_scope_or_raise(
        {"employee_id": "EMP-1"},
        "EMPLOYEE",
        EmployeeWorkflowApplicationService(gateway=None),
        set(),
        profile={"employee_id": "EMP-1"},
    )

    assert result is None


@pytest.mark.asyncio
async def test_employee_write_scope_blocks_other_profile() -> None:
    with pytest.raises(HTTPException) as exc:
        await enforce_profile_write_scope_or_raise(
            {"employee_id": "EMP-1"},
            "EMPLOYEE",
            EmployeeWorkflowApplicationService(gateway=None),
            set(),
            profile={"employee_id": "EMP-2"},
        )

    assert exc.value.status_code == 403
    assert "own profile" in str(exc.value.detail)


def test_validate_verify_transition_blocks_creator() -> None:
    service = EmployeeWorkflowApplicationService(gateway=None)

    with pytest.raises(HTTPException) as exc:
        service.validate_verify_transition(
            current_status="SUBMITTED",
            user_role="VERIFIER",
            profile_created_by="user-1",
            actor_user_id="user-1",
        )

    assert exc.value.status_code == 403
    assert exc.value.detail["error_code"] == "SEPARATION_OF_DUTIES"


def test_validate_approve_transition_returns_new_status() -> None:
    service = EmployeeWorkflowApplicationService(gateway=None)

    status = service.validate_approve_transition(
        current_status="VERIFIED",
        user_role="APPROVING_AUTHORITY",
        profile_created_by="creator",
        profile_verified_by="verifier",
        actor_user_id="approver",
    )

    assert status == "APPROVED"


def test_validate_reject_transition_requires_remarks() -> None:
    service = EmployeeWorkflowApplicationService(gateway=None)

    with pytest.raises(HTTPException) as exc:
        service.validate_reject_transition(
            current_status="SUBMITTED",
            user_role="VERIFIER",
            remarks=None,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Rejection remarks are required"


@pytest.mark.asyncio
async def test_persist_verified_delegates_to_profile_gateway() -> None:
    profile_gateway = _FakeProfileGateway()
    service = EmployeeWorkflowApplicationService(
        gateway=None, profile_gateway=profile_gateway
    )

    await service.persist_verified(
        employee_id="EMP-77", remarks="ok", actor_user_id="verifier-7"
    )

    assert len(profile_gateway.calls) == 1
    call = profile_gateway.calls[0]
    assert call["employee_id"] == "EMP-77"
    assert call["new_status"] == "VERIFIED"
    assert call["transition"] == "VERIFY"


@pytest.mark.asyncio
async def test_persist_locked_delegates_to_profile_gateway() -> None:
    profile_gateway = _FakeProfileGateway()
    service = EmployeeWorkflowApplicationService(
        gateway=None, profile_gateway=profile_gateway
    )

    await service.persist_locked(
        employee_id="EMP-88", remarks="locked", actor_user_id="approver-8"
    )

    assert len(profile_gateway.calls) == 1
    call = profile_gateway.calls[0]
    assert call["new_status"] == "LOCKED"
    assert call["transition"] == "LOCK"


@pytest.mark.asyncio
async def test_write_workflow_audit_delegates_to_audit_gateway() -> None:
    audit_gateway = _FakeAuditGateway()
    service = EmployeeWorkflowApplicationService(
        gateway=None, audit_gateway=audit_gateway
    )

    audit_id = await service.write_workflow_audit(
        EmployeeWorkflowAuditDTO(
            employee_id="EMP-501",
            action="APPROVE",
            user_id="approver-1",
            user_name="Approver",
            user_role="APPROVING_AUTHORITY",
            status_before="VERIFIED",
            status_after="APPROVED",
            remarks="ok",
            ip_address="127.0.0.1",
            user_agent="pytest",
        )
    )

    assert audit_id == "audit-123"
    assert len(audit_gateway.calls) == 1
    assert audit_gateway.calls[0]["employee_id"] == "EMP-501"
    assert audit_gateway.calls[0]["action"] == "APPROVE"


@pytest.mark.asyncio
async def test_write_profile_audit_with_change_payload_delegates() -> None:
    audit_gateway = _FakeAuditGateway()
    service = EmployeeWorkflowApplicationService(
        gateway=None, audit_gateway=audit_gateway
    )

    audit_id = await service.write_profile_audit(
        EmployeeWorkflowAuditDTO(
            employee_id="EMP-502",
            action="UPDATE",
            user_id="editor-1",
            user_name="Editor",
            user_role="DEPARTMENT_DATA_ENTRY",
            previous_data={"mobile_primary": "111"},
            new_data={"mobile_primary": "999"},
            changed_fields=["mobile_primary"],
            status_before="DRAFT",
            status_after="DRAFT",
        )
    )

    assert audit_id == "audit-123"
    assert audit_gateway.calls[0]["changed_fields"] == ["mobile_primary"]
    assert audit_gateway.calls[0]["previous_data"]["mobile_primary"] == "111"


def test_build_workflow_response_submit_message_and_action() -> None:
    service = EmployeeWorkflowApplicationService(gateway=None)

    response = service.build_workflow_response(
        action="SUBMIT",
        employee_id="EMP-600",
        previous_status="DRAFT",
        new_status="SUBMITTED",
        performed_by="user-6",
        audit_log_id="audit-600",
        remarks="done",
    )

    assert response["message"] == "Profile submitted for verification"
    assert response["action_performed"] == "submit"
    assert response["previous_status"] == "DRAFT"
    assert response["new_status"] == "SUBMITTED"


def test_build_workflow_response_reject_includes_remarks() -> None:
    service = EmployeeWorkflowApplicationService(gateway=None)

    response = service.build_workflow_response(
        action="REJECT",
        employee_id="EMP-700",
        previous_status="VERIFIED",
        new_status="REJECTED",
        performed_by="approver-7",
        audit_log_id="audit-700",
        remarks="missing document",
    )

    assert response["message"] == "Profile rejected with remarks: missing document"
    assert response["action_performed"] == "reject"


@pytest.mark.asyncio
async def test_profile_repo_methods_delegate_to_gateway() -> None:
    repo_gateway = _FakeProfileRepoGateway()
    service = EmployeeWorkflowApplicationService(
        gateway=None, profile_repo_gateway=repo_gateway
    )

    await service.insert_profile_record(profile={"employee_id": "EMP-R2"})
    profile = await service.get_employee_record(employee_id="EMP-R1")
    modified = await service.update_profile_record(
        employee_id="EMP-R1", mongo_update={"$set": {"x": 1}}
    )
    await service.archive_and_delete_profile_record(
        profile={"employee_id": "EMP-R1"}, actor_user_id="user-r"
    )
    total = await service.count_profile_records(query={"workflow_status": "DRAFT"})
    listed = await service.list_profile_records(
        query={"workflow_status": "DRAFT"}, skip=0, limit=10
    )
    completion = await service.list_profile_records_for_completion(
        query={"current_department_id": "FIN"}, limit=200
    )
    trail = await service.list_profile_audit_trail(employee_id="EMP-R1", limit=50)
    await service.add_domain_violation_log(
        log={"violation_type": "PROFILE_DOMAIN_ONLY"}
    )

    assert repo_gateway.inserted[0]["employee_id"] == "EMP-R2"
    assert profile is not None and profile["employee_id"] == "EMP-R1"
    assert modified == 1
    assert repo_gateway.archived[0]["actor_user_id"] == "user-r"
    assert total == 3
    assert listed[0]["employee_id"] == "EMP-R1"
    assert completion[0]["employee_id"] == "EMP-R1"
    assert trail[0]["employee_id"] == "EMP-R1"
    assert repo_gateway.domain_logs[0]["violation_type"] == "PROFILE_DOMAIN_ONLY"

