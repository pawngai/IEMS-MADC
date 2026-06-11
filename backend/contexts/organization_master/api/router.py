"""Canonical Organization Master department portal API router.

TODO(context-migration): Move route implementation from contexts.department into
contexts.organization_master once all legacy imports are migrated.
"""

from contexts.department.api.router import department_portal_router  # noqa: F401
