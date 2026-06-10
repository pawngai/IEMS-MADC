"""Employee identity normalization domain service.

Pure functions for normalizing employee identity records: employment type
resolution, workflow status canonicalization, and service status unification.
"""

from __future__ import annotations

from typing import Any

from app_platform.reference_data.contracts.employment_rules import (
    check_employment_type_allows_service_book,
)
from contexts.employee_master.identity.domain.employment_rules import (
    determine_employment_type,
)
from contexts.employee_master.identity.contracts.workflow_status_utils import normalize_workflow_status


def determineEmploymentType(employee_or_type: Any) -> str | None:
    return determine_employment_type(employee_or_type)


def isServiceBookEligible(employee_or_type: Any) -> bool:
    employment_type = determineEmploymentType(employee_or_type)
    return check_employment_type_allows_service_book(employment_type or "")


def normalizeEmployeeRecord(employee_record: dict[str, Any] | None) -> dict[str, Any]:
    normalized = dict(employee_record or {})

    employment_type = determineEmploymentType(normalized)
    if employment_type:
        normalized["employment_type"] = employment_type

    normalized["workflow_status"] = (
        normalize_workflow_status(normalized.get("workflow_status")) or "DRAFT"
    )

    service_status = (
        normalized.get("service_status")
        or normalized.get("employee_status")
        or "ACTIVE"
    )
    normalized_status = str(service_status).strip().upper() or "ACTIVE"
    normalized["service_status"] = normalized_status
    normalized["employee_status"] = normalized_status

    return normalized


def updateEmployeeStatus(
    employee_record: dict[str, Any] | None,
    *,
    workflow_status: str | None = None,
    service_status: str | None = None,
) -> dict[str, Any]:
    updated = normalizeEmployeeRecord(employee_record)

    if workflow_status is not None:
        updated["workflow_status"] = (
            normalize_workflow_status(workflow_status) or updated.get("workflow_status") or "DRAFT"
        )

    if service_status is not None:
        normalized_status = str(service_status).strip().upper() or "ACTIVE"
        updated["service_status"] = normalized_status
        updated["employee_status"] = normalized_status

    return updated