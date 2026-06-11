from __future__ import annotations

import re


COLLECTION_OWNERSHIP: dict[str, str] = {
    r"^employee_master$": "employee_master",
    r"^employee_profiles$": "employee_master",
    r"^employee_identities$": "employee_master",
    r"^counters$": "employee_master",
    r"^designations$": "employee_master",
    r"^employee_profile_extensions$": "employee_master",
    r"^employee_profile_read_models$": "employee_master",
    r"^employee_profiles_deleted$": "employee_master",
    r"^profile_audit_logs_v2$": "employee_master",
    r"^immutability_audit_logs$": "employee_master",
    r"^domain_violation_logs$": "employee_master",
    r"^servicebook_entries$": "service_book",
    r"^servicebook_schema_definitions$": "service_book",
    r"^servicebook_schema_versions$": "service_book",
    r"^service_book_entries$": "service_book",
    r"^service_book_part_projections$": "service_book",
    r"^service_book_projection_status$": "service_book",
    r"^service_book_part_revisions$": "leave",
    r"^service_book_part_(i|ii_a|ii_b|iii|iv|v|vi|vii|viii)$": "service_book",
    r"^servicebook_.*": "service_book",
    r"^service_book_.*": "service_book",
    r"^leave_.*": "leave",
    r"^pay_.*": "pay",
    r"^payroll_.*": "pay",
    r"^change_requests$": "change_requests",
    r"^document_metadata$": "documents",
    r"^document_retention_policies$": "documents",
    r"^document_audit_timeline$": "documents",
    r"^document_templates$": "documents",
    r"^document_signature_requests$": "documents",
    r"^workflow_tasks$": "workflow",
    r"^workflow_transitions$": "workflow",
    r"^department_change_logs$": "system_admin",
    r"^users$": "identity_access",
    r"^refresh_tokens$": "identity_access",
    r"^user_activity_logs$": "identity_access",
    r"^role_change_audit$": "identity_access",
    r"^workflow_config$": "identity_access",
    r"^system_config$": "identity_access",
    r"^notifications$": "notifications",
    r"^notification_.*": "notifications",
    r"^departments$": "department",
    r"^department_establishments$": "department",
    r"^department_establishment_logs$": "department",
    r"^audit_logs$": "audit",
    r"^immutable_audit_logs$": "audit",
    r"^ledger_audit_logs$": "audit",
    r"^seniority_lists$": "seniority",
    r"^master_.*": "masters",
    r"^outbox_events$": "app_platform",
    r"^service_book_records$": "service_book",
    r"^service_book_record_streams$": "service_book",
    r"^service_events$": "service_book",
    r"^service_event_streams$": "service_book",
    r"^service_event_records$": "service_book",
    r"^employee_service_summaries$": "service_book",
}

INFRA_APPEND_ONLY_EXCEPTIONS = {"audit_logs", "immutable_audit_logs", "ledger_audit_logs"}
INFRA_SHARED_EXCEPTIONS = {"outbox_events"}


def owner_for_collection(collection_name: str) -> str | None:
    for pattern, owner in COLLECTION_OWNERSHIP.items():
        if re.match(pattern, collection_name):
            return owner
    return None


def assert_collection_ownership(
    *,
    context: str,
    collection_name: str,
    write: bool,
) -> None:
    owner = owner_for_collection(collection_name)
    if owner is None:
        return

    if collection_name in INFRA_SHARED_EXCEPTIONS:
        return

    if collection_name in INFRA_APPEND_ONLY_EXCEPTIONS and not write:
        return

    if owner != context:
        raise PermissionError(
            f"Collection ownership violation: context={context} collection={collection_name} owner={owner}"
        )
