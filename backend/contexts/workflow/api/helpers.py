from __future__ import annotations

from fastapi import HTTPException
from contexts.identity_access.contracts.access_control import has_authority


PENDING_STAGE_AUTHORITIES: dict[str, set[str]] = {
    "SUBMITTED": {"VERIFIER"},
    "VERIFIED": {"APPROVING_AUTHORITY", "DDO"},
    "APPROVED": {"APPROVING_AUTHORITY", "HOD"},
}

def resolve_actor_id(current_user: dict) -> str:
    actor_id = str(current_user.get("employee_id") or current_user.get("sub") or "")
    if not actor_id:
        raise HTTPException(status_code=401, detail="Unable to resolve current user")
    return actor_id


def validate_pending_stage_access(*, stage: str, current_user: dict) -> str:
    normalized_stage = stage.strip().upper()
    allowed_authorities = PENDING_STAGE_AUTHORITIES.get(normalized_stage)
    if allowed_authorities is None:
        raise HTTPException(status_code=404, detail="Unknown workflow stage")

    if not has_authority(current_user, *allowed_authorities):
        raise HTTPException(status_code=403, detail="Insufficient authority for pending stage")
    return normalized_stage
