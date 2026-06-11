from __future__ import annotations

import ast
import pathlib
import re


BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTEXTS_ROOT = BACKEND_ROOT / "contexts"


def test_no_cross_context_infrastructure_imports() -> None:
    violations: list[str] = []

    for py_file in CONTEXTS_ROOT.rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue
        text = py_file.read_text(encoding="utf-8")
        this_context = py_file.parts[py_file.parts.index("contexts") + 1]

        for match in re.finditer(r"from\s+contexts\.([a-zA-Z_][a-zA-Z0-9_]*)\.infrastructure", text):
            target_context = match.group(1)
            if target_context != this_context:
                violations.append(f"{py_file} imports {target_context}.infrastructure")

        for match in re.finditer(r"import\s+contexts\.([a-zA-Z_][a-zA-Z0-9_]*)\.infrastructure", text):
            target_context = match.group(1)
            if target_context != this_context:
                violations.append(f"{py_file} imports {target_context}.infrastructure")

    assert not violations, "Cross-context infrastructure imports found:\n" + "\n".join(violations)


# ---------------------------------------------------------------------------
# identity ↔ employee_identity boundary enforcement
# ---------------------------------------------------------------------------

def _iter_py_files(root: pathlib.Path):
    for f in root.rglob("*.py"):
        if "__pycache__" in f.parts:
            continue
        yield f


