from __future__ import annotations

from typing import Any, Awaitable, Callable

from fastapi import HTTPException

from contexts.employee_profile.application.identity_activation_gate import (
    ensure_identity_active_for_profile_work,
)
from contexts.employee_profile.application.services.workflow_engine import (
    EmployeeWorkflowApplicationService,
)
from contexts.employee_profile.contracts.dto import (
    EmployeeWorkflowAuditDTO,
    EmployeeWorkflowEventDTO,
)


EnforceProfileWriteScopeFn = Callable[..., Awaitable[Any]]


async def submit_profile_action(
    *,
    employee_id: str,
    remarks: str | None,
    request: Any,
    current_user: dict,
    user_role: str,
    user_id: str,
    workflow_service: EmployeeWorkflowApplicationService,
    enforce_profile_write_scope_or_raise_fn: EnforceProfileWriteScopeFn,
) -> dict:
    profile = await workflow_service.get_employee_record(employee_id=employee_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    ensure_identity_active_for_profile_work(profile)

    current_status = profile.get("workflow_status")

    await enforce_profile_write_scope_or_raise_fn(
        current_user,
        user_role,
        workflow_service,
        profile=profile,
    )

    new_status = workflow_service.validate_submit_transition(
        current_status=current_status,
        user_role=user_role,
        employee_section_completed=bool(profile.get("employee_section_completed")),
        data_entry_section_completed=bool(profile.get("data_entry_section_completed")),
    )

    await workflow_service.persist_submitted(
        employee_id=employee_id,
        remarks=remarks,
        actor_user_id=user_id,
    )

    audit_id = await workflow_service.write_workflow_audit(
        EmployeeWorkflowAuditDTO(
            employee_id=employee_id,
            action="SUBMIT",
            user_id=user_id,
            user_name=current_user.get("name") or "Unknown",
            user_role=user_role,
            status_before=current_status,
            status_after=new_status,
            remarks=remarks,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
        )
    )

    await workflow_service.publish_submitted(
        EmployeeWorkflowEventDTO(
            employee_id=employee_id,
            status=new_status,
            remarks=remarks,
            actor_id=user_id,
            department_id=profile.get("current_department_id") or current_user.get("department_code"),
        )
    )
    return workflow_service.build_workflow_response(
        action="SUBMIT",
        employee_id=employee_id,
        previous_status=current_status,
        new_status=new_status,
        performed_by=user_id,
        audit_log_id=audit_id,
        remarks=remarks,
    )


async def verify_profile_action(
    *,
    employee_id: str,
    remarks: str | None,
    request: Any,
    current_user: dict,
    user_role: str,
    user_id: str,
    workflow_service: EmployeeWorkflowApplicationService,
    enforce_profile_write_scope_or_raise_fn: EnforceProfileWriteScopeFn,
) -> dict:
    profile = await workflow_service.get_employee_record(employee_id=employee_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    current_status = profile.get("workflow_status")

    await enforce_profile_write_scope_or_raise_fn(
        current_user,
        user_role,
        workflow_service,
        profile=profile,
    )

    new_status = workflow_service.validate_verify_transition(
        current_status=current_status,
        user_role=user_role,
        profile_created_by=profile.get("created_by"),
        actor_user_id=user_id,
    )

    await workflow_service.persist_verified(
        employee_id=employee_id,
        remarks=remarks,
        actor_user_id=user_id,
    )

    audit_id = await workflow_service.write_workflow_audit(
        EmployeeWorkflowAuditDTO(
            employee_id=employee_id,
            action="VERIFY",
            user_id=user_id,
            user_name=current_user.get("name") or "Unknown",
            user_role=user_role,
            status_before=current_status,
            status_after=new_status,
            remarks=remarks,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
        )
    )

    await workflow_service.publish_verified(
        EmployeeWorkflowEventDTO(
            employee_id=employee_id,
            status=new_status,
            remarks=remarks,
            actor_id=user_id,
            department_id=profile.get("current_department_id") or current_user.get("department_code"),
        )
    )
    return workflow_service.build_workflow_response(
        action="VERIFY",
        employee_id=employee_id,
        previous_status=current_status,
        new_status=new_status,
        performed_by=user_id,
        audit_log_id=audit_id,
        remarks=remarks,
    )


async def approve_profile_action(
    *,
    employee_id: str,
    remarks: str | None,
    request: Any,
    current_user: dict,
    user_role: str,
    user_id: str,
    workflow_service: EmployeeWorkflowApplicationService,
    enforce_profile_write_scope_or_raise_fn: EnforceProfileWriteScopeFn,
) -> dict:
    profile = await workflow_service.get_employee_record(employee_id=employee_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    current_status = profile.get("workflow_status")

    await enforce_profile_write_scope_or_raise_fn(
        current_user,
        user_role,
        workflow_service,
        profile=profile,
    )

    new_status = workflow_service.validate_approve_transition(
        current_status=current_status,
        user_role=user_role,
        profile_created_by=profile.get("created_by"),
        profile_verified_by=profile.get("verified_by"),
        actor_user_id=user_id,
    )

    await workflow_service.persist_approved(
        employee_id=employee_id,
        remarks=remarks,
        actor_user_id=user_id,
    )

    audit_id = await workflow_service.write_workflow_audit(
        EmployeeWorkflowAuditDTO(
            employee_id=employee_id,
            action="APPROVE",
            user_id=user_id,
            user_name=current_user.get("name") or "Unknown",
            user_role=user_role,
            status_before=current_status,
            status_after=new_status,
            remarks=remarks,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
        )
    )

    await workflow_service.publish_approved(
        EmployeeWorkflowEventDTO(
            employee_id=employee_id,
            status=new_status,
            remarks=remarks,
            actor_id=user_id,
            department_id=profile.get("current_department_id") or current_user.get("department_code"),
        )
    )
    return workflow_service.build_workflow_response(
        action="APPROVE",
        employee_id=employee_id,
        previous_status=current_status,
        new_status=new_status,
        performed_by=user_id,
        audit_log_id=audit_id,
        remarks=remarks,
    )


async def lock_profile_action(
    *,
    employee_id: str,
    remarks: str | None,
    request: Any,
    db: Any,
    current_user: dict,
    user_role: str,
    user_id: str,
    workflow_service: EmployeeWorkflowApplicationService,
    enforce_profile_write_scope_or_raise_fn: EnforceProfileWriteScopeFn,
) -> dict:
    profile = await workflow_service.get_employee_record(employee_id=employee_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    current_status = profile.get("workflow_status")

    await enforce_profile_write_scope_or_raise_fn(
        current_user,
        user_role,
        workflow_service,
        profile=profile,
    )

    new_status = workflow_service.validate_lock_transition(
        current_status=current_status,
        user_role=user_role,
    )

    await workflow_service.persist_locked(
        employee_id=employee_id,
        remarks=remarks,
        actor_user_id=user_id,
    )

    audit_id = await workflow_service.write_workflow_audit(
        EmployeeWorkflowAuditDTO(
            employee_id=employee_id,
            action="LOCK",
            user_id=user_id,
            user_name=current_user.get("name") or "Unknown",
            user_role=user_role,
            status_before=current_status,
            status_after=new_status,
            remarks=remarks,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
        )
    )

    await workflow_service.publish_locked(
        EmployeeWorkflowEventDTO(
            employee_id=employee_id,
            status=new_status,
            remarks=remarks,
            actor_id=user_id,
            department_id=profile.get("current_department_id") or current_user.get("department_code"),
        )
    )
    return workflow_service.build_workflow_response(
        action="LOCK",
        employee_id=employee_id,
        previous_status=current_status,
        new_status=new_status,
        performed_by=user_id,
        audit_log_id=audit_id,
        remarks=remarks,
    )


async def reject_profile_action(
    *,
    employee_id: str,
    remarks: str | None,
    request: Any,
    current_user: dict,
    user_role: str,
    user_id: str,
    workflow_service: EmployeeWorkflowApplicationService,
    enforce_profile_write_scope_or_raise_fn: EnforceProfileWriteScopeFn,
) -> dict:
    profile = await workflow_service.get_employee_record(employee_id=employee_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    current_status = profile.get("workflow_status")

    await enforce_profile_write_scope_or_raise_fn(
        current_user,
        user_role,
        workflow_service,
        profile=profile,
    )

    new_status = workflow_service.validate_reject_transition(
        current_status=current_status,
        user_role=user_role,
        remarks=remarks,
    )

    await workflow_service.persist_rejected(
        employee_id=employee_id,
        remarks=remarks,
        actor_user_id=user_id,
    )

    audit_id = await workflow_service.write_workflow_audit(
        EmployeeWorkflowAuditDTO(
            employee_id=employee_id,
            action="REJECT",
            user_id=user_id,
            user_name=current_user.get("name") or "Unknown",
            user_role=user_role,
            status_before=current_status,
            status_after=new_status,
            remarks=remarks,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
        )
    )

    await workflow_service.publish_rejected(
        EmployeeWorkflowEventDTO(
            employee_id=employee_id,
            status=new_status,
            remarks=remarks,
            actor_id=user_id,
            department_id=profile.get("current_department_id") or current_user.get("department_code"),
        )
    )
    return workflow_service.build_workflow_response(
        action="REJECT",
        employee_id=employee_id,
        previous_status=current_status,
        new_status=new_status,
        performed_by=user_id,
        audit_log_id=audit_id,
        remarks=remarks,
    )
