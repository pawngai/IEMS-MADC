from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any, List, Optional, Set

import bcrypt
import jwt
from app_platform.config.settings import settings
from contexts.identity.domain.module_access_policy import (
    module_access_fallback,
    normalize_module_access_config,
)
from fastapi import HTTPException

# â”€â”€ Password policy â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
MIN_PASSWORD_LENGTH = 8
PASSWORD_PATTERN = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]).{8,}$'
)


def validate_password_strength(password: str) -> None:
    """Enforce password complexity: min 8 chars, upper, lower, digit, special."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Password must be at least {MIN_PASSWORD_LENGTH} characters long",
        )
    if not PASSWORD_PATTERN.match(password):
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character",
        )


# â”€â”€ Login rate limiting â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
from contexts.rbac.contracts.models import (
    AUTHORITY_PERMISSIONS,
    WORKFLOW_TRANSITIONS,
    Authority,
    Permission,
    TokenResponse,
)
from contexts.rbac.contracts.models import UserResponse as AuthUserResponse
from contexts.rbac.contracts.models import (
    WorkflowStage,
)
from contexts.identity.infrastructure import repo
from contexts.identity.contracts.schemas import (
    ActivityLogResponse,
    UserCreate,
    UserPasswordUpdate,
    UserResponse,
    UserUpdate,
)
from contexts.employee_master.contracts.identity_directory import get_employee_department_code

logger = logging.getLogger(__name__)


_DATA_ENTRY_AUTHORITIES = {"DEPT_DATA_ENTRY", "GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT", "SECTION_OFFICER"}
_VERIFICATION_AUTHORITIES = {"VERIFIER"}
_APPROVAL_AUTHORITIES = {"APPROVING_AUTHORITY", "DDO"}
_ATTESTATION_AUTHORITIES = {"HOD", "APPOINTING_AUTHORITY", "DISCIPLINARY_AUTHORITY"}

_ESS_PORTAL_PERMISSIONS = {
    Permission.DOCUMENT_READ_OWN.value,
    Permission.SERVICE_BOOK_READ_OWN.value,
    Permission.LEAVE_APPLY_OWN.value,
    Permission.LEAVE_READ_OWN.value,
}
_SERVICE_BOOK_MODULE_PERMISSIONS = {
    Permission.SERVICE_BOOK_READ_ALL.value,
    Permission.SERVICE_BOOK_ENTRY_CREATE.value,
    Permission.SERVICE_BOOK_ENTRY_SUBMIT.value,
    Permission.SERVICE_BOOK_ENTRY_VERIFY.value,
    Permission.SERVICE_BOOK_ENTRY_APPROVE.value,
    Permission.SERVICE_BOOK_ENTRY_ATTEST.value,
    Permission.SERVICE_BOOK_OPENING_CREATE.value,
    Permission.SERVICE_BOOK_OPENING_UPDATE.value,
    Permission.SERVICE_BOOK_OPENING_SUBMIT.value,
    Permission.SERVICE_BOOK_OPENING_VERIFY.value,
    Permission.SERVICE_BOOK_OPENING_APPROVE.value,
    Permission.SERVICE_BOOK_PRINT.value,
    Permission.SERVICE_BOOK_SUPERSEDE.value,
}
_LEAVE_MODULE_PERMISSIONS = {
    Permission.LEAVE_READ_ALL.value,
    Permission.LEAVE_RECOMMEND.value,
    Permission.LEAVE_SANCTION.value,
}
_AUDIT_MODULE_PERMISSIONS = {
    Permission.AUDIT_READ_ALL.value,
}
_ADMIN_CONSOLE_PERMISSIONS = {
    Permission.USER_MANAGEMENT.value,
    Permission.SYSTEM_CONFIG.value,
}


def _baseline_allowed_modules(authorities: list[str] | None) -> set[str]:
    authority_list = authorities or []
    allowed: set[str] = set()
    permissions = get_permissions_for_authorities(authority_list)

    if permissions & _ESS_PORTAL_PERMISSIONS:
        allowed.add("ess_portal")

    if permissions & _SERVICE_BOOK_MODULE_PERMISSIONS:
        allowed.add("service_book")

    if permissions & _LEAVE_MODULE_PERMISSIONS:
        allowed.add("leave")

    if permissions & _AUDIT_MODULE_PERMISSIONS:
        allowed.add("audit")

    if permissions & _ADMIN_CONSOLE_PERMISSIONS:
        allowed.update({"admin_console", "user_management", "department_management"})

    authority_set = set(authority_list)
    if authority_set & _DATA_ENTRY_AUTHORITIES:
        allowed.add("data_entry")
    if authority_set & _VERIFICATION_AUTHORITIES:
        allowed.add("verification")
    if authority_set & _APPROVAL_AUTHORITIES:
        allowed.add("approval")
    if authority_set & _ATTESTATION_AUTHORITIES:
        allowed.add("attestation")

    return allowed


def _get_audit_service_module():
    return import_module("contexts.audit.application.service")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def get_permissions_for_authorities(authorities: List[str]) -> Set[str]:
    permissions: Set[str] = set()
    for auth_str in authorities:
        try:
            auth = Authority(auth_str)
        except ValueError:
            continue
        permissions.update([p.value for p in AUTHORITY_PERMISSIONS.get(auth, set())])
    return permissions


def _candidate_login_emails(email: str) -> List[str]:
    """Return normalized login email candidates."""
    normalized = (email or "").strip().lower()
    if not normalized:
        return []

    return [normalized]


def create_token(user_data: dict) -> str:
    """Create a short-lived access token (30 minutes).

    The token carries authorities and derived permissions for frontend
    access control checks. Permissions are derived from authorities.
    """
    authorities = user_data.get("authorities", [Authority.EMPLOYEE.value])
    permissions = list(get_permissions_for_authorities(authorities))

    payload = {
        "sub": user_data["id"],
        "email": user_data["email"],
        "authorities": authorities,
        "permissions": permissions,
        "name": user_data["name"],
        "employee_id": user_data.get("employee_id"),
        "department_code": user_data.get("department_code"),
        "token_version": int(user_data.get("token_version") or 0),
        "exp": datetime.now(timezone.utc).timestamp() + ACCESS_TOKEN_EXPIRE_SECONDS,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


ACCESS_TOKEN_EXPIRE_SECONDS = 1800  # 30 minutes
REFRESH_TOKEN_EXPIRE_SECONDS = 604800  # 7 days


def _create_refresh_token() -> str:
    """Generate an opaque, cryptographically-random refresh token."""
    return secrets.token_urlsafe(48)


def _hash_refresh_token(refresh_token: str) -> str:
    return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()


async def _store_refresh_token(db, user_id: str, refresh_token: str) -> None:
    """Persist refresh token in MongoDB for later validation / revocation."""
    if db is None:
        return
    await db.refresh_tokens.insert_one(
        {
            "token_hash": _hash_refresh_token(refresh_token),
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (
                datetime.now(timezone.utc)
                + timedelta(seconds=REFRESH_TOKEN_EXPIRE_SECONDS)
            ).isoformat(),
        }
    )


async def _validate_refresh_token(db, refresh_token: str) -> dict:
    """
    Look up a refresh token, verify it hasn't expired, and return the
    associated user record.  Raises HTTPException on failure.
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    token_hash = _hash_refresh_token(refresh_token)
    record = await db.refresh_tokens.find_one_and_delete({"token_hash": token_hash})
    if not record:
        # Compatibility for legacy plaintext tokens issued before hashing.
        record = await db.refresh_tokens.find_one_and_delete({"token": refresh_token})
    if not record:
        raise HTTPException(status_code=401, detail="Invalid or revoked refresh token")

    expires_at = datetime.fromisoformat(record["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        # Expired — clean up and reject
        raise HTTPException(status_code=401, detail="Refresh token expired")

    user = await repo.find_user_by_id(db, record["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")
    if user.get("is_active") is False:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    return user


async def _revoke_refresh_token(db, refresh_token: str) -> None:
    """Delete a specific refresh token (logout)."""
    if db is None:
        return
    await db.refresh_tokens.delete_many(
        {"$or": [{"token_hash": _hash_refresh_token(refresh_token)}, {"token": refresh_token}]}
    )


async def _revoke_all_refresh_tokens(db, user_id: str) -> None:
    """Revoke every refresh token and invalidate existing access tokens for a user."""
    if db is None:
        return
    await db.refresh_tokens.delete_many({"user_id": user_id})
    users = getattr(db, "users", None)
    if users is not None and hasattr(users, "update_one"):
        await users.update_one({"id": user_id}, {"$inc": {"token_version": 1}})


# Use canonical require_system_admin from contexts.rbac.contracts.access_control
from contexts.rbac.contracts.access_control import prevent_self_action, require_system_admin

# Department-scoped authorities that require the user to belong to the target department
DEPARTMENT_SCOPED_AUTHORITIES = {"DEPT_DATA_ENTRY", "HOD"}


async def _validate_department_scoped_roles(
    db,
    target_user: dict,
    new_authorities: list[str],
    department_code: str | None = None,
) -> None:
    """Ensure that department-scoped roles are only assigned to employees
    belonging to the specified department.

    Raises HTTPException(400/403) if the employee's profile department
    does not match the department_code being assigned.
    """
    dept_roles = set(new_authorities) & DEPARTMENT_SCOPED_AUTHORITIES
    if not dept_roles:
        return  # No department-scoped roles being assigned — nothing to check

    # Resolve department: explicit param â†’ user record â†’ fail
    target_dept = (department_code or "").strip().upper() or (
        target_user.get("department_code") or ""
    ).strip().upper()

    # Look up the employee's profile to get their actual department
    employee_id = target_user.get("employee_id") or ""
    if not employee_id:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot assign department-scoped role(s) {', '.join(sorted(dept_roles))} "
                f"— user has no linked employee_id."
            ),
        )

    profile_dept = await get_employee_department_code(
        db,
        employee_id=employee_id,
    ) or ""

    if not profile_dept:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot assign department-scoped role(s) {', '.join(sorted(dept_roles))} "
                f"— employee {employee_id} has no department in their profile."
            ),
        )

    if not target_dept:
        # No department specified — auto-use profile department (will be set by caller)
        return

    if target_dept != profile_dept:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Employee {employee_id} belongs to department {profile_dept}, "
                f"cannot assign role(s) {', '.join(sorted(dept_roles))} to department {target_dept}."
            ),
        )


