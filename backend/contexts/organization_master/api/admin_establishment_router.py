"""Canonical Organization Master admin establishment API router.

TODO(context-migration): Move route implementation from contexts.department into
contexts.organization_master once all legacy imports are migrated.
"""

from contexts.department.api.admin_establishment_router import (  # noqa: F401
    department_admin_establishment_router,
)
