from __future__ import annotations

from typing import Any, Optional

from contexts.audit.repository import audit_repository as repo
from contexts.rbac.contracts.models import AuditLog, Permission
from contexts.rbac.contracts.access_control import require_permissions
from contexts.audit.domain.models import ImmutableAuditLog


def _build_audit_log(
    *,
    user_id: str,
    user_name: str,
    authority: str,
    action: str,
    resource_type: str,
    resource_id: str,
    details: Optional[dict[str, Any]] = None,
    old_value: Optional[dict[str, Any]] = None,
    new_value: Optional[dict[str, Any]] = None,
    workflow_stage: Optional[str] = None,
    workflow_action: Optional[str] = None,
) -> AuditLog:
    return AuditLog(
        user_id=user_id,
        user_name=user_name,
        authority=authority,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        old_value=old_value,
        new_value=new_value,
        workflow_stage=workflow_stage,
        workflow_action=workflow_action,
    )


async def log_audit(
    db,
    *,
    user_id: str,
    user_name: str,
    authority: str,
    action: str,
    resource_type: str,
    resource_id: str,
    details: Optional[dict[str, Any]] = None,
    old_value: Optional[dict[str, Any]] = None,
    new_value: Optional[dict[str, Any]] = None,
    workflow_stage: Optional[str] = None,
    workflow_action: Optional[str] = None,
) -> AuditLog:
    audit = _build_audit_log(
        user_id=user_id,
        user_name=user_name,
        authority=authority,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        old_value=old_value,
        new_value=new_value,
        workflow_stage=workflow_stage,
        workflow_action=workflow_action,
    )
    if db is None:
        return audit

    await repo.insert_audit_log(db, audit.model_dump())
    return audit


async def get_audit_logs(
    db,
    *,
    current_user: dict,
    resource_type: Optional[str],
    action: Optional[str],
    limit: int,
) -> list[dict[str, Any]]:
    require_permissions(current_user, Permission.AUDIT_READ_ALL.value)
    query: dict[str, Any] = {}
    if resource_type:
        query["resource_type"] = resource_type
    if action:
        query["action"] = action
    return await repo.list_audit_logs(db, query, limit=limit)


async def get_service_book_logs(
    db,
    *,
    current_user: dict,
    employee_id: Optional[str],
    limit: int,
) -> list[dict[str, Any]]:
    require_permissions(current_user, Permission.AUDIT_READ_ALL.value)
    query: dict[str, Any] = {}
    if employee_id:
        query["employee_id"] = employee_id
    return await repo.list_service_book_audit_logs(db, query, limit=limit)


async def create_immutable_audit_log(
    db,
    *,
    user_id: str,
    user_name: str,
    user_role: str,
    user_authorities: list[str],
    entity_type: str,
    entity_id: str,
    action: str,
    from_status: str | None = None,
    to_status: str | None = None,
    remarks: str | None = None,
    rejection_reason: str | None = None,
    request=None,
) -> str:
    import hashlib

    log_entry = ImmutableAuditLog(
        user_id=user_id,
        user_name=user_name,
        user_role=user_role,
        user_authorities=user_authorities,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        from_status=from_status,
        to_status=to_status,
        remarks=remarks,
        rejection_reason=rejection_reason,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )

    hash_data = f"{log_entry.id}:{log_entry.timestamp}:{log_entry.user_id}:{log_entry.entity_id}:{log_entry.action}"
    log_entry_dict = log_entry.model_dump()
    log_entry_dict["integrity_hash"] = hashlib.sha256(hash_data.encode()).hexdigest()

    if db is not None:
        await repo.insert_immutable_audit_log(db, log_entry_dict)
    return log_entry_dict["id"]


async def list_immutable_audit_logs(
    db,
    *,
    entity_type: str,
    entity_id: str,
    limit: int = 1000,
    sort_asc: bool = True,
) -> list[dict[str, Any]]:
    if db is None:
        return []
    return await repo.list_immutable_audit_logs(
        db,
        {"entity_id": entity_id, "entity_type": entity_type},
        limit=limit,
        sort_asc=sort_asc,
    )
