from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException


ROLE_VERIFIER = "VERIFIER"
ROLE_ACTIVATOR = "APPROVING_AUTHORITY"
DATA_ENTRY_ROLES = {"DEPT_DATA_ENTRY", "DEPARTMENT_DATA_ENTRY", "GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT"}


def validate_identity_submit_transition(
    *,
    current_status: str,
    user_role: str,
) -> str:
    if current_status not in {"DRAFT", "REJECTED"}:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot submit from '{current_status}'. Must be DRAFT or REJECTED.",
        )
    if user_role not in DATA_ENTRY_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Only Data Entry staff can submit an identity for verification.",
        )
    return "SUBMITTED"


def validate_identity_verify_transition(
    *,
    current_status: str,
    user_role: str,
    identity_created_by: str | None,
    actor_user_id: str,
) -> str:
    if current_status != "SUBMITTED":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot verify from '{current_status}'. Must be SUBMITTED.",
        )
    if user_role != ROLE_VERIFIER:
        raise HTTPException(
            status_code=403,
            detail="Only Verifier can verify identity records.",
        )
    if identity_created_by and identity_created_by == actor_user_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "SEPARATION_OF_DUTIES",
                "message": "You cannot verify an identity record you created.",
            },
        )
    return "VERIFIED"


def validate_identity_activate_transition(
    *,
    current_status: str,
    user_role: str,
    identity_created_by: str | None,
    identity_verified_by: str | None,
    actor_user_id: str,
) -> str:
    if current_status != "VERIFIED":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot activate from '{current_status}'. Must be VERIFIED.",
        )
    if user_role != ROLE_ACTIVATOR:
        raise HTTPException(
            status_code=403,
            detail="Only Approving Authority can activate identity records.",
        )
    if actor_user_id and actor_user_id in {identity_created_by, identity_verified_by}:
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "SEPARATION_OF_DUTIES",
                "message": "You cannot activate an identity record you created or verified.",
            },
        )
    return "ACTIVE"


def validate_identity_reject_transition(
    *,
    current_status: str,
    user_role: str,
    remarks: str | None,
) -> str:
    if current_status == "SUBMITTED":
        if user_role != ROLE_VERIFIER:
            raise HTTPException(
                status_code=403,
                detail="Only Verifier can reject a SUBMITTED identity record.",
            )
    elif current_status == "VERIFIED":
        if user_role != ROLE_ACTIVATOR:
            raise HTTPException(
                status_code=403,
                detail="Only Approving Authority can reject a VERIFIED identity record.",
            )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reject from '{current_status}'. Must be SUBMITTED or VERIFIED.",
        )
    if not remarks:
        raise HTTPException(
            status_code=400,
            detail="Rejection remarks are required.",
        )
    return "REJECTED"


def build_identity_workflow_response(
    *,
    action: str,
    employee_id: str,
    previous_status: str,
    new_status: str,
    performed_by: str,
    remarks: str | None = None,
) -> dict:
    action_upper = action.upper()
    message_map = {
        "SUBMIT": "Identity submitted for verification.",
        "VERIFY": "Identity verified successfully.",
        "ACTIVATE": "Identity activated. Employee is now live in the system.",
        "REJECT": f"Identity rejected. Remarks: {remarks}",
    }
    return {
        "success": True,
        "message": message_map.get(action_upper, "Workflow action completed."),
        "employee_id": employee_id,
        "previous_status": previous_status,
        "new_status": new_status,
        "action_performed": action.lower(),
        "performed_by": performed_by,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
