from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from app_platform.forms.contracts.hooks import get_field_aliases, validate_form_data_hook
from contexts.employee_master.profile.api.forms_validation import (
    filtered_form_errors,
    flatten_employee_record_for_forms,
    raise_form_validation_failed,
)
from contexts.employee_master.profile.application.access_scope import (
    enforce_profile_write_scope_or_raise as _enforce_profile_write_scope_or_raise,
)
from contexts.employee_master.profile.application.commands.profile_commands import (
    update_profile_extension_response,
)
from contexts.employee_master.profile.application.dependencies import get_current_user, get_db
from contexts.employee_master.profile.application.factory import build_employee_workflow_service
from contexts.employee_master.profile.application.policy import (
    DATA_ENTRY_ROLES,
    DEPARTMENT_SCOPED_ROLES,
)
from contexts.employee_master.profile.application.router_support import (
    create_audit_log,
    get_changed_fields,
    get_user_id,
)
from contexts.employee_master.profile.application.services.workflow_engine import (
    EmployeeWorkflowApplicationService,
)
from contexts.employee_master.profile.contracts.profile_write import (
    ESS_EDITABLE_FIELDS,
    IMMUTABLE_AFTER_VERIFICATION,
    PROFILE_EXTENSION_EDITABLE_FIELDS,
    EmployeeProfileExtensionUpsert,
)
from contexts.identity_access.contracts.user_role import get_user_role


write_router = APIRouter()
FIELD_ALIASES = get_field_aliases()

PROFILE_EXTENSION_UPDATE_DESCRIPTION = (
    "Update employee-owned profile enrichment after the EmployeeIdentity already exists. "
    "Use this endpoint for contact, address, personal enrichment, and identity-document fields."
)


def validate_form_data(*args, **kwargs):
    return validate_form_data_hook(*args, **kwargs)


def _validate_profile_payload_with_forms(
    *,
    payload: dict,
    employment_type: Optional[str],
    workflow_stage: str,
    actionable_payload: Optional[dict] = None,
) -> None:
    try:
        errors = validate_form_data(
            data=payload,
            employment_type=employment_type,
            workflow_stage=workflow_stage,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    actionable_errors = filtered_form_errors(
        errors,
        actionable_payload if actionable_payload is not None else payload,
        field_aliases=FIELD_ALIASES,
    )
    if actionable_errors:
        raise_form_validation_failed(actionable_errors)


def enforce_system_admin_readonly(user: dict, action: str):
    authorities = user.get("authorities", [])
    if "SYSTEM_ADMIN" not in authorities:
        return

    forbidden_actions = [
        "CREATE",
        "UPDATE",
        "DELETE",
        "SUBMIT",
        "VERIFY",
        "APPROVE",
        "REJECT",
        "LOCK",
    ]
    if action.upper() in forbidden_actions:
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "SYSTEM_ADMIN_FORBIDDEN",
                "message": f"SYSTEM_ADMIN cannot perform {action} on employee records. This role has READ_ONLY access to transactional data.",
                "governance_rule": "SYSTEM_ADMIN configures policy but NEVER alters employee service history.",
            },
        )


def get_employee_workflow_service(
    request: Request, db=None
) -> EmployeeWorkflowApplicationService:
    if db is None:
        db = get_db()
    return build_employee_workflow_service(request=request, db=db)


async def enforce_profile_write_scope_or_raise(
    current_user: dict,
    user_role: str,
    workflow_service: EmployeeWorkflowApplicationService,
    profile: Optional[dict] = None,
    target_department: Optional[str] = None,
) -> Optional[str]:
    return await _enforce_profile_write_scope_or_raise(
        current_user,
        user_role,
        workflow_service,
        DEPARTMENT_SCOPED_ROLES,
        profile=profile,
        target_department=target_department,
    )


@write_router.put(
    "/{employee_id}",
    response_model=dict,
    summary="Update employee profile extension",
    description=PROFILE_EXTENSION_UPDATE_DESCRIPTION,
)
async def update_profile_extension(
    employee_id: str,
    updates: EmployeeProfileExtensionUpsert,
    request: Request,
    current_user: dict = Depends(get_current_user),
    workflow_service: EmployeeWorkflowApplicationService = Depends(
        get_employee_workflow_service
    ),
):
    db = get_db()
    enforce_system_admin_readonly(current_user, "UPDATE")

    profile = await workflow_service.get_employee_record(employee_id=employee_id)
    if profile is not None:
        updates_payload = {
            key: value
            for key, value in updates.model_dump(mode="json").items()
            if value is not None
        }
        merged_payload = flatten_employee_record_for_forms(profile)
        merged_payload.update(updates_payload)

        _validate_profile_payload_with_forms(
            payload=merged_payload,
            employment_type=merged_payload.get("employment_type"),
            workflow_stage=profile.get("workflow_status") or "DRAFT",
            actionable_payload=updates_payload,
        )

    user_role = get_user_role(current_user)
    user_id = get_user_id(current_user)
    return await update_profile_extension_response(
        employee_id=employee_id,
        updates_model=updates,
        request=request,
        db=db,
        current_user=current_user,
        user_role=user_role,
        user_id=user_id,
        workflow_service=workflow_service,
        enforce_profile_write_scope_or_raise_fn=enforce_profile_write_scope_or_raise,
        create_audit_log_fn=create_audit_log,
        get_changed_fields_fn=get_changed_fields,
        data_entry_roles=set(DATA_ENTRY_ROLES),
        data_entry_editable_fields=PROFILE_EXTENSION_EDITABLE_FIELDS,
        ess_editable_fields=ESS_EDITABLE_FIELDS,
        immutable_after_verification=IMMUTABLE_AFTER_VERIFICATION,
    )
