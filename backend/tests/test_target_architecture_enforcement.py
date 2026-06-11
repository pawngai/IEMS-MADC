from __future__ import annotations

import ast
import os
import re
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
CONTEXTS_ROOT = BACKEND_ROOT / "contexts"
FRONTEND_ROOT = BACKEND_ROOT.parent / "frontend" / "src"

REQUIRED_CONTEXTS = {
    "employee_master",
    "identity_access",
    "leave_attendance",
    "organization_master",
    "pay_benefits",
    "reporting_analytics",
    "service_book",
    "workflow",
}

ALLOWED_TRANSITION_CONTEXTS: set[str] = {
    "audit",
    "change_requests",
    "department",
    "documents",
    "employee_identity",
    "employee_profile",
    "ess",
    "identity",
    "leave",
    "notifications",
    "pay",
    "rbac",
    "reporting",
    "seniority",
    "system_admin",
}

REQUIRED_CONTEXT_SUBPACKAGES = {
    "contracts",
}

FORBIDDEN_CONTEXT_IMPORTS = {
    "shared.auth",
    "shared.permissions",
    "models.auth_rbac",
}

FORBIDDEN_PLATFORM_NAMESPACE_IMPORTS = {
    "backend.platform",
    "platform.auth",
    "platform.config",
    "platform.db",
    "platform.logging",
    "platform.web",
}

REQUIRED_APP_PLATFORM_SUBPACKAGES = {
    "audit",
    "auth",
    "authorization",
    "config",
    "db",
    "documents",
    "event_bus",
    "logging",
    "notifications",
    "storage",
    "web",
}

REQUIRED_SHARED_KERNEL_SUBPACKAGES = {
    "events",
    "base",
    "ids",
    "types",
}

ALLOWED_TRANSITION_SHARED_KERNEL_SUBPACKAGES: set[str] = set()

TRANSITION_WRAPPER_FILES = {
    "backend/contexts/leave_attendance/api/router.py",
    "backend/contexts/leave_attendance/contracts/dto.py",
    "backend/contexts/leave_attendance/contracts/leave_commands.py",
    "backend/contexts/leave_attendance/contracts/leave_directory.py",
    "backend/contexts/leave_attendance/contracts/ports.py",
    "backend/contexts/pay_benefits/api/router.py",
    "backend/contexts/pay_benefits/contracts/dto.py",
    "backend/contexts/pay_benefits/contracts/pay_operations.py",
    "backend/contexts/pay_benefits/contracts/ports.py",
    "backend/contexts/reporting_analytics/api/router.py",
    "backend/contexts/reporting_analytics/contracts/analytics_queries.py",
    "backend/contexts/organization_master/api/admin_establishment_router.py",
    "backend/contexts/organization_master/api/router.py",
    "backend/contexts/organization_master/contracts/department_directory.py",
    "backend/contexts/organization_master/contracts/establishment.py",
    "frontend/src/contexts/leave_attendance/index.js",
    "frontend/src/contexts/pay_benefits/index.js",
    "frontend/src/contexts/reporting_analytics/index.js",
    "frontend/src/contexts/organization_master/index.js",
}

ARCH_ENFORCEMENT_MODE = os.getenv("ARCH_ENFORCEMENT_MODE", "staged").strip().lower()


def _iter_py_files(root: Path):
    for file_path in root.rglob("*.py"):
        if "__pycache__" in file_path.parts:
            continue
        yield file_path


