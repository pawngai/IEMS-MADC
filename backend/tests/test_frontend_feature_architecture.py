from __future__ import annotations

import json
import os
import re
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_SRC = WORKSPACE_ROOT / "frontend" / "src"
CONTEXTS_ROOT = FRONTEND_SRC / "contexts"
APP_CONTEXTS_ROOT = FRONTEND_SRC / "app" / "contexts"

# Deprecated staged baseline. In final mode, app/contexts must not exist.
APP_CONTEXTS_STAGED_BASELINE = 85

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

LEGACY_CONTEXT_IMPORTS = {
    "@/features/employee/",
    "@/features/serviceBook/",
    "@/features/serviceEvents/",
    "@/features/leave/",
    "@/features/pay/",
    "@/features/documents/",
    "@/features/audit/",
}

CONTEXT_IMPORT_RE = re.compile(r"@/contexts/([A-Za-z0-9_-]+)/")
CONTEXT_BOUNDARY_ALLOWLIST_PATH = (
    FRONTEND_SRC / "contexts" / "__tests__" / "fixtures" / "context-boundary-allowlist.json"
)

REQUIRED_SHARED_SUBDIRS = {
    "ui",
    "lib",
    "api",
    "types",
}

REQUIRED_FRONTEND_TOP_LEVEL = {
    "app",
    "contexts",
    "features",
    "platform",
    "portals",
    "shared",
}

FRONTEND_ARCH_ENFORCEMENT_MODE = os.getenv("FRONTEND_ARCH_ENFORCEMENT_MODE", "final").strip().lower()

DEPRECATED_CONTEXT_BASELINES = {
    "access_control": 2,
    "admin": 25,
    "analytics": 9,
    "audit": 5,
    "change_requests": 16,
    "department": 18,
    "documents": 5,
    "employee_identity": 8,
    "employee_profile": 16,
    "ess": 8,
    "identity": 11,
    "leave": 11,
    "masters": 2,
    "notifications": 3,
    "pay": 3,
    "seniority": 6,
}


def _iter_frontend_source_files():
    for pattern in ("*.js", "*.jsx", "*.ts", "*.tsx"):
        for file_path in FRONTEND_SRC.rglob(pattern):
            if "node_modules" in file_path.parts:
                continue
            yield file_path


def test_required_frontend_top_level_directories_exist() -> None:
    missing = [name for name in sorted(REQUIRED_FRONTEND_TOP_LEVEL) if not (FRONTEND_SRC / name).exists()]
    assert not missing, f"Missing required frontend top-level directories: {missing}"


def test_only_target_frontend_top_level_directories_exist_in_final_mode() -> None:
    actual_top_level_dirs = {
        entry.name
        for entry in FRONTEND_SRC.iterdir()
        if entry.is_dir() and entry.name != "__mocks__"
    }

    assert REQUIRED_FRONTEND_TOP_LEVEL.issubset(actual_top_level_dirs), (
        "Required frontend top-level directories are missing. "
        f"Required={sorted(REQUIRED_FRONTEND_TOP_LEVEL)} Actual={sorted(actual_top_level_dirs)}"
    )

    if FRONTEND_ARCH_ENFORCEMENT_MODE == "final":
        assert actual_top_level_dirs == REQUIRED_FRONTEND_TOP_LEVEL, (
            "Frontend top-level directories must match target architecture exactly. "
            f"Expected={sorted(REQUIRED_FRONTEND_TOP_LEVEL)} Actual={sorted(actual_top_level_dirs)}"
        )
        return

    if FRONTEND_ARCH_ENFORCEMENT_MODE != "staged":
        raise AssertionError(
            "FRONTEND_ARCH_ENFORCEMENT_MODE must be 'staged' or 'final' "
            f"(received: {FRONTEND_ARCH_ENFORCEMENT_MODE!r})"
        )


def test_required_context_directories_exist() -> None:
    missing = [name for name in sorted(REQUIRED_CONTEXTS) if not (CONTEXTS_ROOT / name).exists()]
    assert not missing, f"Missing required frontend contexts: {missing}"


