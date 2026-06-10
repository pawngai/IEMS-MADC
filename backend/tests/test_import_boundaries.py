from __future__ import annotations

import ast
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
CONTEXTS_ROOT = BACKEND_ROOT / "contexts"
SHARED_KERNEL_ROOT = BACKEND_ROOT / "shared_kernel"

# RBAC models and access-control helpers are a cross-cutting platform concern:
# every context needs Permission/Authority enums for API authorization guards.
# These prefixes are universally allowed as cross-context imports.
UNIVERSALLY_ALLOWED_RBAC_PREFIXES = {
    "contexts.rbac.contracts.models",
    "contexts.rbac.contracts.access_control",
}

ALLOWED_CONTEXTS_MODULE_IMPORT_FILES = {
}

ALLOWED_DYNAMIC_IMPORT_FILES = {
    "app_platform/db/migration_runner.py",
}

ALLOWED_WRITE_CONTRACT_MODULES = {
    "contexts/change_requests/contracts/ports.py",
    "contexts/identity/contracts/department_authority_commands.py",
    "contexts/employee_identity/contracts/identity_commands.py",
    "contexts/employee_profile/contracts/immutability.py",
    "contexts/employee_profile/contracts/ports.py",
    "contexts/employee_profile/contracts/profile_commands.py",
    "contexts/identity/contracts/system_config.py",
    "contexts/identity/contracts/user_directory.py",
    "contexts/leave/contracts/leave_commands.py",
    "contexts/leave/contracts/ports.py",
    "contexts/notifications/contracts/notification_commands.py",
    "contexts/notifications/contracts/publisher.py",
    "contexts/service_book/contracts/servicebook/revisions.py",
}

WRITE_OPERATION_NAMES = {
    "archive",
    "create",
    "delete",
    "ensure",
    "insert",
    "mark",
    "publish",
    "refresh",
    "remove",
    "set",
    "update",
    "upsert",
}

DB_WRITE_METHODS = {
    "delete_many",
    "delete_one",
    "find_one_and_delete",
    "find_one_and_replace",
    "find_one_and_update",
    "insert_many",
    "insert_one",
    "replace_one",
    "update_many",
    "update_one",
}

