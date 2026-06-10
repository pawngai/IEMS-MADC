from __future__ import annotations

from typing import Any

from contexts.audit.application import service as audit_app_service


async def recordAuditEntry(
    db,
    *,
    user_id: str,
    user_name: str,
    authority: str,
    action: str,
    resource_type: str,
    resource_id: str,
    details: dict[str, Any] | None = None,
    old_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
    workflow_stage: str | None = None,
    workflow_action: str | None = None,
):
    return await audit_app_service.log_audit(
        db,
        user_id=user_id,
        user_name=user_name,
        authority=authority,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        old_value=old_value,
        new_value=new_value,
        workflow_stage=workflow_stage,
        workflow_action=workflow_action,
    )


async def buildAuditTrail(
    db,
    *,
    current_user: dict,
    resource_type: str | None = None,
    action: str | None = None,
    employee_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    if resource_type == "service_book" or employee_id:
        return await audit_app_service.get_service_book_logs(
            db,
            current_user=current_user,
            employee_id=employee_id,
            limit=limit,
        )
    return await audit_app_service.get_audit_logs(
        db,
        current_user=current_user,
        resource_type=resource_type,
        action=action,
        limit=limit,
    )
