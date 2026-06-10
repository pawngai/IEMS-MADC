from __future__ import annotations


class DomainError(Exception):
    """Base error for domain/application level failures."""


class PolicyDeniedError(DomainError):
    """Raised when policy enforcement denies an action."""