ALLOWED_CROSS_CONTEXT_IMPORT_PREFIXES_BY_FILE = {
    "contexts/employee_identity/api/read_router.py": {
        "contexts.identity.contracts.user_role",
        "contexts.employee_profile.contracts.profile_directory",
    },
    "contexts/employee_identity/api/write_router.py": {
        "contexts.identity.contracts.user_role",
    },
    "contexts/employee_identity/application/identity_interface.py": {
        "contexts.service_book.records.contracts.service_summary_directory",
    },
    "contexts/employee_profile/api/admin_router.py": {
        "contexts.identity.contracts.user_role",
    },
    "contexts/employee_profile/api/completion_router.py": {
        "contexts.identity.contracts.user_role",
    },
    "contexts/employee_profile/api/read_router.py": {
        "contexts.identity.contracts.user_role",
        "contexts.identity.contracts.user_directory",
    },
    "contexts/employee_profile/api/workflow_router.py": {
        "contexts.identity.contracts.user_role",
    },
    "contexts/employee_profile/api/write_router.py": {
        "contexts.identity.contracts.user_role",
    },
    "contexts/employee_profile/contracts/attestation.py": {
        "contexts.employee_identity.contracts.designation_directory",
    },
    "contexts/employee_profile/contracts/profile_commands.py": {
        "contexts.employee_identity.contracts.identity_directory",
    },
    "contexts/department/services/department_portal_service.py": {
        "contexts.identity.contracts.user_directory",
    },
    "contexts/department/services/directory_service.py": {
        "contexts.employee_profile.contracts.profile_directory",
        "contexts.employee_profile.contracts.workflow_status_utils",
        "contexts.identity.contracts.user_directory",
    },
    "contexts/department/services/portal_common.py": {
        "contexts.employee_profile.contracts.profile_directory",
        "contexts.identity.contracts.user_directory",
        "contexts.rbac.application.authorization_service",
    },
    "contexts/department/services/workload_service.py": {
        "contexts.employee_profile.contracts.workflow_status_utils",
    },
    "contexts/department/repository/department_portal_repo.py": {
        "contexts.employee_profile.contracts.profile_directory",
        "contexts.employee_profile.contracts.workflow_status_utils",
        "contexts.employee_identity.contracts.identity_directory",
        "contexts.leave.contracts.leave_directory",
        "contexts.audit.contracts.audit_directory",
    },
    "contexts/change_requests/infrastructure/gateway.py": {
        "contexts.employee_profile.contracts.profile_directory",
        "contexts.change_requests.infrastructure.document_lock",
        "contexts.identity.contracts.user_role",
        "contexts.identity.contracts.user_directory",
        "contexts.notifications.contracts.publisher",
    },
    "contexts/change_requests/infrastructure/document_lock.py": {
        "contexts.documents.contracts.document_lock",
    },
    "contexts/leave/infrastructure/document_lock.py": {
        "contexts.documents.contracts.document_lock",
    },
    "contexts/change_requests/application/apply_handler.py": {
        "contexts.employee_profile.contracts.immutability",
        "contexts.employee_profile.contracts.profile_commands",
        "contexts.employee_profile.contracts.profile_directory",
        "contexts.service_book.records.contracts.service_history_bridge",
    },
    "contexts/change_requests/application/service.py": {
        "contexts.employee_identity.contracts.events",
    },
    "contexts/employee_profile/application/services/workflow_engine.py": {
        "contexts.employee_identity.contracts.events",
    },
    "contexts/leave/infrastructure/gateway.py": {
        "contexts.rbac.application.authorization_service",
        "contexts.documents.contracts.document_metadata",
        "contexts.identity.contracts.user_directory",
        "contexts.employee_identity.contracts.identity_directory",
        "contexts.rbac.policies.operational",
        "contexts.service_book.contracts.servicebook",
    },
    "contexts/leave/infrastructure/gateway_helpers.py": {
        "contexts.documents.contracts.document_metadata",
        "contexts.identity.contracts.user_directory",
        "contexts.employee_identity.contracts.identity_directory",
        "contexts.rbac.application.authorization_service",
        "contexts.service_book.contracts.service_book_directory",
    },
    "contexts/leave/api/router.py": {
        "contexts.rbac.policies.operational",
    },
    "contexts/pay/api/router.py": {
        "contexts.rbac.policies.operational",
    },
    "contexts/pay/infrastructure/gateway.py": {
        "contexts.employee_profile.contracts.profile_directory",
    },
    "contexts/documents/api/router.py": {
        "contexts.rbac.policies.operational",
    },
    "contexts/documents/application/commands.py": {
        "contexts.employee_identity.contracts.identity_directory",
        "contexts.change_requests.contracts.change_request_directory",
        "contexts.leave.contracts.leave_directory",
    },
    "contexts/documents/infrastructure/access_control.py": {
        "contexts.rbac.policies.operational",
    },
    "contexts/documents/infrastructure/storage_ops.py": {
        "contexts.employee_profile.contracts.media_directory",
    },

    "contexts/leave/repository/leave_repository.py": {
        "contexts.employee_profile.contracts.profile_directory",
    },

    "contexts/service_book/read_side/contracts/print_view.py": {
        "contexts.employee_identity.contracts.identity_directory",
        "contexts.service_book.application.service",
    },
    "contexts/service_book/read_side/application/queries/get_service_book.py": {
    },
    "contexts/identity/infrastructure/auth_session_service.py": {
        "contexts.employee_identity.contracts.identity_directory",
    },
    "contexts/identity/infrastructure/user_management_service.py": {
        "contexts.rbac.application.authorization_service",
        "contexts.employee_identity.contracts.identity_directory",
        "contexts.employee_profile.contracts.profile_directory",
    },
    "contexts/identity/infrastructure/user_management_roles.py": {
        "contexts.employee_identity.contracts.identity_directory",
    },
    "contexts/ess/services/ess_service.py": {
        "contexts.employee_identity.contracts.employee_domain",
    },
    "contexts/ess/infrastructure/repo.py": {
        "contexts.documents.contracts.document_metadata",
        "contexts.employee_profile.contracts.profile_commands",
        "contexts.employee_profile.contracts.profile_directory",
        "contexts.leave.contracts.leave_directory",
        "contexts.notifications.contracts.notification_commands",
        "contexts.notifications.contracts.notification_directory",
        "contexts.service_book.contracts.service_book_directory",
    },
    "contexts/ess/infrastructure/service.py": {
        "contexts.employee_identity.contracts.employee_domain",
        "contexts.leave.contracts.leave_commands",
        "contexts.service_book.contracts.servicebook",
    },
    "contexts/system_admin/api/shared.py": {
        "contexts.service_book.contracts.service_book_directory",
    },
    "contexts/system_admin/api/router.py": {
        "contexts.audit.contracts.audit_directory",
        "contexts.employee_identity.contracts.identity_commands",
        "contexts.employee_profile.contracts.profile_commands",
        "contexts.identity.contracts.user_directory",
        "contexts.identity.contracts.system_config",
        "contexts.employee_profile.contracts.profile_directory",
        "contexts.leave.contracts.leave_commands",
        "contexts.leave.contracts.leave_directory",
        "contexts.service_book.contracts.service_book_directory",
    },
    "contexts/system_admin/api/audit_helpers.py": {
        "contexts.audit.contracts.audit_directory",
    },
    "contexts/system_admin/department/api/management_router.py": {
        "contexts.identity.contracts.department_authority_commands",
    },
    "contexts/service_book/application/service.py": {
        "contexts.employee_identity.contracts.employee_domain",
        "contexts.service_book.domain.service_book_rules",
        "contexts.service_book.read_side.application.factory",
    },
    "contexts/service_book/application/queries/print_queries.py": {
        "contexts.employee_identity.contracts.identity_directory",
        "contexts.service_book.records.contracts.service_summary_directory",
    },
    "contexts/service_book/application/queries/service_book_queries.py": {
        "contexts.employee_identity.contracts.identity_directory",
        "contexts.employee_profile.contracts.profile_directory",
        "contexts.service_book.records.contracts.service_summary_directory",
    },
    "contexts/service_book/api/query_router.py": {
        "contexts.employee_identity.contracts.identity_directory",
        "contexts.service_book.read_side.application.factory",
        "contexts.service_book.records.contracts.service_summary_directory",
    },
    "contexts/service_book/read_side/read_model/projectors/part_vi_leave_projection.py": {
        "contexts.leave.contracts.leave_directory",
    },
    "contexts/service_book/read_side/application/projection_rebuilder.py": {
        "contexts.service_book.records.contracts.approved_event_records",
    },
    "contexts/service_book/records/api/router.py": {
        "contexts.employee_identity.contracts.identity_directory",
    },

}