def _imports_from_ast(file_path: pathlib.Path) -> list[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def test_identity_does_not_import_employee_identity_internals() -> None:
    """identity may only import employee_identity.contracts, never domain/infra/repo."""
    violations: list[str] = []
    identity_root = CONTEXTS_ROOT / "identity_access" / "identity"
    for py_file in _iter_py_files(identity_root):
        for imp in _imports_from_ast(py_file):
            if not imp.startswith("contexts.employee_master.identity."):
                continue
            suffix = imp[len("contexts.employee_master.identity."):]
            # contracts imports are the only allowed cross-context surface
            if suffix.startswith("contracts"):
                continue
            rel = py_file.relative_to(BACKEND_ROOT)
            violations.append(f"{rel}: imports {imp}")
    assert not violations, (
        "identity must only use employee_identity via contracts:\n"
        + "\n".join(sorted(violations))
    )


def test_employee_identity_does_not_import_identity_internals() -> None:
    """employee_identity may only import identity.contracts, never infra/services."""
    violations: list[str] = []
    ei_root = CONTEXTS_ROOT / "employee_master" / "identity"
    for py_file in _iter_py_files(ei_root):
        for imp in _imports_from_ast(py_file):
            if not imp.startswith("contexts.identity_access.identity."):
                continue
            suffix = imp[len("contexts.identity_access.identity."):]
            if suffix.startswith("contracts"):
                continue
            rel = py_file.relative_to(BACKEND_ROOT)
            violations.append(f"{rel}: imports {imp}")
    assert not violations, (
        "employee_identity must only use identity via contracts:\n"
        + "\n".join(sorted(violations))
    )


def test_identity_has_no_employee_master_collections() -> None:
    """identity must not directly access employee_identities or counters collections."""
    forbidden = {"employee_identities", "counters", "employee_profiles",
                 "employee_profile_extensions", "employee_profile_read_models"}
    db_access = re.compile(r"\bdb\.([a-z_]+)\b|\bdb\[(?:\"|')([a-z_]+)(?:\"|')\]")
    violations: list[str] = []
    identity_root = CONTEXTS_ROOT / "identity_access" / "identity"
    for py_file in _iter_py_files(identity_root):
        text = py_file.read_text(encoding="utf-8")
        for m in db_access.finditer(text):
            col = m.group(1) or m.group(2)
            if col in forbidden:
                rel = py_file.relative_to(BACKEND_ROOT)
                violations.append(f"{rel}: accesses collection '{col}'")
    assert not violations, (
        "identity must not access employee-master collections:\n"
        + "\n".join(sorted(violations))
    )


def test_identity_contracts_rbac_workflow_shim_deleted() -> None:
    """The dead backward-compat rbac_workflow shim must stay deleted."""
    shim = CONTEXTS_ROOT / "identity_access" / "identity" / "contracts" / "rbac_workflow.py"
    assert not shim.exists(), (
        f"{shim.relative_to(BACKEND_ROOT)} must not exist — "
        "ImmutableAuditLog lives in contexts.audit"
    )


def test_employee_identity_has_no_read_model_subscriber_shim() -> None:
    """The dead subscribers shim with dangling imports must stay deleted."""
    shim = CONTEXTS_ROOT / "employee_master" / "identity" / "contracts" / "subscribers.py"
    assert not shim.exists(), (
        f"{shim.relative_to(BACKEND_ROOT)} must not exist — "
        "read-model subscribers live in employee_profile"
    )


# ---------------------------------------------------------------------------
# Internal structure consistency
# ---------------------------------------------------------------------------

_REQUIRED_FOLDERS = {"api", "application", "contracts", "domain"}

# Contexts that must have the standard folder layout.
_STANDARDIZED_CONTEXTS = {
    "audit",
    "documents",
    "leave",
    "workflow",
    "pay",
}

# Employee Master and Identity Access use sub-packages internally (the merges of
# employee_identity+employee_profile and identity+rbac respectively), so the
# standard folder layout is asserted on those sub-packages rather than the root.
_STANDARDIZED_SUBCONTEXTS = {
    "employee_master/identity",
    "employee_master/profile",
    "identity_access/identity",
}


def test_standardized_contexts_have_required_folders() -> None:
    """Each standardized context must contain api/, application/, contracts/, domain/."""
    violations: list[str] = []
    for ctx_name in sorted(_STANDARDIZED_CONTEXTS | _STANDARDIZED_SUBCONTEXTS):
        ctx_dir = CONTEXTS_ROOT / ctx_name
        if not ctx_dir.is_dir():
            continue
        for folder in sorted(_REQUIRED_FOLDERS):
            folder_path = ctx_dir / folder
            if not folder_path.is_dir():
                violations.append(f"{ctx_name}: missing {folder}/")
            else:
                init_file = folder_path / "__init__.py"
                if not init_file.exists():
                    violations.append(f"{ctx_name}/{folder}: missing __init__.py")
    assert not violations, (
        "Context structure violations:\n" + "\n".join(violations)
    )


def test_no_sys_modules_hack_in_contexts() -> None:
    """No context module should use sys.modules[__name__] redirection."""
    violations: list[str] = []
    for py_file in _iter_py_files(CONTEXTS_ROOT):
        text = py_file.read_text(encoding="utf-8")
        if "sys.modules[__name__]" in text:
            rel = py_file.relative_to(BACKEND_ROOT)
            violations.append(str(rel))
    assert not violations, (
        "sys.modules[__name__] hack found — use explicit re-exports:\n"
        + "\n".join(sorted(violations))
    )


def test_workflow_dead_sub_context_stays_deleted() -> None:
    """The empty change_requests sub-context must stay deleted."""
    dead = CONTEXTS_ROOT / "workflow" / "change_requests"
    assert not dead.exists(), (
        f"{dead.relative_to(BACKEND_ROOT)} must not exist — "
        "change_requests is a separate top-level context"
    )


def test_workflow_domain_has_no_http_dependency() -> None:
    """Workflow domain must raise domain exceptions, not HTTPException."""
    domain_dir = CONTEXTS_ROOT / "workflow" / "domain"
    violations: list[str] = []
    for py_file in domain_dir.rglob("*.py"):
        if py_file.name.startswith("__"):
            continue
        source = py_file.read_text(encoding="utf-8")
        if "HTTPException" in source or "from fastapi" in source:
            violations.append(str(py_file.relative_to(BACKEND_ROOT)))
    assert not violations, (
        "Workflow domain must not depend on fastapi/HTTPException — "
        "raise domain exceptions instead:\n" + "\n".join(sorted(violations))
    )


def test_workflow_backward_compat_aliases_stay_deleted() -> None:
    """Dead backward-compat alias file must not return."""
    dead_service = CONTEXTS_ROOT / "workflow" / "application" / "service.py"
    assert not dead_service.exists(), (
        f"{dead_service.relative_to(BACKEND_ROOT)} must not exist — "
        "WorkflowApplicationService alias was removed"
    )

    commands_file = CONTEXTS_ROOT / "workflow" / "application" / "commands.py"
    source = commands_file.read_text(encoding="utf-8")
    for alias in ("StartWorkflow", "SubmitStep", "ApproveStep", "RejectStep", "RollbackStep"):
        assert alias not in source, (
            f"Legacy alias '{alias}' must not exist in {commands_file.relative_to(BACKEND_ROOT)}"
        )


def test_pay_repository_lives_in_infrastructure() -> None:
    """Pay repository must live in infrastructure/, not repository/."""
    canonical = CONTEXTS_ROOT / "pay_benefits" / "infrastructure" / "pay_repository.py"
    assert canonical.exists(), (
        f"{canonical.relative_to(BACKEND_ROOT)} must exist — "
        "pay repository belongs in infrastructure/"
    )
    old_location = CONTEXTS_ROOT / "pay_benefits" / "repository" / "pay_repository.py"
    assert not old_location.exists(), (
        f"{old_location.relative_to(BACKEND_ROOT)} must not exist — "
        "canonical location is infrastructure/pay_repository.py"
    )


def test_pay_domain_has_no_http_dependency() -> None:
    """Pay domain must not depend on fastapi/HTTP concerns."""
    domain_dir = CONTEXTS_ROOT / "pay_benefits" / "domain"
    violations: list[str] = []
    for py_file in domain_dir.rglob("*.py"):
        if py_file.name.startswith("__"):
            continue
        source = py_file.read_text(encoding="utf-8")
        if "HTTPException" in source or "from fastapi" in source:
            violations.append(str(py_file.relative_to(BACKEND_ROOT)))
    assert not violations, (
        "Pay domain must not depend on fastapi/HTTPException:\n"
        + "\n".join(sorted(violations))
    )


def test_no_external_context_writes_to_pay_ledger() -> None:
    """Only pay context may write to pay_ledger_entries."""
    violations: list[str] = []
    for ctx_dir in CONTEXTS_ROOT.iterdir():
        if not ctx_dir.is_dir() or ctx_dir.name in ("pay_benefits", "__pycache__"):
            continue
        for py_file in ctx_dir.rglob("*.py"):
            source = py_file.read_text(encoding="utf-8", errors="replace")
            if "pay_ledger_entries" in source:
                violations.append(str(py_file.relative_to(BACKEND_ROOT)))
    assert not violations, (
        "Only pay context may reference pay_ledger_entries:\n"
        + "\n".join(sorted(violations))
    )


# ---------------------------------------------------------------------------
# reporting context — pure projection / read-only
# ---------------------------------------------------------------------------

_WRITE_OPS = re.compile(
    r"\.(insert_one|insert_many|update_one|update_many"
    r"|replace_one|delete_one|delete_many|bulk_write)\b"
)


def test_reporting_never_writes_to_any_collection() -> None:
    """Reporting is a pure read-only projection context — no write operations."""
    reporting_root = CONTEXTS_ROOT / "reporting_analytics"
    violations: list[str] = []
    for py_file in reporting_root.rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue
        source = py_file.read_text(encoding="utf-8", errors="replace")
        for m in _WRITE_OPS.finditer(source):
            violations.append(f"{py_file.relative_to(BACKEND_ROOT)}: {m.group(0)}")
    assert not violations, (
        "Reporting must be read-only:\n" + "\n".join(sorted(violations))
    )


def test_reporting_has_no_domain_models() -> None:
    """Reporting should not define its own Pydantic models (no shadow truth)."""
    reporting_root = CONTEXTS_ROOT / "reporting_analytics"
    violations: list[str] = []
    for py_file in reporting_root.rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue
        source = py_file.read_text(encoding="utf-8", errors="replace")
        if re.search(r"class\s+\w+\(.*BaseModel.*\)", source):
            violations.append(str(py_file.relative_to(BACKEND_ROOT)))
    assert not violations, (
        "Reporting must not define Pydantic domain models:\n"
        + "\n".join(sorted(violations))
    )


def test_reporting_dead_scaffolding_stays_deleted() -> None:
    """Empty dashboards/ and projections/ packages were removed."""
    reporting_root = CONTEXTS_ROOT / "reporting_analytics"
    for name in ("dashboards", "projections"):
        assert not (reporting_root / name).exists(), (
            f"reporting/{name}/ was dead scaffolding and should stay deleted"
        )


# ---------------------------------------------------------------------------
# seniority context — owns seniority_lists only, reads canonical sources
# ---------------------------------------------------------------------------

def test_no_external_context_writes_to_seniority_lists() -> None:
    """Only seniority context may write to seniority_lists."""
    violations: list[str] = []
    for ctx_dir in CONTEXTS_ROOT.iterdir():
        if not ctx_dir.is_dir() or ctx_dir.name in ("seniority", "__pycache__"):
            continue
        for py_file in ctx_dir.rglob("*.py"):
            source = py_file.read_text(encoding="utf-8", errors="replace")
            if "seniority_lists" in source:
                violations.append(str(py_file.relative_to(BACKEND_ROOT)))
    assert not violations, (
        "Only seniority context may reference seniority_lists:\n"
        + "\n".join(sorted(violations))
    )


def test_seniority_router_does_not_touch_foreign_collections() -> None:
    """Seniority router delegates cross-context reads to the service layer."""
    router_file = CONTEXTS_ROOT / "seniority" / "api" / "router.py"
    source = router_file.read_text(encoding="utf-8", errors="replace")
    foreign = {"employee_identities", "employee_profile_extensions", "service_book_part_ii_a"}
    violations = [c for c in foreign if c in source]
    assert not violations, (
        "Seniority router should not directly reference foreign collections "
        f"(delegate to application service): {violations}"
    )


def test_seniority_service_documents_canonical_sources() -> None:
    """gather_employees docstring must name the three canonical source contexts."""
    svc_file = CONTEXTS_ROOT / "seniority" / "application" / "seniority_service.py"
    source = svc_file.read_text(encoding="utf-8", errors="replace")
    for expected in ("employee_identity", "employee_profile", "service_book"):
        assert expected in source, (
            f"seniority_service.py must document dependency on {expected} context"
        )


def test_documents_application_uses_leave_contract_for_leave_entities() -> None:
    """Documents may validate Leave attachments, but must not touch Leave collections directly."""
    commands_file = CONTEXTS_ROOT / "documents" / "application" / "commands.py"
    source = commands_file.read_text(encoding="utf-8", errors="replace")
    forbidden_snippets = [
        'db["leaves"]',
        "db['leaves']",
        "db.leave_applications",
    ]
    violations = [snippet for snippet in forbidden_snippets if snippet in source]
    assert not violations, (
        "Documents application must validate Leave entities through "
        "contexts.leave_attendance.contracts.leave_directory, not direct collection access: "
        f"{violations}"
    )


# ---------------------------------------------------------------------------
# collection ownership coverage — every write-path repo asserts ownership
# ---------------------------------------------------------------------------

_OWNERSHIP_ASSERTION_REPOS = {
    "contexts/workflow/infrastructure/repository.py": {"workflow_tasks", "workflow_transitions"},
    "contexts/change_requests/infrastructure/gateway.py": {"change_requests"},
    "contexts/notifications/infrastructure/repo.py": {"notifications"},
    "contexts/documents/repository/metadata_repository.py": {"document_metadata"},
    "contexts/leave_attendance/repository/leave_repository.py": {"leave_applications", "leave_ledger_entries"},
}


def test_write_repos_assert_collection_ownership() -> None:
    """All write-path repository constructors must call assert_collection_ownership."""
    violations: list[str] = []
    for rel_path, expected_collections in _OWNERSHIP_ASSERTION_REPOS.items():
        file_path = BACKEND_ROOT / rel_path
        source = file_path.read_text(encoding="utf-8", errors="replace")
        if "assert_collection_ownership(" not in source:
            violations.append(f"{rel_path}: missing assert_collection_ownership call")
        for col in expected_collections:
            if col not in source:
                violations.append(f"{rel_path}: expected ownership assertion for '{col}'")
    assert not violations, (
        "Write-path repositories must enforce collection ownership:\n"
        + "\n".join(sorted(violations))
    )
