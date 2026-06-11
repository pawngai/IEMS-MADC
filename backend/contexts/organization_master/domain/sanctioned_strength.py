from __future__ import annotations

from typing import Any

from fastapi import HTTPException


def normalize_sanctioned_strength_rows(
    rows: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str | None]] = set()
    employment_types_by_designation: dict[str, set[str | None]] = {}

    for index, raw_row in enumerate(rows or []):
        designation_code = str(raw_row.get("designation_code") or "").strip().upper()
        if not designation_code:
            raise HTTPException(
                status_code=400,
                detail=f"sanctioned_strength[{index}].designation_code is required.",
            )

        employment_type = str(raw_row.get("employment_type") or "").strip().upper() or None

        try:
            sanctioned_count = int(raw_row.get("sanctioned_count", 0))
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"sanctioned_strength[{index}].sanctioned_count must be an integer."
                ),
            ) from exc

        if sanctioned_count < 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"sanctioned_strength[{index}].sanctioned_count cannot be negative."
                ),
            )

        key = (designation_code, employment_type)
        if key in seen_keys:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Duplicate sanctioned strength rows are not allowed for the same "
                    "designation and employment type."
                ),
            )
        seen_keys.add(key)

        employment_types = employment_types_by_designation.setdefault(designation_code, set())
        employment_types.add(employment_type)

        normalized.append(
            {
                "designation_code": designation_code,
                "employment_type": employment_type,
                "sanctioned_count": sanctioned_count,
                "order_number": str(raw_row.get("order_number") or "").strip() or None,
                "order_date": str(raw_row.get("order_date") or "").strip() or None,
                "remarks": str(raw_row.get("remarks") or "").strip() or None,
            }
        )

    for designation_code, employment_types in employment_types_by_designation.items():
        if None in employment_types and len(employment_types) > 1:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Sanctioned strength cannot mix department-wide and employment-type-specific "
                    f"rows for designation '{designation_code}'."
                ),
            )

    return sorted(
        normalized,
        key=lambda row: (row["designation_code"], row.get("employment_type") or ""),
    )