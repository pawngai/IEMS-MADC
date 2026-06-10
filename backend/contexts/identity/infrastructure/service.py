from __future__ import annotations

from contexts.rbac.domain.models import AUTHORITY_PERMISSIONS, WORKFLOW_TRANSITIONS, Authority, Permission, WorkflowStage
from contexts.rbac.domain.models import UserResponse as AuthUserResponse
from contexts.rbac.application.access_control import get_permissions as _get_perms

from contexts.identity.infrastructure import repo
from contexts.identity.infrastructure import auth_session_service as _auth
from contexts.identity.infrastructure import user_management_service as _users
from contexts.identity.infrastructure import activity_service as _activity


# Re-export auth/session concerns.
validate_password_strength = _auth.validate_password_strength
hash_password = _auth.hash_password
verify_password = _auth.verify_password
get_permissions_for_authorities = _auth.get_permissions_for_authorities
create_token = _auth.create_token
login = _auth.login
refresh_access_token = _auth.refresh_access_token
logout = _auth.logout

# Re-export user lifecycle/admin concerns.
list_users = _users.list_users
get_user_count = _users.get_user_count
list_employee_directory = _users.list_employee_directory
get_employee_directory_count = _users.get_employee_directory_count
get_user = _users.get_user
create_user = _users.create_user
update_user = _users.update_user
patch_user_authorities = _users.patch_user_authorities
update_user_password = _users.update_user_password
change_own_password = _users.change_own_password
auto_create_employee_account = _users.auto_create_employee_account
provision_employee_account_for_employee = _users.provision_employee_account_for_employee
reset_employee_temp_password = _users.reset_employee_temp_password
delete_user = _users.delete_user
list_authorities = _users.list_authorities
get_authority_holders = _users.get_authority_holders

# Re-export activity/analytics concerns.
list_activity_logs = _activity.list_activity_logs
get_activity_stats = _activity.get_activity_stats
get_role_change_history = _activity.get_role_change_history
get_role_change_stats = _activity.get_role_change_stats


async def me_from_token(db_optional, current_user: dict) -> AuthUserResponse:
    """Return principal details, preferring live DB authorities over JWT snapshot."""
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
                department_code=user.get("department_code", current_user.get("department_code")),
            )

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
    return await _auth.get_module_access(db_optional, current_user)


def get_rbac_matrix() -> dict:
    matrix: dict[str, list[str]] = {}
    for authority in Authority:
        if authority in AUTHORITY_PERMISSIONS:
            matrix[authority.value] = [p.value for p in AUTHORITY_PERMISSIONS[authority]]

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
                    else (trans["required_authority"].value if trans["required_authority"] else None)
                ),
                "can_edit": trans["can_edit"],
            }
            for stage, trans in WORKFLOW_TRANSITIONS.items()
        },
    }
