from __future__ import annotations

from types import MappingProxyType


CONTEXT_RESPONSIBILITIES = MappingProxyType(
    {
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
)


def get_context_responsibility(context_name: str) -> str | None:
    return CONTEXT_RESPONSIBILITIES.get(context_name)
