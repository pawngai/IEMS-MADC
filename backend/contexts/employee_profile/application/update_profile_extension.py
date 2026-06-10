from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from app_platform.domain_separation.enforcement import ProfilePayloadValidator
from app_platform.domain_separation.validators import DomainSeparationError
from fastapi import HTTPException

from contexts.employee_profile.application.services.workflow_engine import EmployeeWorkflowApplicationService
from contexts.employee_profile.contracts.dto import EmployeeWorkflowAuditDTO
from contexts.employee_profile.domain.constants import (
    WORKFLOW_STATUS_APPROVED,
    WORKFLOW_STATUS_DRAFT,
    WORKFLOW_STATUS_LOCKED,
    WORKFLOW_STATUS_REJECTED,
    WORKFLOW_STATUS_VERIFIED,
)
from contexts.employee_profile.infrastructure.profile_schema_gateway import (
    validate_contact_details,
    validate_identity_documents,
)
from contexts.rbac.application.access_control import is_owner, require_permissions
from contexts.rbac.domain.models import Permission

EnforceProfileWriteScopeFn = Callable[..., Awaitable[Any]]
CreateAuditLogFn = Callable[..., Awaitable[Any]]
GetChangedFieldsFn = Callable[[dict, dict], list[str]]

CONTACT_FIELDS = {
    "mobile_primary",
    "mobile_alternate",
    "email_personal",
    "email_official",
    "address_line1",
    "address_line2",
    "city",
    "district",
    "state",
    "pincode",
    "present_address_line1",
    "present_address_line2",
    "present_city",
    "present_district",
    "present_state",
    "present_pincode",
    "emergency_name",
    "emergency_phone",
    "emergency_relation",
}
IDENTIFIER_FIELDS = {
    "aadhaar_number",
    "pan_number",
}
AUTO_EMPLOYEE_COMPLETION_FIELDS = {
    "mobile_primary",
    "email_personal",
    "address_line1",
    "city",
    "state",
    "pincode",
    "present_address_line1",
    "present_city",
    "present_state",
    "present_pincode",
}
BASE_DATA_ENTRY_COMPLETION_FIELDS: set[str] = set()
EMPLOYMENT_TYPE_REQUIRED_FIELDS = {
    "REGULAR": set(),
    "CONTRACT": {
        "current_department_id",
        "current_designation_id",
        "date_of_initial_engagement",
        "engagement_order_no",
        "engagement_end_date",
        "fixed_monthly_amount",
    },
    "MUSTER_ROLL": {
        "current_department_id",
        "current_designation_id",
        "date_of_initial_engagement",
        "engagement_order_no",
        "daily_wage_rate",
    },
    "FIXED_PAY": {
        "current_department_id",
        "current_designation_id",
        "date_of_initial_engagement",
        "engagement_order_no",
        "fixed_monthly_amount",
    },
    "CO_TERMINUS": {
        "current_department_id",
        "current_designation_id",
        "date_of_initial_engagement",
        "engagement_order_no",
        "pay_level",
        "basic_pay",
    },
    "WAGES": {
        "current_department_id",
        "current_designation_id",
        "date_of_initial_engagement",
        "daily_wage_rate",
    },
    "CONTRACTUAL": {
        "contract_order_no",
        "contract_start_date",
        "contract_end_date",
        "consolidated_pay",
        "contract_authority",
        "renewal_allowed",
    },
    "DAILY_WAGE": {
        "engagement_order_no",
        "muster_roll_number",
        "daily_wage_rate",
        "engagement_office",
        "nature_of_work",
    },
    "DEPUTATION": {
        "deputation_order_no",
        "parent_department",
        "parent_designation",
        "lien_status",
        "deputation_start_date",
        "deputation_end_date",
    },
}


