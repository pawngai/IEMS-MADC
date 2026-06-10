"""
Cross-context MongoDB collection isolation.

Enforces the ARCHITECTURE_RULES constraint: "No cross-context DB writes."
Each bounded context must only access collections it owns. Cross-context
data must flow through contracts / service facades, never via direct
collection access.

This test statically scans Python source under backend/contexts/ for
db.<collection> and db["<collection>"] patterns and flags any context
that touches collections belonging to another context.
"""
from __future__ import annotations

import re
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
CONTEXTS_ROOT = BACKEND_ROOT / "contexts"

# ── Collection ownership map ──────────────────────────────────────────
# Maps collection name → owning context directory name.
COLLECTION_OWNER: dict[str, str] = {
    # identity
    "users": "identity",
    "refresh_tokens": "identity",
    "user_activity_logs": "identity",
    "role_change_audit": "identity",
    "system_config": "identity",
    # employee identity/profile
    "employee_profiles": "employee_master",
    "employee_identities": "employee_master",
    "employee_profile_extensions": "employee_master",
    "employee_profile_read_models": "employee_master",
    "employee_profiles_deleted": "employee_master",
    "profile_audit_logs_v2": "employee_master",
    "immutability_audit_logs": "employee_master",
    "domain_violation_logs": "employee_master",
    "designations": "employee_master",
    "counters": "employee_master",
    # leave
    "leave_applications": "leave",
    "leave_types": "leave",
    "leave_ledger_entries": "leave",
    # notifications
    "notifications": "notifications",
    # audit
    "audit_logs": "audit",
    "ledger_audit_logs": "audit",
    "immutable_audit_logs": "audit",
    # workflow
    "workflow_tasks": "workflow",
    "workflow_transitions": "workflow",
    # change_requests
    "change_requests": "change_requests",
    # documents
    "document_metadata": "documents",
    # system_admin / department
    "departments": "system_admin",
    "department_change_logs": "system_admin",
    "department_establishments": "department",
    "department_establishment_logs": "department",
    # pay
    "pay_ledger_entries": "pay",
    # service_book records, with legacy collections retained during migration.
    "service_events": "service_book",
    "service_event_streams": "service_book",
    "service_event_records": "service_book",
    "service_book_record_streams": "service_book",
    "service_book_records": "service_book",
    # seniority
    "seniority_lists": "seniority",
    # service_book read / legacy collections
    "servicebook_entries": "service_book",
    "servicebook_schema_definitions": "service_book",
    "servicebook_schema_versions": "service_book",
    "service_book_part_i": "service_book",
    "service_book_part_ii_a": "service_book",
    "service_book_part_ii_b": "service_book",
    "service_book_part_iii": "service_book",
    "service_book_part_iv": "service_book",
    "service_book_part_v": "service_book",
    "service_book_part_vi": "service_book",
    "service_book_part_vii": "service_book",
    "service_book_part_viii": "service_book",
    "service_book_entries": "service_book",
    "service_book_part_projections": "service_book",
    "service_book_part_revisions": "leave",
}

# Contexts that are thin compatibility shims or sub-contexts of a parent.
# These are allowed to access the parent context's collections.
CONTEXT_ALIASES: dict[str, str] = {
    "read_model": "employee_master",
}

# ── Transitional allowlist ────────────────────────────────────────────
# File (relative to backend/) → set of foreign collections allowed.
# Each entry must have a tracking comment. Shrink this list over time.
ALLOWED_CROSS_COLLECTION_ACCESS: dict[str, set[str]] = {
    # employee_master now owns the identity + profile collections, so the former
    # cross-context reads between identity and profile are same-context. The only
    # remaining foreign read is the profile gateway joining `users` (owned by
    # identity) for login-account status. COMPAT: removable when that join moves
    # behind the identity_access contract.
    "contexts/employee_master/profile/infrastructure/gateway.py": {
        "users",
    },
    # Seniority uses cross-context reads for three-collection join at generation
    # time and for reference-data dropdowns.  All reads go through the application
    # service; the router itself no longer touches foreign collections.
    "contexts/seniority/application/seniority_service.py": {
        "employee_identities",
        "employee_profile_extensions",
        "service_book_part_ii_a",
    },
    # Reporting is a read-only analytics projection consumer.
    "contexts/reporting/queries/analytics_queries.py": {
        "service_book_records",
        "service_event_records",
    },
}


