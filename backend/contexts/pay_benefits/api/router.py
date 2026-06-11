"""Canonical Pay Benefits API router.

TODO(context-migration): Move route implementation from contexts.pay into
contexts.pay_benefits once all legacy imports are migrated.
"""

from contexts.pay.api.router import pay_router  # noqa: F401
