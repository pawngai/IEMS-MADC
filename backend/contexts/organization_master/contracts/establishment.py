"""Organization Master establishment contracts."""

# TODO(context-migration): Move implementation from contexts.department into
# contexts.organization_master once all legacy imports are migrated.
from contexts.department.services.sanctioned_strength_service import (  # noqa: F401
    build_sanctioned_strength_summary,
    get_sanctioned_strength,
    get_sanctioned_strength_for_department_admin,
    update_sanctioned_strength,
    update_sanctioned_strength_for_department_admin,
)
