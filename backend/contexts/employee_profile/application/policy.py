from __future__ import annotations

from fastapi import HTTPException

ROLE_DEPT_DATA_ENTRY = "DEPT_DATA_ENTRY"
ROLE_GLOBAL_DATA_ENTRY = "GLOBAL_DATA_ENTRY"
ROLE_DEALING_ASSISTANT = "DEALING_ASSISTANT"
DATA_ENTRY_ROLES = [ROLE_DEPT_DATA_ENTRY, ROLE_GLOBAL_DATA_ENTRY, ROLE_DEALING_ASSISTANT]
ROLE_VERIFIER = "VERIFIER"
ROLE_APPROVER = "APPROVING_AUTHORITY"
ROLE_HOD = "HOD"
ROLE_HOD = "HOD"
ROLE_AUDITOR = "AUDITOR"
DEPARTMENT_SCOPED_ROLES = {ROLE_DEPT_DATA_ENTRY, ROLE_HOD}


def enforce_system_admin_readonly(user: dict, action: str) -> None:
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
