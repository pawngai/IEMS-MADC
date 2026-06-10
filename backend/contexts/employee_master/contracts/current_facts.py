"""Canonical Employee Master reads for current employee facts."""

from contexts.employee_master.identity.contracts.identity_directory import (  # noqa: F401
    count_identities,
    find_identities_by_ids,
    find_identity,
    get_employee_department_code,
    get_employee_ids_for_department,
    get_employee_name_map,
    get_identity_bootstrap,
    list_identities,
    resolve_identity_ref,
)
from contexts.employee_master.profile.contracts.profile_directory import (  # noqa: F401
    count_profiles,
    count_profiles_by_department,
    find_profile,
    find_profile_view,
    list_profile_assignment_fields,
    list_profile_workflow_statuses,
    list_profiles,
    list_profiles_by_department,
    require_profile_view,
)

__all__ = [
    "count_identities",
    "count_profiles",
    "count_profiles_by_department",
    "find_identities_by_ids",
    "find_identity",
    "find_profile",
    "find_profile_view",
    "get_employee_department_code",
    "get_employee_ids_for_department",
    "get_employee_name_map",
    "get_identity_bootstrap",
    "list_identities",
    "list_profile_assignment_fields",
    "list_profile_workflow_statuses",
    "list_profiles",
    "list_profiles_by_department",
    "require_profile_view",
    "resolve_identity_ref",
]

