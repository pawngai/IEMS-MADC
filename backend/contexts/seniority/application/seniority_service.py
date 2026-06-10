"""Seniority Management application service.

Business logic for seniority list generation via three-collection lookup:
  1. employee_identities      – canonical identity (employee_identity context)
  2. employee_profile_extensions – service, group/cadre (employee_profile context)
  3. service_book_part_ii_a   – appointment / promotion events (service_book context)

All three are **read-only** cross-context queries at generation time.
Seniority owns only the ``seniority_lists`` collection (snapshot + rank state).
"""

from __future__ import annotations

from typing import Any, Optional


# ── Reference-data lookups (cross-context reads) ─────────────────────


async def list_services(db) -> list[str]:
    """Distinct service values from employee_profile_extensions (employee_profile context)."""
    values = await db["employee_profile_extensions"].distinct("service")
    return sorted([v for v in values if v])


async def list_designation_codes(db) -> list[str]:
    """Distinct designation codes from employee_identities (employee_identity context)."""
    values = await db["employee_identities"].distinct("current_designation_id")
    return sorted([v for v in values if v])


# ── Seniority list generation ────────────────────────────────────────


async def gather_employees(
    db,
    service: str,
    designation_code: Optional[str] = None,
) -> list[dict]:
    """Three-collection lookup: identities + profile extensions + service book."""

    # 1. Identities matching designation & active status
    id_filter: dict[str, Any] = {
        "employee_status": "ACTIVE",
    }
    if designation_code:
        id_filter["current_designation_id"] = designation_code
    id_cursor = db["employee_identities"].find(id_filter, {
        "_id": 0,
        "employee_id": 1,
        "employee_code": 1,
        "full_name": 1,
        "gender": 1,
        "employment_type": 1,
        "date_of_initial_engagement": 1,
        "current_department_id": 1,
        "current_designation_id": 1,
    })
    identities = {doc["employee_id"]: doc async for doc in id_cursor}
    if not identities:
        return []

    emp_ids = list(identities.keys())

    # 2. Profile extensions – filter by service
    ext_cursor = db["employee_profile_extensions"].find(
        {"employee_id": {"$in": emp_ids}, "service": service},
        {"_id": 0, "employee_id": 1, "service": 1, "group": 1, "mode_of_recruitment": 1},
    )
    extensions: dict[str, dict] = {}
    async for doc in ext_cursor:
        extensions[doc["employee_id"]] = doc

    # Only keep employees that match both identity AND extension service
    matched_ids = [eid for eid in emp_ids if eid in extensions]
    if not matched_ids:
        return []

    # 3. Service book Part II-A – latest appointment / promotion per employee
    sb_cursor = db["service_book_part_ii_a"].find(
        {"employee_id": {"$in": matched_ids}},
        {
            "_id": 0,
            "employee_id": 1,
            "entries": 1,
            "appointment_date": 1,
            "confirmation_date": 1,
        },
    )
    sb_data: dict[str, dict] = {}
    async for doc in sb_cursor:
        eid = doc["employee_id"]
        sb_info: dict[str, Any] = {}
        if doc.get("appointment_date"):
            sb_info["appointment_date"] = doc["appointment_date"]
        if doc.get("confirmation_date"):
            sb_info["confirmation_date"] = doc["confirmation_date"]
        entries = doc.get("entries") or []
        for entry in entries:
            etype = (entry.get("event_type") or "").upper()
            if etype == "PROMOTION" and entry.get("promotion_date"):
                existing = sb_info.get("last_promotion_date", "")
                if entry["promotion_date"] > existing:
                    sb_info["last_promotion_date"] = entry["promotion_date"]
            if etype == "APPOINTMENT" and entry.get("appointment_date"):
                if not sb_info.get("appointment_date"):
                    sb_info["appointment_date"] = entry["appointment_date"]
        sb_data[eid] = sb_info

    # Merge & sort by date_of_initial_engagement ascending (most senior first)
    merged: list[dict] = []
    for eid in matched_ids:
        identity = identities[eid]
        ext = extensions.get(eid, {})
        sb = sb_data.get(eid, {})
        merged.append({
            "employee_id": eid,
            "employee_code": identity.get("employee_code"),
            "full_name": identity.get("full_name"),
            "gender": identity.get("gender"),
            "employment_type": identity.get("employment_type"),
            "department_code": identity.get("current_department_id"),
            "designation_code": identity.get("current_designation_id"),
            "date_of_initial_engagement": identity.get("date_of_initial_engagement", ""),
            "service": ext.get("service"),
            "group": ext.get("group"),
            "mode_of_recruitment": ext.get("mode_of_recruitment"),
            "appointment_date": sb.get("appointment_date"),
            "confirmation_date": sb.get("confirmation_date"),
            "last_promotion_date": sb.get("last_promotion_date"),
        })

    merged.sort(key=lambda r: r.get("date_of_initial_engagement") or "9999-12-31")
    for idx, row in enumerate(merged, start=1):
        row["rank"] = idx

    return merged
