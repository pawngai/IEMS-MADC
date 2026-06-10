"""Audit which DB collections are still referenced in the live backend code.

Excludes one-off migration scripts under backend/scripts/mongodb/ so that
historical migrations don't keep dead collections alive.
"""

from __future__ import annotations

import pathlib
import re


COLLECTIONS = """audit_logs caste_categories change_requests counters department_change_logs
department_establishment_logs department_establishments department_portal_activity_feed
department_portal_employee_index departments designations document_metadata document_types
employee_identities employee_identity_activation_backup_20260430084017
employee_profile_extensions employee_profile_read_models employee_profiles
employee_profiles_deleted employment_types ess_employee_snapshot ess_servicebook_view
event_duplicate_quarantine identity_user_employee_link_view leave_accounts
leave_applications leave_balances leave_ledger_entries leave_types master_audit_logs
notifications offices outbox_events pay_levels profile_audit_logs_v2 qualifications
refresh_tokens role_change_audit roles schema_migrations seniority_lists
service_book_entries service_book_part_i service_book_part_ii_a service_book_part_ii_b
service_book_part_iii service_book_part_iv service_book_part_projections
service_book_part_revisions service_book_part_v service_book_part_vi
service_book_part_vii service_book_part_viii service_book_projection_metadata
service_book_projection_status service_book_record_streams service_book_records
service_book_workflow_entries service_event_records service_event_streams
service_event_types service_events service_groups servicebook_employee_scope_view
servicebook_entries servicebook_part_views servicebook_projection_events
servicebook_schema_definitions servicebook_schema_versions services
user_activity_logs users workflow_approvals workflow_cases workflow_config
workflow_history workflow_instances workflow_stages workflow_steps workflow_tasks
workflow_transitions""".split()


def main() -> None:
    backend = pathlib.Path("backend")
    found: dict[str, list[str]] = {c: [] for c in COLLECTIONS}

    for path in backend.rglob("*.py"):
        parts = path.parts
        if "__pycache__" in parts or ".venv" in parts:
            continue
        posix = path.as_posix()
        if "scripts/mongodb" in posix:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for collection in COLLECTIONS:
            if re.search(rf"\b{re.escape(collection)}\b", text):
                found[collection].append(posix)

    print("=== UNREFERENCED in live backend (excluding scripts/mongodb) ===")
    for collection in COLLECTIONS:
        if not found[collection]:
            print("  ", collection)
    print()
    print("=== REFERENCED ===")
    for collection in COLLECTIONS:
        if found[collection]:
            print(f"  {collection:55s} refs={len(found[collection]):3d}")


if __name__ == "__main__":
    main()
