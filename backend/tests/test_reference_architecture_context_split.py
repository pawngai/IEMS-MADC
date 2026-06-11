from __future__ import annotations

from app_platform.domain_separation.context_responsibilities import CONTEXT_RESPONSIBILITIES


EXPECTED_CONTEXT_RESPONSIBILITIES = {
    "employee_identity": "Canonical employee identity (employee code, name, DOB, employment type)",
    "employee_profile": "Profile enrichment and employee read projections",
    "service_book": "Official Service Book opening, records, parts, projection, verification, and printing",
    "leave_attendance": "Leave requests, balances, and policy lifecycle",
    "pay_benefits": "Salary and pay adjustments",
    "workflow": "Approval routing and transition orchestration",
    "change_requests": "Draft/request-before-finalization flows",
    "documents": "Document metadata and entity links",
    "audit": "Business audit trail",
    "identity": "AuthN/AuthZ and principals",
    "notifications": "Outbound notification orchestration",
    "reporting_analytics": "Dashboards and analytical projections",
}


def test_reference_architecture_context_split_is_registered() -> None:
    assert dict(CONTEXT_RESPONSIBILITIES) == EXPECTED_CONTEXT_RESPONSIBILITIES
