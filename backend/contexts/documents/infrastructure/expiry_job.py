"""Document expiry sweep.

For each document with ``expires_at`` set, emit:

* ``DocumentExpiringSoon`` at the T-30 / T-7 / T-1 day boundaries — each
  stage fires at most once per document (tracked via
  ``expiry_notified_stages``)
* ``DocumentExpired`` once the expiry has passed (also one-shot)

The job does NOT delete or archive expired documents — that is retention's
job. ``expires_at`` is informational and feeds notifications + UI badges.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app_platform.event_bus.types import EventName
from contexts.documents.infrastructure.event_publish import publish_document_event
from contexts.documents.infrastructure.metadata_ops import (
    metadata_repository,
    write_document_metadata,
)


_NOTIFY_STAGES: tuple[tuple[str, int], ...] = (
    ("T-30", 30),
    ("T-7", 7),
    ("T-1", 1),
)
_EXPIRED_STAGE = "EXPIRED"


async def run_once(*, db, now: datetime | None = None) -> dict[str, int]:
    """Returns ``{"expiring_soon": int, "expired": int}``."""
    if db is None:
        return {"expiring_soon": 0, "expired": 0}

    when = now or datetime.now(timezone.utc)
    summary = {"expiring_soon": 0, "expired": 0}

    from contexts.documents.repository.metadata_repository import COLLECTION

    await metadata_repository(db=db).ensure_indexes()
    cursor = db[COLLECTION].find(
        {"expires_at": {"$exists": True, "$type": "string"}},
        {"_id": 0},
    )
    async for row in cursor:
        if not isinstance(row, dict):
            continue
        filename = str(row.get("filename") or "").strip()
        expires_at = _parse_iso(row.get("expires_at"))
        if not filename or expires_at is None:
            continue

        notified = set(row.get("expiry_notified_stages") or [])
        if expires_at <= when:
            if _EXPIRED_STAGE in notified:
                continue
            await _emit_expired(filename, row, expired_at=when, db=db)
            notified.add(_EXPIRED_STAGE)
            row["expiry_notified_stages"] = sorted(notified)
            await write_document_metadata(filename, row, db=db)
            summary["expired"] += 1
            continue

        delta_days = (expires_at - when).days
        for stage, days in _NOTIFY_STAGES:
            if delta_days < days and stage not in notified:
                await _emit_expiring(
                    filename,
                    row,
                    stage=stage,
                    days_until_expiry=delta_days,
                    db=db,
                )
                notified.add(stage)
                row["expiry_notified_stages"] = sorted(notified)
                await write_document_metadata(filename, row, db=db)
                summary["expiring_soon"] += 1
                # Don't fire multiple stages in one sweep — let the next run
                # pick up the next stage. Keeps notifications human-readable.
                break

    return summary


async def _emit_expiring(
    filename: str,
    metadata: dict[str, Any],
    *,
    stage: str,
    days_until_expiry: int,
    db,
) -> None:
    await publish_document_event(
        name=EventName.DOCUMENT_EXPIRING_SOON.value,
        payload={
            "event_version": 1,
            "document_id": str(metadata.get("document_id") or filename),
            "filename": filename,
            "expires_at": str(metadata.get("expires_at") or ""),
            "days_until_expiry": int(days_until_expiry),
            "stage": stage,
            "uploaded_employee_id": metadata.get("uploaded_employee_id"),
            "subject_employee_id": metadata.get("subject_employee_id"),
            "document_type": metadata.get("document_type"),
        },
        db=db,
    )


async def _emit_expired(
    filename: str,
    metadata: dict[str, Any],
    *,
    expired_at: datetime,
    db,
) -> None:
    await publish_document_event(
        name=EventName.DOCUMENT_EXPIRED.value,
        payload={
            "event_version": 1,
            "document_id": str(metadata.get("document_id") or filename),
            "filename": filename,
            "expires_at": str(metadata.get("expires_at") or ""),
            "expired_at": expired_at.isoformat(),
            "uploaded_employee_id": metadata.get("uploaded_employee_id"),
            "subject_employee_id": metadata.get("subject_employee_id"),
            "document_type": metadata.get("document_type"),
        },
        db=db,
    )


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