def _resolve_context(parts: tuple[str, ...]) -> str | None:
    """Return the effective owning context for a file path."""
    if len(parts) < 2:
        return None
    ctx = parts[1]
    return CONTEXT_ALIASES.get(ctx, ctx)


# Patterns that match direct collection access on a db variable.
_DB_DOT = re.compile(r"\bdb\.([a-z][a-z0-9_]+)\b")
_DB_BRACKET = re.compile(r'\bdb\[(?:"|\')([a-z][a-z0-9_]+)(?:"|\')\]')
# Matches dynamic collection via PART_COLLECTION_MAP or similar constants.
_DB_BRACKET_VAR = re.compile(r"\bdb\[(\w+)\]")


def _collection_refs_in_source(source: str) -> set[str]:
    """Extract collection names referenced via db.xxx or db['xxx']."""
    names: set[str] = set()
    for m in _DB_DOT.finditer(source):
        names.add(m.group(1))
    for m in _DB_BRACKET.finditer(source):
        names.add(m.group(1))
    # Filter out obvious non-collection attribute calls.
    names -= {
        "client", "command", "get_collection", "list_collection_names",
        "create_collection", "drop_collection", "name",
    }
    return names


def _iter_py_files(root: Path):
    for f in root.rglob("*.py"):
        if "__pycache__" in f.parts:
            continue
        yield f


def test_no_cross_context_collection_access() -> None:
    """Contexts must not directly access MongoDB collections owned by another context."""
    violations: list[str] = []

    for file_path in _iter_py_files(CONTEXTS_ROOT):
        rel = file_path.relative_to(BACKEND_ROOT)
        rel_str = rel.as_posix()
        parts = rel.parts
        ctx = _resolve_context(parts)
        if ctx is None:
            continue

        source = file_path.read_text(encoding="utf-8-sig")
        refs = _collection_refs_in_source(source)

        allowed = ALLOWED_CROSS_COLLECTION_ACCESS.get(rel_str, set())

        for col in sorted(refs):
            owner = COLLECTION_OWNER.get(col)
            if owner is None:
                # Unknown collection — not mapped yet; skip.
                continue
            if owner == ctx:
                # Same context — allowed.
                continue
            if col in allowed:
                # Transitional allowlist — allowed for now.
                continue
            violations.append(
                f"{rel_str}: context '{ctx}' accesses collection '{col}' "
                f"owned by '{owner}'"
            )

    assert not violations, (
        "Cross-context MongoDB collection access detected. "
        "Use contracts or service facades instead of direct collection access.\n"
        + "\n".join(sorted(violations))
    )


def test_no_cross_context_collection_writes() -> None:
    """Contexts must not INSERT/UPDATE/DELETE documents in collections owned by another context.

    This is stricter than the read check: even allowlisted reads should not
    include mutations.
    """
    write_ops = re.compile(
        r"\bdb[\.\[].+?\.(insert_one|insert_many|update_one|update_many|"
        r"delete_one|delete_many|replace_one|bulk_write|find_one_and_update|"
        r"find_one_and_replace|find_one_and_delete)\b"
    )

    # Allowlisted write access (strictly shrink over time).
    allowed_writes: dict[str, set[str]] = {
    }

    violations: list[str] = []

    for file_path in _iter_py_files(CONTEXTS_ROOT):
        rel = file_path.relative_to(BACKEND_ROOT)
        rel_str = rel.as_posix()
        parts = rel.parts
        ctx = _resolve_context(parts)
        if ctx is None:
            continue

        source = file_path.read_text(encoding="utf-8-sig")
        file_allowed = allowed_writes.get(rel_str, set())

        for line_no, line in enumerate(source.splitlines(), 1):
            m = write_ops.search(line)
            if not m:
                continue
            # Extract collection name from the line.
            col_match = re.search(r"\bdb\.([a-z][a-z0-9_]+)\.", line) or re.search(
                r'\bdb\[(?:"|\')([a-z][a-z0-9_]+)(?:"|\')\]', line
            )
            if not col_match:
                continue
            col = col_match.group(1)
            owner = COLLECTION_OWNER.get(col)
            if owner is None or owner == ctx:
                continue
            if col in file_allowed:
                continue
            violations.append(
                f"{rel_str}:{line_no}: context '{ctx}' writes to collection "
                f"'{col}' owned by '{owner}'"
            )

    assert not violations, (
        "Cross-context MongoDB collection WRITE access detected. "
        "This violates the 'No cross-context DB writes' architecture rule.\n"
        + "\n".join(sorted(violations))
    )
