from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException


ROLE_VERIFIER = "VERIFIER"
ROLE_APPROVER = "APPROVING_AUTHORITY"
ROLE_HOD = "HOD"
ROLE_HOD = "HOD"
DATA_ENTRY_ROLES = {"DEPT_DATA_ENTRY", "DEPARTMENT_DATA_ENTRY", "GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT"}
SUBMITTER_ROLES = DATA_ENTRY_ROLES | {"EMPLOYEE"}


def validate_submit_transition(
	*,
	current_status: str,
	user_role: str,
	employee_section_completed: bool,
	data_entry_section_completed: bool,
) -> str:
	if current_status not in {"DRAFT", "REJECTED"}:
		raise HTTPException(
			status_code=400,
			detail=f"Cannot submit from {current_status}. Must be DRAFT or REJECTED.",
		)
	if user_role not in SUBMITTER_ROLES:
		raise HTTPException(
			status_code=403,
			detail="Only Data Entry or the employee can submit profiles",
		)
	if not employee_section_completed:
		raise HTTPException(
			status_code=400,
			detail="Employee must complete their profile section before submission.",
		)
	if not data_entry_section_completed:
		raise HTTPException(
			status_code=400,
			detail="Data Entry must mark their section complete before submission.",
		)
	return "SUBMITTED"


def validate_verify_transition(
	*,
	current_status: str,
	user_role: str,
	profile_created_by: str | None,
	actor_user_id: str,
) -> str:
	if current_status != "SUBMITTED":
		raise HTTPException(
			status_code=400,
			detail=f"Cannot verify from {current_status}. Must be SUBMITTED.",
		)
	if user_role != ROLE_VERIFIER:
		raise HTTPException(status_code=403, detail="Only Verifier can verify profiles")
	if profile_created_by == actor_user_id:
		raise HTTPException(
			status_code=403,
			detail={
				"error_code": "SEPARATION_OF_DUTIES",
				"message": "You cannot verify a profile you created",
			},
		)
	return "VERIFIED"


def validate_approve_transition(
	*,
	current_status: str,
	user_role: str,
	profile_created_by: str | None,
	profile_verified_by: str | None,
	actor_user_id: str,
) -> str:
	if current_status != "VERIFIED":
		raise HTTPException(
			status_code=400,
			detail=f"Cannot approve from {current_status}. Must be VERIFIED.",
		)
	if user_role != ROLE_APPROVER:
		raise HTTPException(status_code=403, detail="Only Approving Authority can approve profiles")
	if profile_created_by == actor_user_id or profile_verified_by == actor_user_id:
		raise HTTPException(
			status_code=403,
			detail={
				"error_code": "SEPARATION_OF_DUTIES",
				"message": "You cannot approve a profile you created or verified",
			},
		)
	return "APPROVED"


def validate_lock_transition(*, current_status: str, user_role: str) -> str:
	if current_status != "APPROVED":
		raise HTTPException(
			status_code=400,
			detail=f"Cannot lock from {current_status}. Must be APPROVED.",
		)
	if user_role not in {ROLE_APPROVER, ROLE_HOD}:
		raise HTTPException(
			status_code=403,
			detail="Only Approving Authority or HOD can lock profiles",
		)
	return "LOCKED"


def validate_reject_transition(
	*,
	current_status: str,
	user_role: str,
	remarks: str | None,
) -> str:
	if current_status == "SUBMITTED":
		if user_role != ROLE_VERIFIER:
			raise HTTPException(status_code=403, detail="Only Verifier can reject SUBMITTED profiles")
	elif current_status == "VERIFIED":
		if user_role != ROLE_APPROVER:
			raise HTTPException(status_code=403, detail="Only Approver can reject VERIFIED profiles")
	else:
		raise HTTPException(
			status_code=400,
			detail=f"Cannot reject from {current_status}. Must be SUBMITTED or VERIFIED.",
		)

	if not remarks:
		raise HTTPException(status_code=400, detail="Rejection remarks are required")

	return "REJECTED"


def build_workflow_response(
	*,
	action: str,
	employee_id: str,
	previous_status: str,
	new_status: str,
	performed_by: str,
	audit_log_id: str,
	remarks: str | None = None,
) -> dict:
	action_upper = action.upper()
	message_map = {
		"SUBMIT": "Profile submitted for verification",
		"VERIFY": "Profile verified successfully",
		"APPROVE": "Profile approved successfully",
		"LOCK": "Profile locked successfully. It is now read-only.",
	}
	if action_upper == "REJECT":
		message = f"Profile rejected with remarks: {remarks}"
	else:
		message = message_map.get(action_upper, "Workflow action completed")

	return {
		"success": True,
		"message": message,
		"employee_id": employee_id,
		"previous_status": previous_status,
		"new_status": new_status,
		"action_performed": action.lower(),
		"performed_by": performed_by,
		"timestamp": datetime.now(timezone.utc).isoformat(),
		"audit_log_id": audit_log_id,
	}