# The active rule is now simple: cross-context imports must use
# contexts.<context>.contracts.*. The old migration allowlist above is retained
# as historical context, but it must not permit new private imports.
ALLOWED_CROSS_CONTEXT_IMPORT_PREFIXES_BY_FILE = {}


def _is_allowlisted_cross_context_import(rel_path: str, import_path: str) -> bool:
    allowed_prefixes = ALLOWED_CROSS_CONTEXT_IMPORT_PREFIXES_BY_FILE.get(rel_path, set())
    return any(import_path.startswith(prefix) for prefix in allowed_prefixes)


def _is_cross_context_internal_import(import_path: str) -> bool:
    return (
        ".infrastructure." in import_path
        or ".repository." in import_path
        or import_path.endswith(".infrastructure")
        or import_path.endswith(".repository")
    )


def _iter_py_files(root: Path):
    if not root.exists():
        return
    for file_path in root.rglob("*.py"):
        if "__pycache__" in file_path.parts:
            continue
        yield file_path


def _imports_from_ast(file_path: Path) -> list[str]:
    # Use utf-8-sig so files with BOM parse cleanly across platforms.
    tree = ast.parse(file_path.read_text(encoding="utf-8-sig"), filename=str(file_path))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    return imported


def _calls_from_ast(file_path: Path) -> list[ast.Call]:
    tree = ast.parse(file_path.read_text(encoding="utf-8-sig"), filename=str(file_path))
    return [node for node in ast.walk(tree) if isinstance(node, ast.Call)]


