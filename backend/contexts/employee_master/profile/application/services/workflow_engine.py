from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from contexts.employee_master.identity.contracts.events import (
    EmployeeCreatedEvent,
    EmployeeStatusChangedEvent,
    EmployeeUpdatedEvent,
)
from app_platform.event_bus.types import EventName
from contexts.employee_master.profile.application.services import workflow_rules
from contexts.employee_master.profile.contracts.dto import EmployeeWorkflowAuditDTO, EmployeeWorkflowEventDTO
from contexts.employee_master.profile.contracts.ports import (
    EmployeeProfileAuditGateway,
    EmployeeProfileReadGateway,
    EmployeeProfileRepositoryGateway,
    EmployeeProfileWorkflowGateway,
    EmployeeWorkflowEventGateway,
)


class EmployeeWorkflowApplicationService:
    ROLE_VERIFIER = workflow_rules.ROLE_VERIFIER
    ROLE_APPROVER = workflow_rules.ROLE_APPROVER
    ROLE_HOD = workflow_rules.ROLE_HOD
    DATA_ENTRY_ROLES = workflow_rules.DATA_ENTRY_ROLES

    def __init__(
        self,
        *,
        gateway: EmployeeWorkflowEventGateway | None,
        profile_gateway: EmployeeProfileWorkflowGateway | None = None,
        profile_repo_gateway: EmployeeProfileRepositoryGateway | None = None,
        profile_read_gateway: EmployeeProfileReadGateway | None = None,
        audit_gateway: EmployeeProfileAuditGateway | None = None,
    ) -> None:
        self._gateway = gateway
        self._profile_gateway = profile_gateway
        self._profile_repo_gateway = profile_repo_gateway
        self._profile_read_gateway = profile_read_gateway
        self._audit_gateway = audit_gateway

    def validate_submit_transition(
        self,
        *,
        current_status: str,
        user_role: str,
        employee_section_completed: bool,
        data_entry_section_completed: bool,
    ) -> str:
        return workflow_rules.validate_submit_transition(
            current_status=current_status,
            user_role=user_role,
            employee_section_completed=employee_section_completed,
            data_entry_section_completed=data_entry_section_completed,
        )

    def validate_verify_transition(
        self,
        *,
        current_status: str,
        user_role: str,
        profile_created_by: str | None,
        actor_user_id: str,
    ) -> str:
        return workflow_rules.validate_verify_transition(
            current_status=current_status,
            user_role=user_role,
            profile_created_by=profile_created_by,
            actor_user_id=actor_user_id,
        )

    def validate_approve_transition(
        self,
        *,
        current_status: str,
        user_role: str,
        profile_created_by: str | None,
        profile_verified_by: str | None,
        actor_user_id: str,
    ) -> str:
        return workflow_rules.validate_approve_transition(
            current_status=current_status,
            user_role=user_role,
            profile_created_by=profile_created_by,
            profile_verified_by=profile_verified_by,
            actor_user_id=actor_user_id,
        )

    def validate_lock_transition(self, *, current_status: str, user_role: str) -> str:
        return workflow_rules.validate_lock_transition(
            current_status=current_status,
            user_role=user_role,
        )

    def validate_reject_transition(
        self,
        *,
        current_status: str,
        user_role: str,
        remarks: str | None,
    ) -> str:
        return workflow_rules.validate_reject_transition(
            current_status=current_status,
            user_role=user_role,
            remarks=remarks,
        )

    async def publish_submitted(self, payload: EmployeeWorkflowEventDTO) -> None:
        await self._publish(EventName.EMPLOYEE_PROFILE_SUBMITTED.value, payload)

    async def publish_verified(self, payload: EmployeeWorkflowEventDTO) -> None:
        await self._publish(EventName.EMPLOYEE_PROFILE_VERIFIED.value, payload)

    async def publish_approved(self, payload: EmployeeWorkflowEventDTO) -> None:
        await self._publish(EventName.EMPLOYEE_PROFILE_APPROVED.value, payload)

    async def publish_rejected(self, payload: EmployeeWorkflowEventDTO) -> None:
        await self._publish(EventName.EMPLOYEE_PROFILE_REJECTED.value, payload)

    async def publish_locked(self, payload: EmployeeWorkflowEventDTO) -> None:
        await self._publish(EventName.EMPLOYEE_PROFILE_LOCKED.value, payload)

    async def publish_employee_created(self, payload: EmployeeCreatedEvent) -> None:
        await self._publish_raw(EventName.EMPLOYEE_CREATED.value, payload.model_dump(mode="json"))

    async def publish_employee_updated(self, payload: EmployeeUpdatedEvent) -> None:
        await self._publish_raw(EventName.EMPLOYEE_UPDATED.value, payload.model_dump(mode="json"))

    async def publish_employee_status_changed(self, payload: EmployeeStatusChangedEvent) -> None:
        await self._publish_raw(EventName.EMPLOYEE_STATUS_CHANGED.value, payload.model_dump(mode="json"))

    async def persist_submitted(self, *, employee_id: str, remarks: str | None, actor_user_id: str) -> None:
        await self._persist_transition(
            employee_id=employee_id,
            new_status="SUBMITTED",
            remarks=remarks,
            actor_user_id=actor_user_id,
            transition="SUBMIT",
        )

    async def persist_verified(self, *, employee_id: str, remarks: str | None, actor_user_id: str) -> None:
        await self._persist_transition(
            employee_id=employee_id,
            new_status="VERIFIED",
            remarks=remarks,
            actor_user_id=actor_user_id,
            transition="VERIFY",
        )

    async def persist_approved(self, *, employee_id: str, remarks: str | None, actor_user_id: str) -> None:
        await self._persist_transition(
            employee_id=employee_id,
            new_status="APPROVED",
            remarks=remarks,
            actor_user_id=actor_user_id,
            transition="APPROVE",
        )

    async def persist_locked(self, *, employee_id: str, remarks: str | None, actor_user_id: str) -> None:
        await self._persist_transition(
            employee_id=employee_id,
            new_status="LOCKED",
            remarks=remarks,
            actor_user_id=actor_user_id,
            transition="LOCK",
        )

    async def persist_rejected(self, *, employee_id: str, remarks: str | None, actor_user_id: str) -> None:
        await self._persist_transition(
            employee_id=employee_id,
            new_status="REJECTED",
            remarks=remarks,
            actor_user_id=actor_user_id,
            transition="REJECT",
        )

    async def write_profile_audit(self, payload: EmployeeWorkflowAuditDTO) -> str:
        return await self._call_audit_gateway(
            lambda gateway: gateway.write_workflow_audit(payload=payload),
            default="",
        )

    async def write_workflow_audit(self, payload: EmployeeWorkflowAuditDTO) -> str:
        return await self.write_profile_audit(payload)

    async def get_employee_record(self, *, employee_id: str) -> dict | None:
        return await self._call_repo_gateway(
            lambda gateway: gateway.get_profile(employee_id=employee_id),
            default=None,
        )

    async def insert_profile_record(self, *, profile: dict) -> None:
        await self._call_repo_gateway(
            lambda gateway: gateway.insert_profile(profile=profile),
            default=None,
        )

    async def update_profile_record(self, *, employee_id: str, mongo_update: dict) -> int:
        return await self._call_repo_gateway(
            lambda gateway: gateway.update_profile(employee_id=employee_id, mongo_update=mongo_update),
            default=0,
        )

    async def archive_and_delete_profile_record(self, *, profile: dict, actor_user_id: str) -> None:
        await self._call_repo_gateway(
            lambda gateway: gateway.archive_and_delete_profile(
                profile=profile,
                actor_user_id=actor_user_id,
            ),
            default=None,
        )

    async def count_profile_records(self, *, query: dict) -> int:
        return await self._call_repo_gateway(
            lambda gateway: gateway.count_profiles(query=query),
            default=0,
        )

    async def list_profile_records(self, *, query: dict, skip: int = 0, limit: int = 20, sort: list | None = None) -> list[dict]:
        return await self._call_repo_gateway(
            lambda gateway: gateway.list_profiles(query=query, skip=skip, limit=limit, sort=sort),
            default=[],
        )

    async def get_profile_view(self, *, employee_id: str) -> dict | None:
        return await self._call_read_gateway(
            lambda gateway: gateway.get_profile(employee_id=employee_id),
            default=None,
        )

    async def count_profile_views(self, *, query: dict) -> int:
        return await self._call_read_gateway(
            lambda gateway: gateway.count_profiles(query=query),
            default=0,
        )

    async def list_profile_views(
        self, *, query: dict, skip: int = 0, limit: int = 20, sort: list | None = None
    ) -> list[dict]:
        return await self._call_read_gateway(
            lambda gateway: gateway.list_profiles(query=query, skip=skip, limit=limit, sort=sort),
            default=[],
        )

    async def list_profile_records_for_completion(self, *, query: dict, limit: int = 5000) -> list[dict]:
        return await self._call_repo_gateway(
            lambda gateway: gateway.list_profiles_for_completion(query=query, limit=limit),
            default=[],
        )

    async def list_profile_audit_trail(self, *, employee_id: str, limit: int = 100) -> list[dict]:
        return await self._call_repo_gateway(
            lambda gateway: gateway.list_audit_trail(employee_id=employee_id, limit=limit),
            default=[],
        )

    async def add_domain_violation_log(self, *, log: dict) -> None:
        await self._call_repo_gateway(
            lambda gateway: gateway.add_domain_violation_log(log=log),
            default=None,
        )

    async def get_user_department_code(self, *, user_id: str) -> str | None:
        return await self._call_repo_gateway(
            lambda gateway: gateway.get_user_department_code(user_id=user_id),
            default=None,
        )

    async def get_profile_department_code(self, *, employee_id: str) -> str | None:
        return await self._call_repo_gateway(
            lambda gateway: gateway.get_profile_department_code(employee_id=employee_id),
            default=None,
        )

    async def get_officer_profile_for_attestation(self, *, employee_id: str) -> dict | None:
        return await self._call_repo_gateway(
            lambda gateway: gateway.get_officer_profile_for_attestation(employee_id=employee_id),
            default=None,
        )

    async def get_designation_name(self, *, code: str) -> str | None:
        return await self._call_repo_gateway(
            lambda gateway: gateway.get_designation_name(code=code),
            default=None,
        )

    def build_workflow_response(
        self,
        *,
        action: str,
        employee_id: str,
        previous_status: str,
        new_status: str,
        performed_by: str,
        audit_log_id: str,
        remarks: str | None = None,
    ) -> dict:
        return workflow_rules.build_workflow_response(
            action=action,
            employee_id=employee_id,
            previous_status=previous_status,
            new_status=new_status,
            performed_by=performed_by,
            audit_log_id=audit_log_id,
            remarks=remarks,
        )

    async def _publish(self, event_name: str, payload: EmployeeWorkflowEventDTO) -> None:
        if self._gateway is None:
            return
        await self._gateway.publish(event_name=event_name, payload=payload)

    async def _publish_raw(self, event_name: str, payload: dict) -> None:
        if self._gateway is None:
            return
        await self._gateway.publish_raw(event_name=event_name, payload=payload)

    async def _persist_transition(
        self,
        *,
        employee_id: str,
        new_status: str,
        remarks: str | None,
        actor_user_id: str,
        transition: str,
    ) -> None:
        if self._profile_gateway is None:
            return
        await self._profile_gateway.persist_transition(
            employee_id=employee_id,
            new_status=new_status,
            remarks=remarks,
            actor_user_id=actor_user_id,
            transition=transition,
        )

    async def _call_repo_gateway(
        self,
        operation: Callable[[EmployeeProfileRepositoryGateway], Awaitable[Any]],
        *,
        default: Any,
    ) -> Any:
        if self._profile_repo_gateway is None:
            return default
        return await operation(self._profile_repo_gateway)

    async def _call_read_gateway(
        self,
        operation: Callable[[EmployeeProfileReadGateway], Awaitable[Any]],
        *,
        default: Any,
    ) -> Any:
        if self._profile_read_gateway is None:
            return default
        return await operation(self._profile_read_gateway)

    async def _call_audit_gateway(
        self,
        operation: Callable[[EmployeeProfileAuditGateway], Awaitable[Any]],
        *,
        default: Any,
    ) -> Any:
        if self._audit_gateway is None:
            return default
        return await operation(self._audit_gateway)

__all__ = ["EmployeeWorkflowApplicationService"]