def _valid_authorities() -> list[str]:
    """Derive valid authorities from the Authority enum to avoid desync."""
    return [a.value for a in Authority]


async def login(db_optional, credentials: dict) -> TokenResponse:
    email = credentials.get("email", "")
    password = credentials.get("password", "")

    if db_optional is not None:
        user = None
        for candidate in _candidate_login_emails(email):
            user = await repo.find_user_by_email(db_optional, candidate)
            if user:
                break

        # â”€â”€ Account lockout check â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if user:
            failed = user.get("failed_login_attempts", 0)
            locked_until = user.get("locked_until")
            if locked_until:
                lock_time = datetime.fromisoformat(locked_until)
                if datetime.now(timezone.utc) < lock_time:
                    remaining = (
                        int(
                            (lock_time - datetime.now(timezone.utc)).total_seconds()
                            // 60
                        )
                        + 1
                    )
                    raise HTTPException(
                        status_code=429,
                        detail=f"Account locked due to too many failed attempts. Try again in {remaining} minute(s).",
                    )
                # Lock expired — reset counters
                await repo.update_user(
                    db_optional,
                    user["id"],
                    {
                        "failed_login_attempts": 0,
                        "locked_until": None,
                    },
                )
                failed = 0

        if user and verify_password(password, user.get("password_hash", "")):
            # Reset failed attempts on success
            if user.get("failed_login_attempts", 0) > 0:
                await repo.update_user(
                    db_optional,
                    user["id"],
                    {
                        "failed_login_attempts": 0,
                        "locked_until": None,
                        "last_login": datetime.now(timezone.utc).isoformat(),
                    },
                )
            else:
                await repo.update_user(
                    db_optional,
                    user["id"],
                    {
                        "last_login": datetime.now(timezone.utc).isoformat(),
                    },
                )

            # Check if deactivated
            if user.get("is_active") is False:
                raise HTTPException(
                    status_code=403,
                    detail="Account is deactivated. Contact your administrator.",
                )

            authorities = user.get("authorities", [Authority.EMPLOYEE.value])
            permissions = list(get_permissions_for_authorities(authorities))
            token = create_token(user)
            refresh_token = _create_refresh_token()
            await _store_refresh_token(db_optional, user["id"], refresh_token)

            # Best-effort audit logging
            try:
                await _get_audit_service_module().log_audit(
                    db_optional,
                    user_id=user["id"],
                    user_name=user["name"],
                    authority=(
                        authorities[0] if authorities else Authority.EMPLOYEE.value
                    ),
                    action="LOGIN",
                    resource_type="auth",
                    resource_id=user["id"],
                    details={"email": user["email"]},
                )
            except Exception:
                logger.exception(
                    "Failed to write audit log for successful login",
                    extra={"email": user.get("email")},
                )

            return TokenResponse(
                access_token=token,
                refresh_token=refresh_token,
                expires_in=ACCESS_TOKEN_EXPIRE_SECONDS,
                user=AuthUserResponse(
                    id=user["id"],
                    email=user["email"],
                    name=user["name"],
                    authorities=authorities,
                    permissions=permissions,
                    employee_id=user.get("employee_id"),
                    department_code=user.get("department_code"),
                    must_change_password=user.get("must_change_password", False),
                ),
            )

        # â”€â”€ Failed attempt tracking â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if user and db_optional is not None:
            new_failed = user.get("failed_login_attempts", 0) + 1
            updates: dict[str, Any] = {"failed_login_attempts": new_failed}
            if new_failed >= MAX_FAILED_ATTEMPTS:
                lock_until = (
                    datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
                ).isoformat()
                updates["locked_until"] = lock_until
            await repo.update_user(db_optional, user["id"], updates)

    raise HTTPException(status_code=401, detail="Invalid credentials")


