from __future__ import annotations

from fastapi import HTTPException

from contexts.rbac.contracts.access_control import has_authority


ROLE_DATA_ENTRY_SET = {"DEPT_DATA_ENTRY", "DEPARTMENT_DATA_ENTRY", "GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT"}
ROLE_VERIFIER = "VERIFIER"
ROLE_APPROVER = "APPROVING_AUTHORITY"

VALID_LIST_TYPES = ("DRAFT", "PROVISIONAL", "FINAL")
PROMOTION_ORDER = {"DRAFT": "PROVISIONAL", "PROVISIONAL": "FINAL"}


def require_role(user: dict, allowed: set[str], action: str) -> None:
    if not any(has_authority(user, authority) for authority in allowed):
        raise HTTPException(403, f"Insufficient authority to {action}")


def validate_list_type(list_type: str) -> str:
    normalized = (list_type or "DRAFT").upper()
    if normalized not in VALID_LIST_TYPES:
        raise HTTPException(400, f"Invalid list_type. Must be one of {VALID_LIST_TYPES}")
    return normalized