def test_deprecated_frontend_contexts_do_not_grow() -> None:
    violations: list[str] = []
    for context_name, baseline in DEPRECATED_CONTEXT_BASELINES.items():
        context_root = CONTEXTS_ROOT / context_name
        if not context_root.exists():
            continue
        current = sum(
            1
            for f in context_root.rglob("*")
            if f.is_file()
            and f.suffix in {".js", ".jsx", ".ts", ".tsx"}
            and "__tests__" not in f.parts
        )
        if current > baseline:
            violations.append(f"{context_name}: {current} source files (baseline={baseline})")

    assert not violations, (
        "Deprecated frontend contexts have grown beyond their baseline:\n"
        + "\n".join(sorted(violations))
    )


def test_legacy_modules_root_is_removed() -> None:
    assert not (FRONTEND_SRC / "modules").exists()


def test_required_shared_subdirectories_exist() -> None:
    shared_root = FRONTEND_SRC / "shared"
    missing = [name for name in sorted(REQUIRED_SHARED_SUBDIRS) if not (shared_root / name).exists()]
    assert not missing, f"Missing required shared subdirectories: {missing}"


def test_legacy_frontend_context_imports_removed_for_core_domains() -> None:
    if FRONTEND_ARCH_ENFORCEMENT_MODE != "final":
        return

    violations: list[str] = []
    for file_path in _iter_frontend_source_files():
        rel = file_path.relative_to(WORKSPACE_ROOT).as_posix()
        source = file_path.read_text(encoding="utf-8")
        for token in LEGACY_CONTEXT_IMPORTS:
            if token in source:
                violations.append(f"{rel}: contains legacy import '{token}'")

    assert not violations, "Legacy core-domain context imports detected:\n" + "\n".join(sorted(violations))


def test_cross_context_imports_use_allowlist_only() -> None:
    violations: list[str] = []

    allowlist = json.loads(CONTEXT_BOUNDARY_ALLOWLIST_PATH.read_text(encoding="utf-8"))
    allowlist_set = set(allowlist if isinstance(allowlist, list) else [])

    for file_path in _iter_frontend_source_files():
        if "contexts" not in file_path.parts or "__tests__" in file_path.parts:
            continue

        rel = file_path.relative_to(WORKSPACE_ROOT).as_posix()
        context_rel = file_path.relative_to(CONTEXTS_ROOT).as_posix()
        parts = rel.split("/")
        owner_context = parts[3] if len(parts) > 3 and parts[2] == "contexts" else None
        if not owner_context:
            continue

        source = file_path.read_text(encoding="utf-8")
        for match in CONTEXT_IMPORT_RE.finditer(source):
            target_context = match.group(1)
            if target_context == owner_context:
                continue
            violations.append(f"{context_rel} -> {target_context}")

    new_violations = sorted(set(violations) - allowlist_set)
    assert not new_violations, "Forbidden cross-context imports detected:\n" + "\n".join(new_violations)


def test_app_contexts_deprecated_folder_is_removed_or_staged_frozen() -> None:
    """frontend/src/app/contexts/ is deprecated. In final mode it must not
    exist. In staged mode it may exist but must not grow."""
    if FRONTEND_ARCH_ENFORCEMENT_MODE == "final":
        assert not APP_CONTEXTS_ROOT.exists(), (
            "app/contexts/ is deprecated and must be removed in final mode. "
            "Place domain code under src/contexts/."
        )
        return

    if not APP_CONTEXTS_ROOT.exists():
        return

    current = sum(
        1
        for f in APP_CONTEXTS_ROOT.rglob("*")
        if f.is_file()
        and f.suffix in {".js", ".jsx", ".ts", ".tsx"}
        and "__tests__" not in f.parts
    )
    assert current <= APP_CONTEXTS_STAGED_BASELINE, (
        f"app/contexts/ has {current} source files (baseline={APP_CONTEXTS_STAGED_BASELINE}). "
        f"Do not add new code here — use src/contexts/ instead."
    )
