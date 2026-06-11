"""Organization Master department read contracts."""

# TODO(context-migration): Move implementation from contexts.department into
# contexts.organization_master once all legacy imports are migrated.
from contexts.department.services.directory_service import (  # noqa: F401
    get_employee_snapshot,
    get_employees,
)