def _has_completion_value(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    return value not in (None, False)


def _get_profile_value(profile: dict[str, Any], field: str) -> Any:
    return (
        profile.get(field)
        or (profile.get("contact") or {}).get(field)
        or (profile.get("identifiers") or {}).get(field)
    )


def _build_projected_profile(
    profile: dict[str, Any],
    *,
    extension_updates: dict[str, Any],
    contact_updates: dict[str, Any],
    identifier_updates: dict[str, Any],
) -> dict[str, Any]:
    projected = dict(profile)
    projected_contact = dict(profile.get("contact") or {})
    projected_identifiers = dict(profile.get("identifiers") or {})
    projected_contact.update(contact_updates)
    projected_identifiers.update(identifier_updates)
    projected.update(extension_updates)
    projected["contact"] = projected_contact
    projected["identifiers"] = projected_identifiers
    return projected


def _derive_completion_flags(profile: dict[str, Any]) -> dict[str, bool]:
    employment_type = str(profile.get("employment_type") or "").strip().upper()
    employee_complete = all(
        _has_completion_value(_get_profile_value(profile, field))
        for field in AUTO_EMPLOYEE_COMPLETION_FIELDS
    )
    data_entry_fields = BASE_DATA_ENTRY_COMPLETION_FIELDS | EMPLOYMENT_TYPE_REQUIRED_FIELDS.get(
        employment_type, set()
    )
    data_entry_complete = all(
        _has_completion_value(_get_profile_value(profile, field))
        for field in data_entry_fields
    )
    return {
        "employee_section_completed": employee_complete,
        "data_entry_section_completed": data_entry_complete,
    }


async def update_profile_extension_response(
    *,
    employee_id: str,
    updates_model: Any,
    request: Any,
    db: Any,
    current_user: dict,
    user_role: str,
    user_id: str,
    workflow_service: EmployeeWorkflowApplicationService,
    enforce_profile_write_scope_or_raise_fn: EnforceProfileWriteScopeFn,
    create_audit_log_fn: CreateAuditLogFn,
    get_changed_fields_fn: GetChangedFieldsFn,
    data_entry_roles: set[str],
    data_entry_editable_fields: set[str],
    ess_editable_fields: set[str],
    immutable_after_verification: set[str],
) -> dict[str, Any]:
    profile = await workflow_service.get_employee_record(employee_id=employee_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    current_status = profile.get("workflow_status", "DRAFT")

    await enforce_profile_write_scope_or_raise_fn(
        current_user,
        user_role,
        workflow_service,
        profile=profile,
    )

    if current_status == WORKFLOW_STATUS_LOCKED:
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "RECORD_LOCKED",
                "message": "This profile is LOCKED and cannot be modified",
            },
        )

    update_data = {
        key: value
        for key, value in updates_model.model_dump().items()
        if value is not None
    }
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")

    try:
        payload_for_validation = dict(update_data)
        payload_for_validation.setdefault(
            "employment_type", profile.get("employment_type")
        )
        ProfilePayloadValidator.validate_update(payload_for_validation, current_status)
    except DomainSeparationError as error:
        await workflow_service.add_domain_violation_log(
            log={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "violation_type": error.error_code,
                "user_id": user_id or "unknown",
                "user_role": user_role,
                "endpoint": f"/api/employee-profiles/{employee_id}",
                "method": "PUT",
                "violating_fields": error.violating_fields,
                "domain": error.domain,
            }
        )
        raise error.to_http_exception()

    if user_role in data_entry_roles:
        require_permissions(current_user, Permission.PROFILE_UPDATE_ALL)
        if current_status in [WORKFLOW_STATUS_DRAFT, WORKFLOW_STATUS_REJECTED]:
            allowed_fields = data_entry_editable_fields
        else:
            raise HTTPException(
                status_code=403,
                detail={
                    "error_code": "INVALID_STATUS",
                    "message": f"Cannot edit profile in {current_status} status. Must be DRAFT or REJECTED.",
                },
            )
    elif user_role == "EMPLOYEE":
        if not is_owner(current_user, employee_id):
            raise HTTPException(
                status_code=403, detail="Employees can only update their own profile"
            )
        require_permissions(current_user, Permission.PROFILE_UPDATE_OWN_LIMITED)
        if current_status not in {
            WORKFLOW_STATUS_DRAFT,
            WORKFLOW_STATUS_REJECTED,
            WORKFLOW_STATUS_APPROVED,
        }:
            raise HTTPException(
                status_code=403,
                detail={
                    "error_code": "SELF_SERVICE_NOT_READY",
                    "message": (
                        "Employee self-service profile updates are available only "
                        "while the employee record is DRAFT, REJECTED, or APPROVED."
                    ),
                    "workflow_status": current_status,
                },
            )
        allowed_fields = ess_editable_fields
    else:
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "INSUFFICIENT_PERMISSION",
                "message": "You do not have permission to update employee profile details",
            },
        )

    if current_status in [WORKFLOW_STATUS_VERIFIED, WORKFLOW_STATUS_APPROVED]:
        blocked_fields = []
        for field in update_data:
            if field in immutable_after_verification:
                old_value = profile.get(field) or profile.get("contact", {}).get(field)
                if old_value and old_value != update_data[field]:
                    blocked_fields.append(field)
        if blocked_fields:
            raise HTTPException(
                status_code=403,
                detail={
                    "error_code": "FIELD_IMMUTABLE",
                    "message": f"These fields cannot be modified after verification: {', '.join(blocked_fields)}",
                    "blocked_fields": blocked_fields,
                },
            )

    filtered_updates = {
        key: value for key, value in update_data.items() if key in allowed_fields
    }

    if not filtered_updates:
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "NO_PERMITTED_FIELDS",
                "message": "None of the provided fields can be updated with your role",
                "attempted_fields": list(update_data.keys()),
                "allowed_fields": list(allowed_fields),
            },
        )

    contact_updates = {
        key: value for key, value in filtered_updates.items() if key in CONTACT_FIELDS
    }
    identifier_updates = {
        key: value
        for key, value in filtered_updates.items()
        if key in IDENTIFIER_FIELDS
    }
    extension_updates = {
        key: value
        for key, value in filtered_updates.items()
        if key not in CONTACT_FIELDS and key not in IDENTIFIER_FIELDS
    }

    if contact_updates:
        merged_contact = dict(profile.get("contact") or {})
        merged_contact.update(contact_updates)
        validated_contact = validate_contact_details(merged_contact)
        for field in list(contact_updates.keys()):
            contact_updates[field] = validated_contact.get(field)

    if identifier_updates:
        merged_identifiers = dict(profile.get("identifiers") or {})
        merged_identifiers.update(identifier_updates)
        validated_identifiers = validate_identity_documents(merged_identifiers)
        for field in list(identifier_updates.keys()):
            identifier_updates[field] = validated_identifiers.get(field)

    projected_profile = _build_projected_profile(
        profile,
        extension_updates=extension_updates,
        contact_updates=contact_updates,
        identifier_updates=identifier_updates,
    )
    completion_flags = _derive_completion_flags(projected_profile)
    extension_updates.update(completion_flags)

    mongo_update = {
        "$set": {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": user_id,
            "version": profile.get("version", 1) + 1,
        }
    }

    for field, value in extension_updates.items():
        mongo_update["$set"][field] = value
    for field, value in contact_updates.items():
        mongo_update["$set"][f"contact.{field}"] = value
    for field, value in identifier_updates.items():
        mongo_update["$set"][f"identifiers.{field}"] = value

    modified_count = await workflow_service.update_profile_record(
        employee_id=employee_id, mongo_update=mongo_update
    )
    if modified_count == 0:
        raise HTTPException(status_code=500, detail="Update failed")

    changed_fields = get_changed_fields_fn(profile, filtered_updates)
    await create_audit_log_fn(
        workflow_service=workflow_service,
        payload=EmployeeWorkflowAuditDTO(
            employee_id=employee_id,
            action="UPDATE_PROFILE_EXTENSION",
            user_id=user_id,
            user_name=current_user.get("name", "Unknown"),
            user_role=user_role,
            previous_data={
                key: profile.get(key) or profile.get("contact", {}).get(key)
                for key in changed_fields
            },
            new_data=filtered_updates,
            changed_fields=changed_fields,
            status_before=current_status,
            status_after=current_status,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
        ),
    )

    return {
        "success": True,
        "message": "Employee profile extension updated successfully",
        "employee_id": employee_id,
        "updated_fields": list(filtered_updates.keys()),
        "workflow_status": current_status,
    }
