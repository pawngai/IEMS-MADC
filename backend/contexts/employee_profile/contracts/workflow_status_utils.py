from __future__ import annotations

from typing import Any


def normalize_workflow_status(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().upper()
    if not normalized:
        return normalized
    return normalized


def workflow_status_filter_values(value: str | None) -> list[str]:
    canonical = normalize_workflow_status(value)
    if not canonical:
        return []
    return [canonical]


def normalize_employee_workflow_status(profile: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(profile or {})
    workflow_status = normalize_workflow_status(normalized.get("workflow_status")) or "DRAFT"
    if workflow_status == "ACTIVE":
        workflow_status = "DRAFT"
    normalized["workflow_status"] = workflow_status
    return normalized