def _imports(file_path: Path) -> list[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8-sig"), filename=str(file_path))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    return imported


def test_required_core_contexts_exist() -> None:
    missing = [name for name in sorted(REQUIRED_CONTEXTS) if not (CONTEXTS_ROOT / name).exists()]
    assert not missing, f"Missing required bounded contexts: {missing}"


def test_required_context_subpackages_exist() -> None:
    missing: list[str] = []
    for context_name in sorted(REQUIRED_CONTEXTS):
        context_root = CONTEXTS_ROOT / context_name
        for subpackage in sorted(REQUIRED_CONTEXT_SUBPACKAGES):
            target = context_root / subpackage
            if not target.exists():
                missing.append(str(target.relative_to(BACKEND_ROOT)))

    assert not missing, "Required bounded-context folders are missing:\n" + "\n".join(missing)


def test_only_final_bounded_contexts_exist() -> None:
    actual_contexts = {
        entry.name
        for entry in CONTEXTS_ROOT.iterdir()
        if entry.is_dir() and entry.name != "__pycache__"
    }
    assert REQUIRED_CONTEXTS.issubset(actual_contexts), (
        "Required final bounded contexts are missing. "
        f"Required={sorted(REQUIRED_CONTEXTS)} Actual={sorted(actual_contexts)}"
    )

    if ARCH_ENFORCEMENT_MODE == "final":
        assert actual_contexts == REQUIRED_CONTEXTS, (
            "Bounded contexts must match final architecture exactly. "
            f"Expected={sorted(REQUIRED_CONTEXTS)} Actual={sorted(actual_contexts)}"
        )
        return

    if ARCH_ENFORCEMENT_MODE != "staged":
        raise AssertionError(
            "ARCH_ENFORCEMENT_MODE must be 'staged' or 'final' "
            f"(received: {ARCH_ENFORCEMENT_MODE!r})"
        )

    allowed = REQUIRED_CONTEXTS | ALLOWED_TRANSITION_CONTEXTS
    unexpected = sorted(actual_contexts - allowed)
    assert not unexpected, f"Unexpected contexts found in staged mode: {unexpected}"


def test_service_book_records_api_package_exists() -> None:
    assert (CONTEXTS_ROOT / "service_book" / "records" / "api").exists()


def test_contexts_do_not_import_legacy_auth_modules() -> None:
    violations: list[str] = []
    for py_file in _iter_py_files(CONTEXTS_ROOT):
        rel = py_file.relative_to(BACKEND_ROOT).as_posix()
        for imp in _imports(py_file):
            if imp in FORBIDDEN_CONTEXT_IMPORTS or any(
                imp.startswith(f"{prefix}.") for prefix in FORBIDDEN_CONTEXT_IMPORTS
            ):
                violations.append(f"{rel}: imports {imp}")
    assert not violations, "Forbidden legacy auth imports detected in contexts:\n" + "\n".join(
        sorted(violations)
    )


def test_service_book_feature_folder_exists() -> None:
    assert (FRONTEND_ROOT / "contexts" / "service_book").exists()


def test_frontend_modules_root_removed() -> None:
    assert not (FRONTEND_ROOT / "modules").exists()


def test_service_events_context_absorbed_into_service_book_records() -> None:
    assert not (CONTEXTS_ROOT / "service_events").exists()
    assert (CONTEXTS_ROOT / "service_book").exists()
    assert (CONTEXTS_ROOT / "service_book" / "records").exists()


def test_service_book_layout_matches_target_structure() -> None:
    service_book_root = CONTEXTS_ROOT / "service_book"
    required_subpackages = {
        "domain",
        "application",
        "repository",
        "api",
        "schemas",
        "mappers",
        "opening",
        "parts",
        "records",
        "corrections",
        "verification",
        "projection",
        "pdf",
        "queries",
    }

    missing = [
        str((service_book_root / folder).relative_to(BACKEND_ROOT))
        for folder in sorted(required_subpackages)
        if not (service_book_root / folder).exists()
    ]
    assert not missing, "Required service_book folders are missing:\n" + "\n".join(missing)


def test_legacy_backend_roots_are_removed() -> None:
    assert not (BACKEND_ROOT / "portal").exists()
    assert not (BACKEND_ROOT / "admin").exists()
    assert not (BACKEND_ROOT / "models").exists()
    assert not (BACKEND_ROOT / "legacy_contexts").exists()


def test_platform_shim_directory_is_removed() -> None:
    """The legacy platform/ re-export shim directory must not exist."""
    assert not (BACKEND_ROOT / "platform").exists(), (
        "backend/platform/ shim directory should be deleted — all code uses app_platform directly"
    )


def test_no_runtime_imports_from_platform_namespace() -> None:
    violations: list[str] = []
    for py_file in _iter_py_files(BACKEND_ROOT):
        rel = py_file.relative_to(BACKEND_ROOT).as_posix()
        for imp in _imports(py_file):
            if imp in FORBIDDEN_PLATFORM_NAMESPACE_IMPORTS or any(
                imp.startswith(f"{prefix}.")
                for prefix in FORBIDDEN_PLATFORM_NAMESPACE_IMPORTS
            ):
                violations.append(f"{rel}: imports {imp}")

    assert not violations, "Forbidden runtime imports from platform namespace detected:\n" + "\n".join(
        sorted(violations)
    )


def test_split_backend_modules_stay_under_size_limit() -> None:
    max_lines = 800
    split_modules = [
        BACKEND_ROOT / "contexts" / "system_admin" / "api" / "router.py",
        BACKEND_ROOT / "contexts" / "identity_access" / "identity" / "infrastructure" / "user_management_service.py",
        BACKEND_ROOT / "contexts" / "leave" / "infrastructure" / "gateway.py",
        BACKEND_ROOT / "contexts" / "service_book" / "records" / "schemas" / "service_event_schemas.py",
    ]
    violations = []
    for module_path in split_modules:
        line_count = len(module_path.read_text(encoding="utf-8").splitlines())
        if line_count > max_lines:
            violations.append(f"{module_path.relative_to(BACKEND_ROOT).as_posix()}: {line_count} lines")

    assert not violations, "Split backend modules exceeded size limit:\n" + "\n".join(violations)


def test_server_entrypoint_exists() -> None:
    assert (BACKEND_ROOT / "server.py").exists()


def test_legacy_shared_package_is_removed() -> None:
    if ARCH_ENFORCEMENT_MODE == "final":
        assert not (BACKEND_ROOT / "shared").exists()


def test_no_hardcoded_iems_database_name() -> None:
    """Prevent code from using 'iems' as a database name instead of 'iems_db'."""
    import re

    pattern = re.compile(r"""\[\s*['"]iems['"]\s*\]""")
    violations: list[str] = []
    for py_file in BACKEND_ROOT.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        text = py_file.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                violations.append(f"{py_file.relative_to(BACKEND_ROOT)}:{lineno}: {line.strip()}")
    assert not violations, (
        "Found hardcoded database name 'iems' (should be 'iems_db'):\n"
        + "\n".join(violations)
    )


def test_shared_kernel_contains_only_allowed_subpackages() -> None:
    shared_kernel_root = BACKEND_ROOT / "shared_kernel"
    assert shared_kernel_root.exists()

    actual_subpackages = {
        entry.name
        for entry in shared_kernel_root.iterdir()
        if entry.is_dir() and entry.name != "__pycache__"
    }
    assert REQUIRED_SHARED_KERNEL_SUBPACKAGES.issubset(actual_subpackages)
    if ARCH_ENFORCEMENT_MODE == "final":
        assert actual_subpackages == REQUIRED_SHARED_KERNEL_SUBPACKAGES
    else:
        allowed = REQUIRED_SHARED_KERNEL_SUBPACKAGES | ALLOWED_TRANSITION_SHARED_KERNEL_SUBPACKAGES
        unexpected = sorted(actual_subpackages - allowed)
        assert not unexpected, f"Unexpected shared_kernel subpackages in staged mode: {unexpected}"


def test_service_book_contract_schema_package_owns_servicebook_definitions() -> None:
    assert not (BACKEND_ROOT / "shared_kernel" / "servicebook").exists(), (
        "Service-book schema/revision definitions are domain-specific and must "
        "live under contexts/service_book/contracts/servicebook, not shared_kernel"
    )
    assert (CONTEXTS_ROOT / "service_book" / "contracts" / "servicebook").exists()


def test_app_platform_contains_required_subpackages() -> None:
    """Verify app_platform has all required infrastructure subpackages."""
    app_platform_root = BACKEND_ROOT / "app_platform"
    assert app_platform_root.exists(), "app_platform package must exist"

    actual_subpackages = {
        entry.name
        for entry in app_platform_root.iterdir()
        if entry.is_dir() and entry.name != "__pycache__"
    }
    assert REQUIRED_APP_PLATFORM_SUBPACKAGES.issubset(actual_subpackages), (
        "app_platform is missing required subpackages: "
        f"{sorted(REQUIRED_APP_PLATFORM_SUBPACKAGES - actual_subpackages)}"
    )


def test_no_bootstrap_compat_re_exports() -> None:
    """The legacy routers.py compat shim must not exist."""
    assert not (BACKEND_ROOT / "app" / "bootstrap" / "routers.py").exists(), (
        "app/bootstrap/routers.py compat re-export should be deleted"
    )


def test_no_backend_dot_imports_in_production_code() -> None:
    """Production code must not use 'backend.*' imports — only scripts may."""
    allowed_roots = {"scripts", "tests"}
    violations: list[str] = []
    for py_file in _iter_py_files(BACKEND_ROOT):
        rel = py_file.relative_to(BACKEND_ROOT)
        parts = rel.parts
        if parts[0] in allowed_roots:
            continue
        # Also allow the backend/__init__.py shim itself
        if rel.as_posix() == "backend/__init__.py":
            continue
        for imp in _imports(py_file):
            if imp == "backend" or imp.startswith("backend."):
                violations.append(f"{rel.as_posix()}: imports {imp}")
    assert not violations, (
        "'backend.*' imports are only allowed in scripts/ and tests/:\n"
        + "\n".join(sorted(violations))
    )


def test_transition_wrappers_are_explicitly_marked() -> None:
    repo_root = BACKEND_ROOT.parent
    violations: list[str] = []
    for rel in sorted(TRANSITION_WRAPPER_FILES):
        path = repo_root / rel
        if not path.exists():
            violations.append(f"{rel}: missing")
            continue
        text = path.read_text(encoding="utf-8")
        if "TODO(context-migration)" not in text:
            violations.append(f"{rel}: missing TODO(context-migration)")

    assert not violations, (
        "Transition compatibility wrappers must be explicit and temporary:\n"
        + "\n".join(violations)
    )


def test_backend_router_registration_uses_canonical_contexts() -> None:
    registration_root = BACKEND_ROOT / "app" / "bootstrap" / "registrations"
    forbidden_modules = {
        "contexts.department.api",
        "contexts.leave.api",
        "contexts.pay.api",
        "contexts.reporting.api",
    }
    violations: list[str] = []
    for py_file in _iter_py_files(registration_root):
        rel = py_file.relative_to(BACKEND_ROOT).as_posix()
        for imp in _imports(py_file):
            if imp in forbidden_modules or any(
                imp.startswith(f"{module}.") for module in forbidden_modules
            ):
                violations.append(f"{rel}: imports {imp}")

    assert not violations, (
        "Backend router registration must use canonical context entrypoints:\n"
        + "\n".join(sorted(violations))
    )


def test_frontend_app_and_portals_use_canonical_context_imports() -> None:
    frontend_root = BACKEND_ROOT.parent / "frontend"
    scan_roots = [
        frontend_root / "src" / "app",
        frontend_root / "src" / "portals",
    ]
    forbidden = re.compile(r'@/contexts/(leave|pay|analytics|reporting|department|masters)(?:/|")')
    violations: list[str] = []
    for root in scan_roots:
        for file_path in root.rglob("*"):
            if not file_path.is_file() or file_path.suffix not in {".js", ".jsx", ".ts", ".tsx"}:
                continue
            if "__tests__" in file_path.parts:
                continue
            text = file_path.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), 1):
                if forbidden.search(line):
                    rel = file_path.relative_to(frontend_root).as_posix()
                    violations.append(f"{rel}:{lineno}: {line.strip()}")

    assert not violations, (
        "Frontend app/portal composition must import canonical context entrypoints:\n"
        + "\n".join(sorted(violations))
    )
