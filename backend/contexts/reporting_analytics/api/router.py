"""Canonical Reporting Analytics API router.

TODO(context-migration): Move route implementation from contexts.reporting into
contexts.reporting_analytics once all legacy imports are migrated.
"""

from contexts.reporting.api.router import reporting_router  # noqa: F401
