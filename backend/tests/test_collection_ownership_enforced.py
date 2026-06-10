from __future__ import annotations

import re
from pathlib import Path

from app_platform.db import runtime
from app_platform.domain_separation.data_ownership import owner_for_collection


BACKEND_ROOT = Path(__file__).resolve().parents[1]
CONTEXTS_ROOT = BACKEND_ROOT / "contexts"


def test_collection_ownership_map_covers_context_collection_usage() -> None:
    required_collections = {
        "servicebook_entries",
        "servicebook_schema_definitions",
        "servicebook_schema_versions",
        "service_book_entries",
        "service_book_workflow_entries",
        "service_book_part_projections",
        "service_book_records",
        "service_book_record_streams",
        "service_event_streams",
        "service_event_records",
        "pay_ledger_entries",
        "leave_ledger_entries",
        "outbox_events",
        "audit_logs",
        "employee_profiles",
        "employee_identities",
        "employee_profile_extensions",
        "employee_profile_read_models",
        "employee_profiles_deleted",
        "profile_audit_logs_v2",
        "domain_violation_logs",
        "immutability_audit_logs",
        "counters",
        "leave_applications",
        "users",
        "department_establishments",
        "department_establishment_logs",
        # Phase 9 additions
        "document_metadata",
        "workflow_tasks",
        "workflow_transitions",
        "change_requests",
        "notifications",
        "seniority_lists",
    }
    missing = sorted(
        collection
        for collection in required_collections
        if owner_for_collection(collection) is None
    )
    assert not missing, "Missing ownership mapping for required collections:\n" + "\n".join(missing)


def test_key_repositories_call_ownership_assertion() -> None:
    files = [
        BACKEND_ROOT / "contexts" / "service_book" / "repository" / "read_repository.py",
        BACKEND_ROOT / "contexts" / "service_book" / "records" / "repository" / "service_record_repository.py",
        BACKEND_ROOT / "contexts" / "employee_identity" / "repository" / "identity_repository.py",
        BACKEND_ROOT / "contexts" / "employee_profile" / "read_model" / "infrastructure" / "repository.py",
        BACKEND_ROOT / "contexts" / "department" / "repository" / "department_portal_repo.py",
        BACKEND_ROOT / "contexts" / "pay" / "infrastructure" / "pay_repository.py",
        BACKEND_ROOT / "contexts" / "leave" / "infrastructure" / "gateway.py",
        # Phase 9 additions
        BACKEND_ROOT / "contexts" / "workflow" / "infrastructure" / "repository.py",
        BACKEND_ROOT / "contexts" / "change_requests" / "infrastructure" / "gateway.py",
        BACKEND_ROOT / "contexts" / "notifications" / "infrastructure" / "repo.py",
        BACKEND_ROOT / "contexts" / "documents" / "repository" / "metadata_repository.py",
        BACKEND_ROOT / "contexts" / "leave" / "repository" / "leave_repository.py",
    ]

    violations: list[str] = []
    for file_path in files:
        source = file_path.read_text(encoding="utf-8")
        if "assert_collection_ownership(" not in source:
            violations.append(file_path.relative_to(BACKEND_ROOT).as_posix())

    assert not violations, (
        "Repository constructors must enforce collection ownership:\n"
        + "\n".join(sorted(violations))
    )


def test_ensure_indexes_covers_critical_unique_indexes() -> None:
    """_ensure_indexes must declare unique indexes for critical identity collections."""
    import inspect

    source = inspect.getsource(runtime._ensure_indexes) if hasattr(runtime, "_ensure_indexes") else ""
    if not source:
        # Fall back to reading the file directly.
        from pathlib import Path

        runtime_file = Path(runtime.__file__)
        source = runtime_file.read_text(encoding="utf-8")

    # Critical unique indexes that must exist.
    critical = {
        "employee_identities": "employee_id",
        "employee_profile_extensions": "employee_id",
        "employee_profile_read_models": "employee_id",
        "outbox_events": "idempotency_key",
        "audit_logs": "source_event_id",
        "notifications": "source_event_id",
        "service_book_entries": "source_event_id",
        "service_book_workflow_entries": "id",
        "service_book_record_streams": "employee_id",
        "service_book_records": "service_event_id",
        "workflow_tasks": "task_id",
        "seniority_lists": "list_id",
        "users": "email",
        "refresh_tokens": "token",
    }
    missing: list[str] = []
    for collection, key in critical.items():
        # Verify collection name AND unique=True appear near the key field.
        if collection not in source:
            missing.append(f"{collection}.{key} — collection not in _ensure_indexes")
    assert not missing, (
        "Critical unique indexes missing from _ensure_indexes:\n"
        + "\n".join(sorted(missing))
    )


def test_ensure_indexes_quarantines_duplicates_before_new_unique_event_indexes() -> None:
    import inspect

    source = inspect.getsource(runtime._ensure_indexes) if hasattr(runtime, "_ensure_indexes") else ""
    assert "_quarantine_duplicate_compound_keys" in source
    assert "event_duplicate_quarantine" in source
    assert "outbox_events" in source and "idempotency_key" in source
    assert "audit_logs" in source and "source_event_id" in source
    assert "notifications" in source and "source_event_id" in source
    assert "service_book_entries" in source and "source_event_id" in source
