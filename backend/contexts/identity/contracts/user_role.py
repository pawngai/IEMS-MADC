"""
Canonical get_user_role() — single source of truth for extracting
the highest-priority authority from a JWT payload dict.
"""

# Ordered from highest to lowest administrative privilege
ROLE_PRIORITY = [
    "SYSTEM_ADMIN",
    "APPROVING_AUTHORITY",
    "HOD",
    "APPOINTING_AUTHORITY",
    "DISCIPLINARY_AUTHORITY",

    "DDO",
    "AUDITOR",
    "NODAL_OFFICER",
    "VERIFIER",
    "SECTION_OFFICER",
    "DEALING_ASSISTANT",
    "DEPT_DATA_ENTRY",
    "GLOBAL_DATA_ENTRY",
    "EMPLOYEE",
]


def get_user_role(current_user: dict) -> str:
    """Extract the highest-priority authority from a JWT user dict.

    Checks ``current_user["authorities"]`` against :data:`ROLE_PRIORITY`
    and returns the first match.  Falls back to the first authority in
    the list, or ``"EMPLOYEE"`` when no authorities are present at all.
    """
    authorities = current_user.get("authorities", [])
    if not authorities:
        return current_user.get("role", "EMPLOYEE")

    active_role = str(current_user.get("active_role") or "").strip().upper()
    if active_role and active_role in authorities:
        return active_role

    for role in ROLE_PRIORITY:
        if role in authorities:
            return role
    return authorities[0]