async def refresh_access_token(db, refresh_token: str) -> dict:
    """
    Validate the refresh token, issue a fresh access token + refresh token pair,
    and revoke the old refresh token (rotation).
    """
    user = await _validate_refresh_token(db, refresh_token)

    # Issue new tokens with up-to-date authorities from the DB
    new_access = create_token(user)
    new_refresh = _create_refresh_token()
    await _store_refresh_token(db, user["id"], new_refresh)

    authorities = user.get("authorities", [Authority.EMPLOYEE.value])
    permissions = list(get_permissions_for_authorities(authorities))

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_SECONDS,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "authorities": authorities,
            "permissions": permissions,
            "employee_id": user.get("employee_id"),
            "department_code": user.get("department_code"),
        },
    }


async def logout(db, refresh_token: str | None) -> dict:
    """Revoke the refresh token so it can no longer be used."""
    if refresh_token:
        await _revoke_refresh_token(db, refresh_token)
    return {"message": "Logged out successfully"}


async def me_from_token(db_optional, current_user: dict) -> AuthUserResponse:
    # When DB is available, return the live user record so that role
    # changes made through the admin console are reflected immediately
    # without requiring the user to log out and log back in.
    if db_optional is not None:
        user = await repo.find_user_by_email(db_optional, current_user.get("email", ""))
        if user:
            authorities = user.get("authorities", current_user.get("authorities", []))
            permissions = list(get_permissions_for_authorities(authorities))
            return AuthUserResponse(
                id=user.get("id", current_user["sub"]),
                email=user.get("email", current_user["email"]),
                name=user.get("name", current_user["name"]),
                authorities=authorities,
                permissions=permissions,
                employee_id=user.get("employee_id", current_user.get("employee_id")),
                department_code=user.get(
                    "department_code", current_user.get("department_code")
                ),
            )

    # Offline fallback: return whatever is in the JWT
    # Derive permissions from authorities since the JWT no longer carries them
    from contexts.rbac.contracts.access_control import get_permissions as _get_perms

    return AuthUserResponse(
        id=current_user["sub"],
        email=current_user["email"],
        name=current_user["name"],
        authorities=current_user.get("authorities", []),
        permissions=list(_get_perms(current_user)),
        employee_id=current_user.get("employee_id"),
        department_code=current_user.get("department_code"),
    )