def _function_defs_from_ast(file_path: Path) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    tree = ast.parse(file_path.read_text(encoding="utf-8-sig"), filename=str(file_path))
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def _is_dynamic_import_call(node: ast.Call) -> bool:
    if isinstance(node.func, ast.Name) and node.func.id == "__import__":
        return True
    if isinstance(node.func, ast.Attribute) and node.func.attr == "import_module":
        return isinstance(node.func.value, ast.Name) and node.func.value.id == "importlib"
    return False


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    if isinstance(node.func, ast.Name):
        return node.func.id
    return None


def _looks_like_write_function(name: str) -> bool:
    first_word = name.split("_", 1)[0]
    return first_word in WRITE_OPERATION_NAMES


def test_non_platform_code_does_not_import_deprecated_shared_business_namespace() -> None:
    violations: list[str] = []
    for file_path in _iter_py_files(BACKEND_ROOT) or []:
        rel = file_path.relative_to(BACKEND_ROOT)
        rel_str = rel.as_posix()
        if rel_str.startswith("platform/"):
            continue

        imports = _imports_from_ast(file_path)
        for imp in imports:
            if imp.startswith("shared.forms") or imp.startswith("shared.reference_data") or imp.startswith("shared.rules_engine"):
                violations.append(f"{rel}: imports deprecated namespace {imp}")

    assert not violations, (
        "Deprecated shared business namespaces found. "
        "Use `platform.*` instead:\n" + "\n".join(sorted(violations))
    )


def test_dynamic_imports_are_restricted_and_do_not_target_deprecated_platform() -> None:
    violations: list[str] = []
    for file_path in _iter_py_files(BACKEND_ROOT) or []:
        rel = file_path.relative_to(BACKEND_ROOT)
        rel_str = rel.as_posix()
        for call in _calls_from_ast(file_path):
            if not _is_dynamic_import_call(call):
                continue
            module_arg = call.args[0] if call.args else None
            module_name = (
                module_arg.value
                if isinstance(module_arg, ast.Constant) and isinstance(module_arg.value, str)
                else None
            )
            if module_name and module_name.startswith("platform."):
                violations.append(f"{rel}: dynamically imports deprecated {module_name}")
            if rel_str not in ALLOWED_DYNAMIC_IMPORT_FILES:
                violations.append(f"{rel}: uses dynamic import outside allowlist")

    assert not violations, (
        "Unexpected dynamic imports found. Use normal imports unless this is an allowlisted loader:\n"
        + "\n".join(sorted(violations))
    )


def test_write_capable_contract_modules_are_explicitly_named_or_allowlisted() -> None:
    violations: list[str] = []
    for file_path in _iter_py_files(CONTEXTS_ROOT) or []:
        rel = file_path.relative_to(BACKEND_ROOT)
        rel_str = rel.as_posix()
        if "/contracts/" not in rel_str:
            continue

        write_functions = [
            node.name
            for node in _function_defs_from_ast(file_path)
            if _looks_like_write_function(node.name)
        ]
        write_calls = [
            name
            for call in _calls_from_ast(file_path)
            if (name := _call_name(call)) in DB_WRITE_METHODS
        ]

        if not write_functions and not write_calls:
            continue
        if rel_str in ALLOWED_WRITE_CONTRACT_MODULES:
            continue
        violations.append(
            f"{rel}: write-capable contract surface (functions={write_functions}, db_calls={write_calls})"
        )

    assert not violations, (
        "Write-capable contract modules must be command/publisher/revision surfaces and explicitly allowlisted:\n"
        + "\n".join(sorted(violations))
    )


