"""
Access control helpers for RBAC and ownership checks.

Keeps policy logic consistent across API modules.
"""

from fastapi import HTTPException
from typing import Iterable, Set

from contexts.identity_access.rbac.domain.models import Authority, Permission
from contexts.identity_access.rbac.application.authorization_service import (
    _normalize_authorities,
    canPerformAction,
    resolveScopeAccess,
    resolveUserPermissions,
)


def get_permissions(user: dict) -> Set[str]:
    """
    Return permissions for a user.
    Prefer JWT-provided permissions; otherwise derive from authorities.
    """
    return set(resolveUserPermissions(user))


def has_permission(user: dict, *permissions: Iterable[str | Permission]) -> bool:
    user_perms = get_permissions(user)
    for perm in permissions:
        key = perm.value if isinstance(perm, Permission) else str(perm)
        if key in user_perms:
            return True
    return False


def has_authority(user: dict, *authorities: Iterable[str | Authority]) -> bool:
    raw = user.get("authorities") or []
    if isinstance(raw, str):
        raw = [raw]
    if not raw:
        single = user.get("authority")
        if single:
            raw = [single]

    user_auths = _normalize_authorities(raw)
    for auth in authorities:
        key = auth.value if isinstance(auth, Authority) else str(auth)
        if str(key).strip().upper() in user_auths:
            return True
    return False


def has_active_authority(user: dict, *authorities: Iterable[str | Authority]) -> bool:
    raw = user.get("authorities") or []
    if isinstance(raw, str):
        raw = [raw]
    if not raw:
        single = user.get("authority")
        if single:
            raw = [single]

    normalized_authorities = _normalize_authorities(raw)
    normalized_targets = {
        (authority.value if isinstance(authority, Authority) else str(authority)).strip().upper()
        for authority in authorities
    }

    active_role = str(user.get("active_role") or "").strip().upper()
    if active_role and active_role in normalized_authorities:
        return active_role in normalized_targets

    return any(target in normalized_authorities for target in normalized_targets)


def is_owner(user: dict, employee_id: str) -> bool:
    scope = resolveScopeAccess(user, target_employee_id=employee_id)
    return bool(scope.get("scope") == "EMPLOYEE" and scope.get("allowed"))


def require_permissions(user: dict, *permissions: Iterable[str | Permission]) -> None:
    if not has_permission(user, *permissions):
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "INSUFFICIENT_PERMISSION",
                "message": "You do not have the required permissions for this action.",
                "required_permissions": [
                    p.value if isinstance(p, Permission) else str(p) for p in permissions
                ],
            },
        )


def require_owner_or_permissions(
    user: dict,
    employee_id: str,
    *permissions: Iterable[str | Permission],
) -> None:
    if is_owner(user, employee_id):
        return

    required = [
        p.value if isinstance(p, Permission) else str(p)
        for p in permissions
    ]
    if canPerformAction(
        user,
        required_permissions=required,
        target_employee_id=employee_id,
    ):
        return
    raise HTTPException(
        status_code=403,
        detail={
            "error_code": "ACCESS_DENIED",
            "message": "You are not allowed to access this employee record.",
            "required_permissions": [
                p.value if isinstance(p, Permission) else str(p) for p in permissions
            ],
        },
    )


def forbid_system_admin_write(user: dict, action: str) -> None:
    """Defense-in-depth guard: block SYSTEM_ADMIN from transactional writes.
    
    The primary defense is the AUTHORITY_PERMISSIONS matrix which excludes
    write permissions. This function catches any code path that checks
    authority directly instead of going through the permission model.
    """
    if has_authority(user, Authority.SYSTEM_ADMIN):
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "SYSTEM_ADMIN_FORBIDDEN",
                "message": f"SYSTEM_ADMIN cannot perform {action} on transactional records.",
                "governance_rule": "SYSTEM_ADMIN is read-only for employee/service records.",
            },
        )


def require_system_admin(user: dict) -> None:
    """Ensure user has SYSTEM_ADMIN authority. Canonical single implementation."""
    if not has_authority(user, Authority.SYSTEM_ADMIN):
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "SYSTEM_ADMIN_REQUIRED",
                "message": "SYSTEM_ADMIN authority required for this action.",
            },
        )


def prevent_self_action(user: dict, target_user_id: str, action: str) -> None:
    """Prevent admin from performing destructive actions on their own account."""
    caller_id = user.get("sub") or user.get("id")
    if caller_id and caller_id == target_user_id:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "SELF_ACTION_FORBIDDEN",
                "message": f"Cannot {action} your own account.",
            },
        )
