"""Leave Attendance read contracts."""

# TODO(context-migration): Move implementation from contexts.leave into
# contexts.leave_attendance once all legacy imports are migrated.
from contexts.leave.contracts.leave_directory import *  # noqa: F401,F403
