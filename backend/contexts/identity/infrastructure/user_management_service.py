from __future__ import annotations

import re
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException
from contexts.identity_access.contracts.models import Authority
from contexts.identity_access.contracts.access_control import has_authority
from contexts.identity.infrastructure import repo
from contexts.identity.contracts.schemas import UserCreate, UserPasswordUpdate, UserResponse, UserUpdate
from contexts.employee_master.contracts.identity_directory import find_identity
from contexts.employee_master.contracts.profile_directory import (
    count_profiles as count_employee_profiles,
    find_profile_view,
    list_profiles,
)

from contexts.identity.infrastructure.auth_session_service import (
    _revoke_all_refresh_tokens,
    hash_password,
    validate_password_strength,
    verify_password,
)
from contexts.identity_access.contracts.authorization_service import assignRole, revokeRole
# Use canonical require_system_admin from contexts.identity_access.contracts.access_control
from contexts.identity_access.contracts.access_control import prevent_self_action, require_system_admin
from contexts.identity.infrastructure.user_management_audit import _log_activity, _log_role_change
from contexts.identity.infrastructure.user_management_roles import (
    ACCOUNT_PROVISIONING_READY_STAGE,
    DEPARTMENT_SCOPED_AUTHORITIES,
    NON_EXCLUSIVE_AUTHORITIES,
    _require_employee_account_ready,
    _valid_authorities,
    _validate_department_scoped_roles,
    _validate_exclusive_role_assignment,
)


def _to_user_response(user: dict[str, Any]) -> UserResponse:
    return UserResponse(
        id=user.get("id", ""),
        email=user.get("email", ""),
        name=user.get("name", ""),
        authorities=user.get("authorities", []),
        employee_id=user.get("employee_id"),
        office_code=user.get("office_code"),
        department_code=user.get("department_code"),
        is_active=user.get("is_active", True),
        created_at=user.get("created_at"),
    )


def _require_employee_directory_access(current_user: dict) -> None:
    if has_authority(current_user, Authority.SYSTEM_ADMIN) or has_authority(current_user, Authority.VERIFIER):
        return
    raise HTTPException(
        status_code=403,
        detail={
            "error_code": "ACCESS_DENIED",
            "message": "Employee directory access requires SYSTEM_ADMIN or VERIFIER authority.",
        },
    )


async def list_users(
    db,
    *,
    skip: int,
    limit: int,
    search: Optional[str],
    authority: Optional[str],
    current_user: dict,
) -> list[UserResponse]:
    require_system_admin(current_user)

    query: dict[str, Any] = {}
    if search:
        safe_search = re.escape(search)
        query["$or"] = [
            {"name": {"$regex": safe_search, "$options": "i"}},
            {"email": {"$regex": safe_search, "$options": "i"}},
        ]
    if authority:
        query["authorities"] = authority

    users = await repo.list_users(
        db, query, skip=skip, limit=limit, projection={"_id": 0, "password_hash": 0}
    )
    return [_to_user_response(u) for u in users]


async def get_user_count(db, *, authority: Optional[str], current_user: dict) -> dict:
    require_system_admin(current_user)

    query: dict[str, Any] = {}
    if authority:
        query["authorities"] = authority

    count = await repo.count_users(db, query)
    return {"count": count}


async def list_employee_directory(
    db,
    *,
    skip: int,
    limit: int,
    search: Optional[str],
    department: Optional[str],
    employment_type: Optional[str],
    workflow_status: Optional[str],
    designation_id: Optional[str],
    office_id: Optional[str],
    employee_status: Optional[str],
    recruitment_mode: Optional[str],
    pay_level: Optional[str],
    service: Optional[str],
    service_group: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
    sort_by: Optional[str],
    sort_dir: Optional[str],
    current_user: dict,
) -> list[dict[str, Any]]:
    _require_employee_directory_access(current_user)
    return await list_profiles(
        db,
        search=search,
        workflow_status=workflow_status,
        employment_type=employment_type,
        department_code=department,
        designation_id=designation_id,
        office_id=office_id,
        employee_status=employee_status,
        recruitment_mode=recruitment_mode,
        pay_level=pay_level,
        service=service,
        service_group=service_group,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=skip,
        sort_by=sort_by,
        sort_dir=sort_dir or "asc",
    )


