"""Documents domain — retention policy rules.

A retention policy specifies, for a slice of documents (matched by
``document_type``, ``category``, or ``source_context``), how long they remain
in the primary bucket before archival and how long they stay archived before
permanent deletion. Documents under legal hold are immune from both
archival-driven deletion *and* archival-driven movement — they stay in their
current bucket until the hold is released.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


# Sentinel meaning "policy applies to this dimension regardless of value".
ANY = "*"


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    key: str
    document_type: str = ANY
    category: str = ANY
    source_context: str = ANY
    archive_after_days: int | None = None
    delete_after_archive_days: int | None = None
    requires_legal_hold_release: bool = False

    def matches(self, metadata: dict[str, Any] | None) -> bool:
        data = metadata or {}
        return (
            _value_matches(self.document_type, data.get("document_type"))
            and _value_matches(self.category, data.get("category"))
            and _value_matches(self.source_context, data.get("source_context"))
        )


def _value_matches(policy_value: str, metadata_value: Any) -> bool:
    if policy_value == ANY:
        return True
    return str(metadata_value or "").strip().upper() == str(policy_value or "").strip().upper()


def select_policy(
    metadata: dict[str, Any] | None,
    policies: list[RetentionPolicy],
) -> RetentionPolicy | None:
    """Return the highest-specificity matching policy. Specificity is the
    count of non-``ANY`` dimensions. Ties are broken by list order."""
    matches = [p for p in policies if p.matches(metadata)]
    if not matches:
        return None
    matches.sort(key=lambda p: _specificity(p), reverse=True)
    return matches[0]


def _specificity(policy: RetentionPolicy) -> int:
    return sum(
        1
        for field in (policy.document_type, policy.category, policy.source_context)
        if field != ANY
    )


def is_eligible_for_archive(
    metadata: dict[str, Any] | None,
    policy: RetentionPolicy,
    *,
    now: datetime | None = None,
) -> bool:
    """A document is eligible for archive once ``archive_after_days`` have
    elapsed since ``uploaded_at`` AND there is no active legal hold. Already
    archived or never-uploaded rows are ineligible."""
    data = metadata or {}
    if data.get("legal_hold"):
        return False
    if data.get("archived_at"):
        return False
    if policy.archive_after_days is None:
        return False

    uploaded_at = _parse_iso(data.get("uploaded_at"))
    if uploaded_at is None:
        return False
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=policy.archive_after_days)
    return uploaded_at <= cutoff


def is_eligible_for_delete(
    metadata: dict[str, Any] | None,
    policy: RetentionPolicy,
    *,
    now: datetime | None = None,
) -> bool:
    """An archived document is eligible for permanent deletion once
    ``delete_after_archive_days`` have elapsed since ``archived_at`` and no
    legal hold has been applied in the meantime."""
    data = metadata or {}
    if data.get("legal_hold"):
        return False
    if policy.delete_after_archive_days is None:
        return False
    archived_at = _parse_iso(data.get("archived_at"))
    if archived_at is None:
        return False
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=policy.delete_after_archive_days)
    return archived_at <= cutoff


def _parse_iso(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed
