"""Policy decision primitive.

This package now hosts only the technical ``Decision`` value object used by
context-owned policy evaluators. Business-specific facts and rules
(leave eligibility, change-request gating, etc.) live in their owning
bounded context, e.g. ``contexts.leave.domain.leave_request_policy``.
"""

from app_platform.policy_engine.decision import Decision

__all__ = ["Decision"]