async def get_employee_directory_count(
    db,
    *,
    search: Optional[str],
    department: Optional[str],
    employment_type: Optional[str],
    workflow_status: Optional[str],
    designation_id: Optional[str],
    office_id: Optional[str],
    employee_status: Optional[str],
    recruitment_mode: Optional[str],
    pay_level: Optional[str],
    service: Optional[str],
    service_group: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
    current_user: dict,
) -> dict[str, int]:
    _require_employee_directory_access(current_user)
    count = await count_employee_profiles(
        db,
        search=search,
        workflow_status=workflow_status,
        employment_type=employment_type,
        department_code=department,
        designation_id=designation_id,
        office_id=office_id,
        employee_status=employee_status,
        recruitment_mode=recruitment_mode,
        pay_level=pay_level,
        service=service,
        service_group=service_group,
        date_from=date_from,
        date_to=date_to,
    )
    return {"count": count}


async def get_user(db, user_id: str, *, current_user: dict) -> UserResponse:
    require_system_admin(current_user)
    user = await repo.find_user_by_id(
        db, user_id, projection={"_id": 0, "password_hash": 0}
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _to_user_response(user)



async def create_user(db, user_data: UserCreate, *, current_user: dict) -> UserResponse:
    require_system_admin(current_user)

    normalized_email = str(user_data.email).strip().lower()

    existing = await repo.find_user_by_email(db, normalized_email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    valid = set(_valid_authorities())
    for auth in user_data.authorities:
        if auth not in valid:
            raise HTTPException(status_code=400, detail=f"Invalid authority: {auth}")

    # Enforce: each authority (except EMPLOYEE) can only be held by one user
    await _validate_exclusive_role_assignment(db, user_data.authorities)

    user_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    new_user = {
        "id": user_id,
        "email": normalized_email,
        "password_hash": hash_password(user_data.password),
        "name": user_data.name,
        "authorities": user_data.authorities,
        "employee_id": user_data.employee_id,
        "office_code": user_data.office_code,
        "department_code": user_data.department_code,
        "is_active": True,
        "created_at": created_at,
        "created_by": current_user["sub"],
    }
    await repo.insert_user(db, new_user)

    await _log_activity(
        db,
        action="USER_CREATED",
        current_user=current_user,
        target_user={"id": user_id, "email": normalized_email, "name": user_data.name},
        details={"authorities": user_data.authorities},
    )

    return _to_user_response(new_user)


async def update_user(
    db, user_id: str, user_data: UserUpdate, *, current_user: dict
) -> UserResponse:
    require_system_admin(current_user)

    # Prevent self-deactivation
    if user_data.is_active is False:
        prevent_self_action(current_user, user_id, "deactivate")

    user = await repo.find_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_authorities = user.get("authorities", [])
    role_changed = False

    update_data: dict[str, Any] = {}
    if user_data.name is not None:
        update_data["name"] = user_data.name
    if user_data.authorities is not None:
        valid = set(_valid_authorities())
        for auth in user_data.authorities:
            if auth not in valid:
                raise HTTPException(
                    status_code=400, detail=f"Invalid authority: {auth}"
                )
        # Enforce: department-scoped roles can only be assigned to employees in that department
        new_dept_roles = set(user_data.authorities) & DEPARTMENT_SCOPED_AUTHORITIES
        if new_dept_roles - set(old_authorities):
            # New dept-scoped roles being added; validate department membership
            await _validate_department_scoped_roles(
                db,
                user,
                user_data.authorities,
                department_code=user_data.department_code,
            )
        # Enforce: each authority (except EMPLOYEE) can only be held by one user
        newly_added = list(set(user_data.authorities) - set(old_authorities))
        if newly_added:
            await _validate_exclusive_role_assignment(
                db, newly_added, exclude_user_id=user_id
            )
        update_data["authorities"] = user_data.authorities
        if set(old_authorities) != set(user_data.authorities):
            role_changed = True
    if user_data.employee_id is not None:
        update_data["employee_id"] = user_data.employee_id
    if user_data.office_code is not None:
        update_data["office_code"] = user_data.office_code
    if user_data.department_code is not None:
        update_data["department_code"] = user_data.department_code
    if user_data.is_active is not None:
        update_data["is_active"] = user_data.is_active

    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        update_data["updated_by"] = current_user["sub"]
        await repo.update_user(db, user_id, update_data)

        await _log_activity(
            db,
            action="USER_UPDATED",
            current_user=current_user,
            target_user={
                "id": user_id,
                "email": user.get("email"),
                "name": user.get("name"),
            },
            details={"changes": list(update_data.keys())},
        )

        if role_changed:
            await _log_role_change(
                db,
                current_user=current_user,
                target_user={
                    "id": user_id,
                    "email": user.get("email"),
                    "name": user.get("name"),
                },
                old_roles=old_authorities,
                new_roles=user_data.authorities or [],
            )
            # Role changes must invalidate active refresh sessions.
            await _revoke_all_refresh_tokens(db, user_id)

    updated = await repo.find_user_by_id(
        db, user_id, projection={"_id": 0, "password_hash": 0}
    )
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    return _to_user_response(updated)


async def patch_user_authorities(
    db, user_id: str, patch, *, current_user: dict
) -> UserResponse:
    """Atomically add/remove specific authorities without replacing the full list."""
    require_system_admin(current_user)

    user = await repo.find_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_authorities = list(user.get("authorities", []))
    valid = set(_valid_authorities())

    add_list = []
    if patch.add:
        for auth in patch.add:
            if auth not in valid:
                raise HTTPException(
                    status_code=400, detail=f"Invalid authority: {auth}"
                )
            add_list = assignRole(add_list, auth)

    remove_list = []
    if patch.remove:
        for auth in patch.remove:
            if auth not in valid:
                raise HTTPException(
                    status_code=400, detail=f"Invalid authority: {auth}"
                )
            remove_list = assignRole(remove_list, auth)

    # Prevent conflicting patch operations by removing any role from add-list when it is also in remove-list.
    if add_list and remove_list:
        for auth in list(remove_list):
            add_list = revokeRole(add_list, auth)

    # Enforce: department-scoped roles can only be assigned to employees in that department
    if add_list:
        await _validate_department_scoped_roles(
            db,
            user,
            add_list,
            department_code=patch.department_code,
        )

    # Enforce: each authority (except EMPLOYEE) can only be held by one user
    if add_list:
        await _validate_exclusive_role_assignment(
            db, add_list, exclude_user_id=user_id
        )

    extra_set: dict[str, Any] = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": current_user["sub"],
    }
    if patch.department_code is not None:
        normalized_department_code = str(patch.department_code).strip().upper()
        if normalized_department_code:
            extra_set["department_code"] = normalized_department_code

    updated = await repo.patch_user_authorities(
        db,
        user_id,
        add=add_list or None,
        remove=remove_list or None,
        extra_set=extra_set,
    )

    if not updated:
        raise HTTPException(status_code=404, detail="User not found after update")

    new_authorities = updated.get("authorities", [])
    if set(old_authorities) != set(new_authorities):
        await _log_role_change(
            db,
            current_user=current_user,
            target_user={
                "id": user_id,
                "email": user.get("email"),
                "name": user.get("name"),
            },
            old_roles=old_authorities,
            new_roles=new_authorities,
        )
        # Role changes must invalidate active refresh sessions.
        await _revoke_all_refresh_tokens(db, user_id)

    return _to_user_response({**updated, "authorities": new_authorities})


async def update_user_password(
    db, user_id: str, password_data: UserPasswordUpdate, *, current_user: dict
) -> dict:
    require_system_admin(current_user)
    user = await repo.find_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updates = {
        "password_hash": hash_password(password_data.new_password),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": current_user["sub"],
    }
    await repo.update_user(db, user_id, updates)

    # Revoke all refresh tokens; force re-login with new password
    await _revoke_all_refresh_tokens(db, user_id)

    await _log_activity(
        db,
        action="PASSWORD_RESET",
        current_user=current_user,
        target_user={
            "id": user_id,
            "email": user.get("email"),
            "name": user.get("name"),
        },
        details=None,
    )
    return {"message": "Password updated successfully"}


async def change_own_password(db, password_data, *, current_user: dict) -> dict:
    """Self-service password change (used after first login with temp password)."""
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = await repo.find_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify current password
    if not verify_password(
        password_data.current_password, user.get("password_hash", "")
    ):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    # Enforce password complexity
    validate_password_strength(password_data.new_password)

    # Update password and clear must_change_password flag
    updates = {
        "password_hash": hash_password(password_data.new_password),
        "must_change_password": False,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await repo.update_user(db, user_id, updates)

    # Revoke all refresh tokens; force re-login with new password
    await _revoke_all_refresh_tokens(db, user_id)

    return {"message": "Password changed successfully"}


async def auto_create_employee_account(
    db,
    *,
    employee_id: str,
    full_name: str,
    email: str,
    department_code: str,
    date_of_birth: str,
    mobile: str,
    created_by: str,
) -> dict | None:
    """Auto-create an EMPLOYEE user account when a profile is created.

    Returns dict with temp_credentials on success, None if email already taken.
    Temp password is generated randomly and must be changed on first login.
    """
    normalized_email = (email or "").strip().lower()
    if not normalized_email:
        return None

    existing = await repo.find_user_by_email(db, normalized_email)
    if existing:
        return None  # Don't overwrite existing accounts

    # Generate cryptographically random temp password
    temp_password = f"Tmp@{secrets.token_hex(4).upper()}"

    user_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    new_user = {
        "id": user_id,
        "email": normalized_email,
        "password_hash": hash_password(temp_password),
        "name": full_name,
        "authorities": [Authority.EMPLOYEE.value],
        "employee_id": employee_id,
        "department_code": department_code,
        "is_active": True,
        "must_change_password": True,
        "created_at": created_at,
        "created_by": created_by,
        "auto_provisioned": True,
    }
    await repo.insert_user(db, new_user)

    return {
        "user_id": user_id,
        "email": normalized_email,
        "temp_password": temp_password,
        "must_change_password": True,
        "message": "Account auto-created. A temporary password has been generated.",
    }


async def provision_employee_account_for_employee(
    db,
    *,
    employee_id: str,
    email: str,
    current_user: dict,
) -> dict:
    caller_authorities = set(current_user.get("authorities", []))
    allowed_authorities = {
        Authority.SYSTEM_ADMIN.value,
        Authority.GLOBAL_DATA_ENTRY.value,
        Authority.DEALING_ASSISTANT.value,
    }
    if not caller_authorities & allowed_authorities:
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "ACCOUNT_PROVISIONING_FORBIDDEN",
                "message": "Only SYSTEM_ADMIN, GLOBAL_DATA_ENTRY, or DEALING_ASSISTANT can provision employee accounts.",
                "required_authorities": sorted(allowed_authorities),
            },
        )

    identity = await find_identity(
        db,
        employee_id=employee_id,
        projection={"_id": 0},
    )
    if not identity:
        raise HTTPException(status_code=404, detail="Employee identity not found")

    _require_employee_account_ready(identity.get("workflow_status"))

    normalized_email = str(email).strip().lower()
    if not normalized_email:
        raise HTTPException(status_code=400, detail="Email is required")

    existing_by_employee = await repo.find_user_by_employee_id(
        db,
        employee_id=employee_id,
        projection={"_id": 0, "id": 1, "email": 1, "must_change_password": 1},
    )
    if existing_by_employee:
        return {
            "user_id": existing_by_employee.get("id"),
            "email": existing_by_employee.get("email"),
            "employee_id": employee_id,
            "must_change_password": bool(existing_by_employee.get("must_change_password", False)),
            "already_exists": True,
            "linked_existing_user": False,
            "message": "Employee account already exists",
        }

    existing_by_email = await repo.find_user_by_email(db, normalized_email)
    if existing_by_email:
        existing_employee_id = existing_by_email.get("employee_id")
        if existing_employee_id and existing_employee_id != employee_id:
            raise HTTPException(
                status_code=409,
                detail="Email is already linked to a different employee account",
            )

        await repo.update_user(
            db,
            existing_by_email["id"],
            {
                "employee_id": employee_id,
                "name": identity.get("full_name"),
                "department_code": identity.get("current_department_id"),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "updated_by": current_user["sub"],
            },
        )
        return {
            "user_id": existing_by_email.get("id"),
            "email": normalized_email,
            "employee_id": employee_id,
            "must_change_password": bool(existing_by_email.get("must_change_password", False)),
            "already_exists": True,
            "linked_existing_user": True,
            "message": "Existing user linked to employee identity",
        }

    created = await auto_create_employee_account(
        db,
        employee_id=employee_id,
        full_name=identity.get("full_name", ""),
        email=normalized_email,
        department_code=identity.get("current_department_id", ""),
        date_of_birth=str(identity.get("date_of_birth") or ""),
        mobile="",
        created_by=current_user["sub"],
    )
    if not created:
        raise HTTPException(
            status_code=409,
            detail="Account could not be created (email may already be in use).",
        )

    return {
        **created,
        "employee_id": employee_id,
        "already_exists": False,
        "linked_existing_user": False,
        "message": "Employee account provisioned successfully",
    }


