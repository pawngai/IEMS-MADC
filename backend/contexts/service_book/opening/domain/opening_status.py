from __future__ import annotations


OPENING_STATUSES = {"NOT_STARTED", "DRAFT", "SUBMITTED", "VERIFIED", "APPROVED", "LOCKED", "REJECTED"}
EDITABLE_STATUSES = {"NOT_STARTED", "DRAFT", "REJECTED"}


def normalize_status(status: str | None) -> str:
    normalized = str(status or "").strip().upper()
    if normalized in {"OPENED", "ATTESTED"}:
        return "LOCKED"
    if normalized in OPENING_STATUSES:
        return normalized
    return "NOT_STARTED"
