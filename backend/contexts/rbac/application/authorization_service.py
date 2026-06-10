"""Authorization service — scope resolution, permission checks, role management.

Provides the application-layer gateway for RBAC enforcement:
- Scope resolution (GLOBAL / DEPARTMENT / EMPLOYEE)
- Permission derivation from authorities
- Permission + scope compound checks
- Role assignment / revocation helpers
"""
from __future__ import annotations

from typing import Any, Iterable

from contexts.rbac.domain.models import AUTHORITY_PERMISSIONS, Authority, Permission


GLOBAL = "GLOBAL"
DEPARTMENT = "DEPARTMENT"
EMPLOYEE = "EMPLOYEE"


DEPARTMENT_AUTHORITIES = {"DEPT_DATA_ENTRY", "HOD"}


def _normalize_authorities(raw: Any) -> set[str]:
    authorities = raw or []
    if isinstance(authorities, str):
        authorities = [authorities]
    normalized = {str(authority).strip().upper() for authority in authorities if authority}
    if not normalized:
        normalized.add("EMPLOYEE")
    return normalized


def _user_authorities(user: dict[str, Any] | None) -> set[str]:
    payload = user or {}
    authorities = payload.get("authorities") or payload.get("authority") or []
    return _normalize_authorities(authorities)


def _user_department_code(user: dict[str, Any] | None) -> str | None:
    payload = user or {}
    value = payload.get("department_code") or payload.get("department_id")
    if value is None:
        return None
    normalized = str(value).strip().upper()
    return normalized or None


def _is_owner(user: dict[str, Any] | None, target_employee_id: str | None) -> bool:
    payload = user or {}
    caller_employee_id = str(payload.get("employee_id") or "").strip()
    target = str(target_employee_id or "").strip()
    return bool(caller_employee_id and target and caller_employee_id == target)


def assignRole(current_roles: Iterable[str] | None, role: str) -> list[str]:
    normalized = [str(item).strip().upper() for item in (current_roles or []) if item]
    next_roles = list(dict.fromkeys(normalized))
    role_key = str(role or "").strip().upper()
    if role_key and role_key not in next_roles:
        next_roles.append(role_key)
    return next_roles


def revokeRole(current_roles: Iterable[str] | None, role: str) -> list[str]:
    role_key = str(role or "").strip().upper()
    next_roles = [str(item).strip().upper() for item in (current_roles or []) if item]
    return [item for item in next_roles if item != role_key]


def resolveUserPermissions(user: dict[str, Any] | None) -> set[str]:
    payload = user or {}
    explicit = payload.get("permissions") or []
    if isinstance(explicit, str):
        explicit = [explicit]
    normalized_explicit = {str(permission).strip() for permission in explicit if permission}
    if normalized_explicit:
        return normalized_explicit

    derived: set[str] = set()
    for authority_key in _user_authorities(payload):
        try:
            authority = Authority(authority_key)
        except ValueError:
            continue
        derived.update(permission.value for permission in AUTHORITY_PERMISSIONS.get(authority, set()))
    return derived


def resolveScopeAccess(
    user: dict[str, Any] | None,
    *,
    target_employee_id: str | None = None,
    target_department_code: str | None = None,
    user_department_code: str | None = None,
) -> dict[str, Any]:
    authorities = _user_authorities(user)

    if authorities & DEPARTMENT_AUTHORITIES:
        scope = DEPARTMENT
    elif authorities == {"EMPLOYEE"}:
        scope = EMPLOYEE
    else:
        scope = GLOBAL

    if scope == GLOBAL:
        return {"scope": GLOBAL, "allowed": True, "reason": "GLOBAL scope"}

    if scope == DEPARTMENT:
        expected = (user_department_code or _user_department_code(user) or "").strip().upper()
        target_dept = str(target_department_code or "").strip().upper()
        if not expected:
            return {
                "scope": DEPARTMENT,
                "allowed": False,
                "reason": "DEPARTMENT scope requires caller department mapping",
            }
        if target_dept and expected and target_dept != expected:
            return {
                "scope": DEPARTMENT,
                "allowed": False,
                "reason": "DEPARTMENT scope mismatch",
            }
        return {"scope": DEPARTMENT, "allowed": True, "reason": "DEPARTMENT scope"}

    if target_employee_id and not _is_owner(user, target_employee_id):
        return {
            "scope": EMPLOYEE,
            "allowed": False,
            "reason": "EMPLOYEE scope requires self access",
        }
    return {"scope": EMPLOYEE, "allowed": True, "reason": "EMPLOYEE self scope"}


def canPerformAction(
    user: dict[str, Any] | None,
    *,
    required_permissions: Iterable[str | Permission] | None = None,
    require_all_permissions: bool = False,
    self_scope_only: bool = False,
    target_employee_id: str | None = None,
    target_department_code: str | None = None,
    user_department_code: str | None = None,
) -> bool:
    permissions = resolveUserPermissions(user)
    checks = [permission.value if isinstance(permission, Permission) else str(permission) for permission in (required_permissions or [])]

    if checks:
        if require_all_permissions:
            if not all(check in permissions for check in checks):
                return False
        elif not any(check in permissions for check in checks):
            return False

    scope = resolveScopeAccess(
        user,
        target_employee_id=target_employee_id,
        target_department_code=target_department_code,
        user_department_code=user_department_code,
    )
    if self_scope_only:
        return bool(scope.get("scope") == EMPLOYEE and scope.get("allowed"))
    return bool(scope.get("allowed"))
