from __future__ import annotations

from typing import Any

from fastapi import HTTPException


def apply_rank_overrides(*, employees: list[dict[str, Any]], overrides) -> list[dict[str, Any]]:
    employee_map = {str(employee["employee_id"]): dict(employee) for employee in employees}
    for override in overrides:
        employee_id = str(override.employee_id)
        if employee_id not in employee_map:
            raise HTTPException(400, f"Employee {employee_id} not in this list")
        employee_map[employee_id]["rank"] = int(override.new_rank)

    updated_rows = list(employee_map.values())
    expected_ranks = list(range(1, len(updated_rows) + 1))
    actual_ranks = sorted(int(row.get("rank") or 0) for row in updated_rows)
    if actual_ranks != expected_ranks:
        raise HTTPException(
            400,
            f"Ranks must be unique whole numbers from 1 to {len(updated_rows)}",
        )

    updated_rows.sort(key=lambda row: (int(row["rank"]), str(row.get("employee_id") or "")))
    return updated_rows