def test_contexts_do_not_import_each_other_directly() -> None:
    violations: list[str] = []
    for file_path in _iter_py_files(CONTEXTS_ROOT) or []:
        rel = file_path.relative_to(BACKEND_ROOT)
        rel_str = rel.as_posix()
        parts = rel.parts
        if len(parts) < 2:
            continue
        current_context = parts[1]
        imports = _imports_from_ast(file_path)
        for imp in imports:
            if not imp.startswith("contexts."):
                continue
            segments = imp.split(".")
            if len(segments) < 2:
                continue
            target_context = segments[1]
            if target_context != current_context:
                if len(segments) >= 3 and segments[2] == "contracts":
                    continue
                if any(imp.startswith(p) for p in UNIVERSALLY_ALLOWED_RBAC_PREFIXES):
                    continue
                if _is_allowlisted_cross_context_import(rel_str, imp):
                    continue
                violations.append(f"{rel}: imports {imp}")
    assert not violations, "Cross-context imports found:\n" + "\n".join(sorted(violations))


def test_employee_master_is_canonical_employee_contract_boundary() -> None:
    assert (CONTEXTS_ROOT / "employee_master" / "contracts").exists()

    violations: list[str] = []
    employee_implementation_contexts = {
        "employee_identity",
        "employee_profile",
        "employee_master",
    }
    legacy_prefixes = (
        "contexts.employee_identity.contracts",
        "contexts.employee_profile.contracts",
    )

    for file_path in _iter_py_files(CONTEXTS_ROOT) or []:
        rel = file_path.relative_to(BACKEND_ROOT)
        parts = rel.parts
        if len(parts) < 2:
            continue
        current_context = parts[1]
        if current_context in employee_implementation_contexts:
            continue
        for imp in _imports_from_ast(file_path):
            if imp.startswith(legacy_prefixes):
                violations.append(f"{rel}: imports {imp}")

    assert not violations, (
        "External contexts must use contexts.employee_master.contracts for "
        "employee current facts:\n" + "\n".join(sorted(violations))
    )


def test_domain_layer_has_no_cross_context_imports() -> None:
    """A bounded context's domain layer must never import another bounded
    context's modules — not even its contracts. Cross-context coupling
    belongs in the application layer (orchestration) or the contracts layer
    (anti-corruption). RBAC enums are the only platform-wide exception."""
    violations: list[str] = []
    for file_path in _iter_py_files(CONTEXTS_ROOT) or []:
        rel = file_path.relative_to(BACKEND_ROOT)
        parts = rel.parts
        if len(parts) < 4:
            continue
        if parts[2] != "domain":
            continue
        current_context = parts[1]
        for imp in _imports_from_ast(file_path):
            if not imp.startswith("contexts."):
                continue
            segments = imp.split(".")
            if len(segments) < 2:
                continue
            target_context = segments[1]
            if target_context == current_context:
                continue
            if any(imp.startswith(p) for p in UNIVERSALLY_ALLOWED_RBAC_PREFIXES):
                continue
            violations.append(f"{rel}: domain layer imports {imp}")
    assert not violations, (
        "Domain layer cross-context imports found. Move the coupling into "
        "the application layer and pass resolved values into the domain "
        "rule:\n" + "\n".join(sorted(violations))
    )


def test_domain_layer_does_not_import_its_infrastructure() -> None:
    violations: list[str] = []
    for file_path in _iter_py_files(CONTEXTS_ROOT) or []:
        rel = file_path.relative_to(BACKEND_ROOT)
        parts = rel.parts
        if len(parts) < 4:
            continue
        if parts[2] != "domain":
            continue
        context_name = parts[1]
        forbidden_prefix = f"contexts.{context_name}.infrastructure"
        imports = _imports_from_ast(file_path)
        for imp in imports:
            if imp.startswith(forbidden_prefix):
                violations.append(f"{rel}: imports {imp}")
    assert not violations, "Domain->Infrastructure import violations:\n" + "\n".join(sorted(violations))


