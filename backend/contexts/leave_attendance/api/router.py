"""Canonical Leave Attendance API router.

TODO(context-migration): Move route implementation from contexts.leave into
contexts.leave_attendance once all legacy imports are migrated.
"""

from contexts.leave.api.router import leave_router  # noqa: F401
