from __future__ import annotations

from app.security.principal import Principal
from shared_kernel.base import PolicyDeniedError


GLOBAL_ROLES = {"SYSTEM_ADMIN", "AUDITOR"}


def enforce(principal: Principal, action: str, resource: str, context: dict | None = None) -> None:
    context = context or {}
    if any(role in GLOBAL_ROLES for role in principal.roles):
        return
    if not principal.user_id:
        raise PolicyDeniedError(f"Denied {action} on {resource}: unauthenticated principal")