async def reset_employee_temp_password(
    db, employee_email: str, *, current_user: dict
) -> dict:
    """Reset an employee's password to a new temp password. Allowed for Data Entry / HOD / SYSTEM_ADMIN."""
    caller_authorities = set(current_user.get("authorities", []))
    allowed = {
        "DEPT_DATA_ENTRY",
        "GLOBAL_DATA_ENTRY",
        "DEALING_ASSISTANT",
        "APPROVING_AUTHORITY",
        "HOD",
        "SYSTEM_ADMIN",
    }
    if not caller_authorities & allowed:
        raise HTTPException(
            status_code=403, detail="Not authorised to reset employee passwords"
        )

    user = await repo.find_user_by_email(db, str(employee_email).strip().lower())
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Only allow resetting EMPLOYEE-only accounts
    if set(user.get("authorities", [])) != {Authority.EMPLOYEE.value}:
        raise HTTPException(
            status_code=400,
            detail="Can only reset passwords for pure EMPLOYEE accounts",
        )

    temp_password = f"Reset@{secrets.token_hex(4).upper()}"
    # Defensive: ensure auto-generated temp password meets complexity rules
    validate_password_strength(temp_password)

    updates = {
        "password_hash": hash_password(temp_password),
        "must_change_password": True,
        "failed_login_attempts": 0,
        "locked_until": None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": current_user["sub"],
    }
    await repo.update_user(db, user["id"], updates)

    # Revoke all existing tokens; the employee must log in again
    await _revoke_all_refresh_tokens(db, user["id"])

    return {
        "message": "Password reset successfully. The user must change their password on next login.",
        "email": employee_email,
        "temp_password": temp_password,
    }


async def delete_user(db, user_id: str, *, current_user: dict) -> dict:
    """Soft-delete: deactivate user to preserve audit trail."""
    require_system_admin(current_user)
    prevent_self_action(current_user, user_id, "delete")

    user = await repo.find_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await repo.update_user(
        db,
        user_id,
        {
            "is_active": False,
            "deactivated_at": datetime.now(timezone.utc).isoformat(),
            "deactivated_by": current_user["sub"],
        },
    )

    # Revoke all refresh tokens; deactivated users must not be able to refresh
    await _revoke_all_refresh_tokens(db, user_id)

    await _log_activity(
        db,
        action="USER_DEACTIVATED",
        current_user=current_user,
        target_user={
            "id": user_id,
            "email": user.get("email"),
            "name": user.get("name"),
        },
        details=None,
    )
    return {"message": "User deactivated successfully"}


from contexts.identity.infrastructure.user_management_authorities import (
    get_authority_holders,
    list_authorities,
)
