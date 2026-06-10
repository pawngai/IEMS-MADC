from __future__ import annotations

import os
from typing import Optional

from contexts.employee_profile.application.services.workflow_engine import EmployeeWorkflowApplicationService
from contexts.employee_profile.contracts.dto import EmployeeWorkflowAuditDTO


def check_role_permission(user_role: str, required_roles: list[str]) -> bool:
    return user_role in required_roles


def get_changed_fields(old_data: dict, new_data: dict) -> list[str]:
    changed: list[str] = []
    for key in new_data:
        if key in old_data and old_data[key] != new_data[key]:
            changed.append(key)
        elif key not in old_data and new_data[key] is not None:
            changed.append(key)
    return changed


def get_user_id(current_user: dict) -> str:
    return current_user.get("sub") or current_user.get("user_id") or ""


def normalize_department_code(value: Optional[str]) -> str:
    return str(value or "").strip().upper()


def sanitize_account_provisioning_response(account_info: dict) -> dict:
    safe_fields = {
        "user_id",
        "email",
        "must_change_password",
        "message",
        "error",
    }
    expose_temp_password = str(
        os.getenv("IEMS_E2E_EXPOSE_TEMP_PASSWORD", "")
    ).strip().lower() in {"1", "true", "yes", "on"}
    if expose_temp_password:
        safe_fields.add("temp_password")
    return {k: v for k, v in account_info.items() if k in safe_fields}


async def create_audit_log(
    *,
    workflow_service: EmployeeWorkflowApplicationService,
    payload: EmployeeWorkflowAuditDTO,
) -> None:
    await workflow_service.write_profile_audit(payload)