def test_application_layer_does_not_import_modules_package() -> None:
    violations: list[str] = []
    for file_path in _iter_py_files(CONTEXTS_ROOT) or []:
        rel = file_path.relative_to(BACKEND_ROOT)
        parts = rel.parts
        if len(parts) < 4:
            continue
        if parts[2] != "application":
            continue
        imports = _imports_from_ast(file_path)
        for imp in imports:
            if imp.startswith("modules."):
                violations.append(f"{rel}: imports {imp}")
    assert not violations, "Application layer must not import modules package:\n" + "\n".join(sorted(violations))


def test_domain_layer_does_not_import_modules_package() -> None:
    violations: list[str] = []
    for file_path in _iter_py_files(CONTEXTS_ROOT) or []:
        rel = file_path.relative_to(BACKEND_ROOT)
        parts = rel.parts
        if len(parts) < 4:
            continue
        if parts[2] != "domain":
            continue
        imports = _imports_from_ast(file_path)
        for imp in imports:
            if imp.startswith("modules."):
                violations.append(f"{rel}: imports {imp}")
    assert not violations, "Domain layer must not import modules package:\n" + "\n".join(sorted(violations))


def test_contexts_modules_imports_are_allowlisted() -> None:
    violations: list[str] = []
    for file_path in _iter_py_files(CONTEXTS_ROOT) or []:
        rel = file_path.relative_to(BACKEND_ROOT)
        rel_str = rel.as_posix()
        imports = _imports_from_ast(file_path)
        has_modules_import = any(imp.startswith("modules.") for imp in imports)
        if not has_modules_import:
            continue
        if rel_str not in ALLOWED_CONTEXTS_MODULE_IMPORT_FILES:
            violations.append(f"{rel}: imports modules.* but is not allowlisted")
    assert not violations, "contexts modules imports must be explicitly allowlisted:\n" + "\n".join(sorted(violations))


def test_cross_context_imports_do_not_target_internal_layers() -> None:
    violations: list[str] = []
    for file_path in _iter_py_files(CONTEXTS_ROOT) or []:
        rel = file_path.relative_to(BACKEND_ROOT)
        rel_str = rel.as_posix()
        parts = rel.parts
        if len(parts) < 2:
            continue
        current_context = parts[1]
        imports = _imports_from_ast(file_path)
        for imp in imports:
            if not imp.startswith("contexts."):
                continue
            segments = imp.split(".")
            if len(segments) < 2:
                continue
            target_context = segments[1]
            if target_context == current_context:
                continue
            if len(segments) >= 3 and segments[2] == "contracts":
                continue
            if not _is_cross_context_internal_import(imp):
                continue
            if _is_allowlisted_cross_context_import(rel_str, imp):
                continue
            violations.append(f"{rel}: imports internal module {imp}")

    assert not violations, (
        "Cross-context internal-layer imports are not allowed. "
        "Import contracts/services API instead:\n" + "\n".join(sorted(violations))
    )


def test_shared_kernel_stays_small() -> None:
    allowed = {
        "__init__.py",
        "errors.py",
        "ids.py",
        "typing.py",
        # Internal subpackage implementations (canonical, not transitional).
        "uuid_generator.py",
        "clock.py",
        "request_context.py",
    }
    files = {p.name for p in _iter_py_files(SHARED_KERNEL_ROOT) or []}
    extra = sorted(files - allowed)
    assert not extra, f"shared_kernel should only contain {sorted(allowed)}; found extras: {extra}"


