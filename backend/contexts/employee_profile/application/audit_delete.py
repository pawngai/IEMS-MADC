from __future__ import annotations

from typing import Any, Awaitable, Callable, Optional

from fastapi import HTTPException

from contexts.employee_profile.application.services.workflow_engine import EmployeeWorkflowApplicationService
from contexts.employee_profile.contracts.dto import EmployeeWorkflowAuditDTO
from contexts.rbac.domain.models import Permission
from contexts.rbac.application.access_control import has_permission, is_owner


EnforceDepartmentScopeFn = Callable[[dict, str, EmployeeWorkflowApplicationService, Optional[str]], Awaitable[Optional[str]]]
EnforceProfileWriteScopeFn = Callable[..., Awaitable[Any]]
NormalizeDepartmentCodeFn = Callable[[Optional[str]], Optional[str]]


def _clean_objectid(data: Any) -> Any:
    if isinstance(data, dict):
        return {key: _clean_objectid(value) for key, value in data.items() if key != "_id"}
    if isinstance(data, list):
        return [_clean_objectid(item) for item in data]
    return data


async def get_audit_trail_response(
    *,
    employee_id: str,
    current_user: dict,
    user_role: str,
    workflow_service: EmployeeWorkflowApplicationService,
    enforce_department_scope_or_raise_fn: EnforceDepartmentScopeFn,
    normalize_department_code_fn: NormalizeDepartmentCodeFn,
) -> dict[str, Any]:
    if has_permission(current_user, Permission.PROFILE_READ_ALL):
        pass
    elif has_permission(current_user, Permission.PROFILE_READ_OWN) and is_owner(current_user, employee_id):
        pass
    else:
        raise HTTPException(status_code=403, detail="Insufficient permission to view audit trail")

    profile = await workflow_service.get_employee_record(employee_id=employee_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    scoped_department = await enforce_department_scope_or_raise_fn(
        current_user,
        user_role,
        workflow_service,
    )
    if scoped_department:
        profile_department = normalize_department_code_fn(profile.get("current_department_id"))
        if profile_department != scoped_department:
            raise HTTPException(
                status_code=403,
                detail="Department-scoped access only allows your own department records.",
            )

    logs = await workflow_service.list_profile_audit_trail(employee_id=employee_id, limit=100)
    cleaned_logs = [_clean_objectid(log) for log in logs]

    return {
        "employee_id": employee_id,
        "audit_trail": cleaned_logs,
        "total_entries": len(cleaned_logs),
    }


async def delete_profile_response(
    *,
    employee_id: str,
    request: Any,
    current_user: dict,
    user_role: str,
    user_id: str,
    workflow_service: EmployeeWorkflowApplicationService,
    enforce_profile_write_scope_or_raise_fn: EnforceProfileWriteScopeFn,
    data_entry_roles: set[str],
    draft_status_value: str,
) -> dict[str, Any]:
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

    if current_status != draft_status_value:
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "CANNOT_DELETE",
                "message": f"Only DRAFT profiles can be deleted. Current status: {current_status}",
            },
        )

    if profile.get("created_by") != user_id:
        raise HTTPException(status_code=403, detail="Only the creator can delete this profile")

    if user_role not in data_entry_roles:
        raise HTTPException(status_code=403, detail="Only Data Entry can delete profiles")

    await workflow_service.archive_and_delete_profile_record(profile=profile, actor_user_id=user_id)

    await workflow_service.write_profile_audit(
        EmployeeWorkflowAuditDTO(
            employee_id=employee_id,
            action="DELETE",
            user_id=user_id,
            user_name=current_user.get("name") or "Unknown",
            user_role=user_role,
            previous_data=profile,
            status_before=current_status,
            remarks="Profile deleted",
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
        )
    )

    return {
        "success": True,
        "message": "Profile deleted successfully",
        "employee_id": employee_id,
    }
