"""Audit contracts — public API for cross-context consumers."""
from contexts.audit.domain.models import ImmutableAuditLog  # noqa: F401

__all__ = ["ImmutableAuditLog"]