async def get_module_access(db_optional, current_user: dict) -> dict:
    authorities = current_user.get("authorities", []) or []
    baseline_allowed = _baseline_allowed_modules(authorities)

    if db_optional is None:
        fallback = module_access_fallback(settings)
        if fallback.get("mode") == "allow_all" or not baseline_allowed:
            return fallback
        return {
            "mode": fallback.get("mode", "deny_by_default"),
            "allowed_modules": sorted(baseline_allowed),
        }

    config = await repo.get_system_config(db_optional)
    matrix = normalize_module_access_config(config)
    if matrix is None:
        fallback = module_access_fallback(settings)
        if fallback.get("mode") == "allow_all" or not baseline_allowed:
            return fallback
        return {
            "mode": fallback.get("mode", "deny_by_default"),
            "allowed_modules": sorted(baseline_allowed),
        }

    allowed: set[str] = set()
    for auth in authorities:
        flags = matrix.get(auth, {}) if isinstance(matrix, dict) else {}
        if not isinstance(flags, dict):
            continue
        for module_id, enabled in flags.items():
            if enabled:
                allowed.add(module_id)

    return {"mode": "config", "allowed_modules": sorted(allowed)}


def get_rbac_matrix() -> dict:
    matrix: dict[str, list[str]] = {}
    for authority in Authority:
        if authority in AUTHORITY_PERMISSIONS:
            matrix[authority.value] = [
                p.value for p in AUTHORITY_PERMISSIONS[authority]
            ]

    return {
        "authorities": [a.value for a in Authority],
        "permissions": [p.value for p in Permission],
        "matrix": matrix,
        "workflow_stages": [s.value for s in WorkflowStage],
        "workflow_transitions": {
            stage.value: {
                "next_stages": [s.value for s in trans["next_stages"]],
                "required_authority": (
                    [a.value for a in trans["required_authority"]]
                    if isinstance(trans["required_authority"], list)
                    else (
                        trans["required_authority"].value
                        if trans["required_authority"]
                        else None
                    )
                ),
                "can_edit": trans["can_edit"],
            }
            for stage, trans in WORKFLOW_TRANSITIONS.items()
        },
    }