def test_contexts_do_not_import_deprecated_platform_namespace() -> None:
    """Contexts must use app_platform.*, not the deprecated platform.* namespace."""
    violations: list[str] = []
    for file_path in _iter_py_files(CONTEXTS_ROOT) or []:
        rel = file_path.relative_to(BACKEND_ROOT)
        imports = _imports_from_ast(file_path)
        for imp in imports:
            if imp.startswith("platform.") or imp == "platform":
                violations.append(f"{rel}: imports deprecated {imp}")
    assert not violations, (
        "Contexts must not import from the deprecated platform.* namespace. "
        "Use app_platform.* instead:\n" + "\n".join(sorted(violations))
    )


def test_service_book_profile_derivation_helpers_are_removed() -> None:
    derivation_module = BACKEND_ROOT / "contexts" / "service_book" / "domain" / "profile_derivation.py"
    assert not derivation_module.exists(), "Legacy Service Book profile derivation module must stay deleted"

    violations: list[str] = []
    for file_path in _iter_py_files(BACKEND_ROOT) or []:
        rel = file_path.relative_to(BACKEND_ROOT)
        for imp in _imports_from_ast(file_path):
            if "profile_derivation" in imp:
                violations.append(f"{rel}: imports removed module {imp}")

    assert not violations, (
        "Runtime/test code still imports removed Service Book derivation helpers:\n"
        + "\n".join(sorted(violations))
    )


# Baseline file counts for deprecated directories.  New code must NOT land here.
# When a directory is fully drained, reduce the count to 0 and eventually
# delete the directory.
DEPRECATED_FOLDER_BASELINES: dict[str, int] = {
}


def test_deprecated_folders_do_not_grow() -> None:
    """Prevent new .py files from being added to deprecated backend directories."""
    violations: list[str] = []
    for folder, baseline in DEPRECATED_FOLDER_BASELINES.items():
        folder_path = BACKEND_ROOT / folder
        if not folder_path.exists():
            continue
        current = sum(1 for _ in _iter_py_files(folder_path))
        if current > baseline:
            violations.append(
                f"{folder}: has {current} .py files (baseline={baseline}). "
                f"Do not add new code to deprecated directories."
            )
    assert not violations, (
        "Deprecated folders have grown beyond their baseline:\n"
        + "\n".join(sorted(violations))
    )


def test_cross_context_allowlist_has_no_stale_entries() -> None:
    """Every entry in the allowlist must correspond to a real file that
    actually performs the listed cross-context import. Stale entries mask
    regression — remove them when the coupling is eliminated."""
    stale: list[str] = []

    for rel_str, allowed_prefixes in ALLOWED_CROSS_CONTEXT_IMPORT_PREFIXES_BY_FILE.items():
        file_path = BACKEND_ROOT / Path(*rel_str.split("/"))
        if not file_path.exists():
            stale.append(f"{rel_str}: file does not exist")
            continue

        if not allowed_prefixes:
            # Empty allowlist is fine — just documents the file has no cross-context imports.
            continue

        imports = set(_imports_from_ast(file_path))

        for prefix in allowed_prefixes:
            if not any(imp.startswith(prefix) for imp in imports):
                stale.append(f"{rel_str}: allowlisted prefix '{prefix}' is never imported")

    assert not stale, (
        "Stale cross-context import allowlist entries found. "
        "Remove them to keep the allowlist honest:\n" + "\n".join(sorted(stale))
    )


# Directories that were fully drained during previous refactor phases.
# They must NOT be recreated.
FULLY_DRAINED_DIRECTORIES: list[str] = [
    "integrations",
    "schemas",
    "contexts/access_control",
    "domain_separation",
    "validators",
    "rbac_policy",
]


def test_fully_drained_directories_stay_deleted() -> None:
    """Directories that have been fully drained must not be recreated."""
    resurrected = [
        d for d in FULLY_DRAINED_DIRECTORIES
        if (BACKEND_ROOT / d).exists()
    ]
    assert not resurrected, (
        "Fully drained directories have been recreated. "
        "Do not add code to these deprecated locations:\n"
        + "\n".join(sorted(resurrected))
    )
