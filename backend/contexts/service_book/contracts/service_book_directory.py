"""Service Book read-side contracts for cross-context consumers."""
from __future__ import annotations

from contexts.service_book.read_side.read_model.projectors.part_vi_leave_projection import (
    LeaveLedgerPartVIProjectionSource,
)
from typing import Any

from contexts.service_book.read_side.application.queries.get_service_book import (
    normalize_part_code,
)


_PART_VI_SOURCE = LeaveLedgerPartVIProjectionSource()


def _normalize_iso_date(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


async def get_service_book_part(
    db,
    *,
    employee_id: str,
    part: str,
) -> dict[str, Any] | None:
    part_code = normalize_part_code(part)
    if not part_code:
        return None
    projection = await db.service_book_part_projections.find_one(
        {"employee_id": employee_id, "part_code": part_code},
        {"_id": 0},
    )
    return await _PART_VI_SOURCE.resolve_part(
        db=db,
        existing_projection=projection,
        employee_id=employee_id,
        part_code=part_code,
    )


async def count_service_book_parts(
    db,
    *,
    employee_id: str,
) -> int:
    return int(
        await db.service_book_part_projections.count_documents(
            {"employee_id": employee_id}
        )
    )


async def get_employee_initial_appointment_date(
    db,
    *,
    employee_id: str,
) -> str | None:
    collection = getattr(db, "service_book_part_ii_a", None)
    if collection is None:
        try:
            collection = db["service_book_part_ii_a"]
        except (KeyError, TypeError, AttributeError):
            return None

    record = await collection.find_one(
        {"employee_id": employee_id},
        {"_id": 0, "appointment_date": 1, "entries": 1},
    )
    if not record:
        return None

    candidates: list[str] = []
    top_level = _normalize_iso_date(record.get("appointment_date"))
    if top_level:
        candidates.append(top_level)

    for entry in record.get("entries") or []:
        if str((entry or {}).get("event_type") or "").strip().upper() != "APPOINTMENT":
            continue
        appointment_date = _normalize_iso_date((entry or {}).get("appointment_date"))
        if appointment_date:
            candidates.append(appointment_date)

    return min(candidates) if candidates else None


async def list_servicebook_entries(
    db,
    *,
    employee_id: str,
    part_key: str | None = None,
    active_only: bool = True,
    statuses: list[str] | None = None,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    query: dict[str, Any] = {"employee_id": employee_id}
    if part_key:
        normalized = normalize_part_code(part_key)
        if not normalized:
            return []
        query["part_code"] = normalized
    if statuses:
        query["payload.status"] = {"$in": statuses}
    entries = (
        await db.service_book_entries.find(query, {"_id": 0})
        .sort("created_at", -1)
        .to_list(limit)
    )
    return await _PART_VI_SOURCE.merge_entries(
        db=db,
        entries=entries,
        employee_id=employee_id,
        part_code=normalize_part_code(part_key),
    )


async def list_projected_service_book_entries(
    db,
    *,
    employee_id: str,
    part_code: str | None = None,
    statuses: list[str] | None = None,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    query: dict[str, Any] = {"employee_id": employee_id}
    if part_code:
        query["part_code"] = part_code
    if statuses:
        query["payload.status"] = {"$in": statuses}
    entries = (
        await db.service_book_entries.find(query, {"_id": 0})
        .sort("created_at", -1)
        .to_list(limit)
    )
    return await _PART_VI_SOURCE.merge_entries(
        db=db,
        entries=entries,
        employee_id=employee_id,
        part_code=part_code,
    )


async def get_projected_service_book_part(
    db,
    *,
    employee_id: str,
    part_code: str,
) -> dict[str, Any] | None:
    projection = await db.service_book_part_projections.find_one(
        {"employee_id": employee_id, "part_code": part_code},
        {"_id": 0},
    )
    return await _PART_VI_SOURCE.resolve_part(
        db=db,
        existing_projection=projection,
        employee_id=employee_id,
        part_code=part_code,
    )


async def count_servicebook_entries(
    db,
    *,
    employee_id: str,
    active_only: bool = True,
    statuses: list[str] | None = None,
) -> int:
    query: dict[str, Any] = {"employee_id": employee_id}
    if statuses:
        query["payload.status"] = {"$in": statuses}
    return int(await db.service_book_entries.count_documents(query))


async def count_projected_service_book_entries(
    db,
    *,
    employee_id: str,
    statuses: list[str] | None = None,
) -> int:
    query: dict[str, Any] = {"employee_id": employee_id}
    if statuses:
        query["payload.status"] = {"$in": statuses}
    return int(await db.service_book_entries.count_documents(query))
