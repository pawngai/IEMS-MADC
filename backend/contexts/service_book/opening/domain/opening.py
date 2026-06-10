from __future__ import annotations

from typing import Any

from contexts.service_book.opening.domain.opening_status import normalize_status


def normalize_parts(parts: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    source = parts or {}
    return {
        "part_i": dict(source.get("part_i") or {}),
        "part_iia": dict(source.get("part_iia") or {}),
        "part_iib": dict(source.get("part_iib") or {}),
        "part_iii": dict(source.get("part_iii") or {}),
    }


def opening_response(opening: dict | None, *, employee_id: str, identity: dict | None = None) -> dict:
    source = opening or {}
    status = normalize_status(source.get("status") or source.get("workflow_status"))
    return {
        "id": source.get("id") or source.get("opening_id") or f"SBO-{employee_id}",
        "opening_id": source.get("opening_id") or source.get("id") or f"SBO-{employee_id}",
        "employee_id": employee_id,
        "employee_code": source.get("employee_code") or (identity or {}).get("employee_code"),
        "full_name": source.get("full_name") or (identity or {}).get("full_name") or (identity or {}).get("name_in_block_letters"),
        "status": status,
        "workflow_status": status,
        "parts": normalize_parts(source.get("parts")),
        "documents": list(source.get("documents") or []),
        "remarks": source.get("remarks") or "",
        "created_at": source.get("created_at"),
        "updated_at": source.get("updated_at"),
        "submitted_at": source.get("submitted_at"),
        "verified_at": source.get("verified_at"),
        "approved_at": source.get("approved_at"),
    }
