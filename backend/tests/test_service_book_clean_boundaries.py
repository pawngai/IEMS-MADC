from __future__ import annotations

import ast
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
SERVICE_BOOK_ROOT = BACKEND_ROOT / "contexts" / "service_book"


def _python_files(root: Path):
    for path in root.rglob("*.py"):
        if "__pycache__" not in path.parts:
            yield path


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def test_service_book_api_does_not_access_mongo_directly() -> None:
    violations: list[str] = []
    for root in (SERVICE_BOOK_ROOT / "api", SERVICE_BOOK_ROOT / "read_side" / "api"):
        for path in _python_files(root):
            source = path.read_text(encoding="utf-8-sig")
            for token in (
                ".insert_one(",
                ".update_one(",
                ".delete_one(",
                ".delete_many(",
                ".replace_one(",
                ".find_one(",
                ".find(",
                "db.service_book_",
                "request.app.state.db",
            ):
                if token in source:
                    violations.append(f"{path.relative_to(BACKEND_ROOT).as_posix()}: {token}")
    assert not violations, "ServiceBook API routers must delegate persistence:\n" + "\n".join(violations)


def test_service_book_domain_does_not_import_fastapi() -> None:
    violations = [
        path.relative_to(BACKEND_ROOT).as_posix()
        for path in _python_files(SERVICE_BOOK_ROOT / "domain")
        for module in _imports(path)
        if module == "fastapi" or module.startswith("fastapi.")
    ]
    assert not violations, "ServiceBook domain must stay framework-free:\n" + "\n".join(violations)


def test_service_book_uses_profile_contracts_not_profile_application() -> None:
    violations = [
        path.relative_to(BACKEND_ROOT).as_posix()
        for path in _python_files(SERVICE_BOOK_ROOT)
        for module in _imports(path)
        if module == "contexts.employee_master.profile.application"
        or module.startswith("contexts.employee_master.profile.application.")
    ]
    assert not violations, "ServiceBook must depend on employee_profile contracts only:\n" + "\n".join(violations)


def test_service_book_repositories_do_not_import_leave_contracts() -> None:
    checked_roots = [
        SERVICE_BOOK_ROOT / "repository",
        SERVICE_BOOK_ROOT / "contracts",
    ]
    violations = [
        path.relative_to(BACKEND_ROOT).as_posix()
        for root in checked_roots
        for path in _python_files(root)
        for module in _imports(path)
        if module == "contexts.leave.contracts" or module.startswith("contexts.leave.contracts.")
    ]
    assert not violations, "Leave integration belongs in ServiceBook read-side projectors:\n" + "\n".join(violations)


def test_service_book_has_no_command_workflow_modules() -> None:
    removed_paths = [
        SERVICE_BOOK_ROOT / "api" / "command_router.py",
        SERVICE_BOOK_ROOT / "application" / "dto" / "commands.py",
        SERVICE_BOOK_ROOT / "application" / "services" / "manual_entry_service.py",
    ]
    removed_paths.extend((SERVICE_BOOK_ROOT / "application" / "commands").glob("*.py"))
    violations = [
        path.relative_to(BACKEND_ROOT).as_posix()
        for path in removed_paths
        if path.exists()
    ]
    assert not violations, "ServiceBook command workflow modules were removed:\n" + "\n".join(violations)


def test_service_book_application_services_do_not_update_projection_collection() -> None:
    checked_roots = [
        SERVICE_BOOK_ROOT / "application" / "services",
    ]
    violations: list[str] = []
    for root in checked_roots:
        for path in _python_files(root):
            source = path.read_text(encoding="utf-8-sig")
            for token in (
                "service_book_part_projections",
                "upsert_part_projection(",
                "upsert_projection_patch(",
            ):
                if token in source:
                    violations.append(f"{path.relative_to(BACKEND_ROOT).as_posix()}: {token}")
    assert not violations, (
        "ServiceBook command workflow must emit events; projection writes belong to read-side projectors:\n"
        + "\n".join(violations)
    )


def test_service_book_runtime_code_does_not_delete_ledger_or_projection_rows() -> None:
    allowed_parts = {"scripts", "tests"}
    violations: list[str] = []
    for path in BACKEND_ROOT.rglob("*.py"):
        rel_parts = set(path.relative_to(BACKEND_ROOT).parts)
        if rel_parts & allowed_parts or "__pycache__" in path.parts:
            continue
        source = path.read_text(encoding="utf-8-sig")
        if "service_book_entries.delete" in source or "service_book_part_projections.delete" in source:
            violations.append(path.relative_to(BACKEND_ROOT).as_posix())
    assert not violations, "ServiceBook ledger/projection hard deletes are script-only:\n" + "\n".join(violations)


def test_service_book_projection_status_collection_is_owned() -> None:
    from app_platform.domain_separation.data_ownership import owner_for_collection

    assert owner_for_collection("service_book_projection_status") == "service_book"


def test_service_book_legacy_workflow_collection_is_read_only() -> None:
    repository = SERVICE_BOOK_ROOT / "repository" / "mongo_entry_repository.py"
    source = repository.read_text(encoding="utf-8-sig")
    assert "service_book_workflow_entries" in source
    assert "def _workflow_entries" in source
    assert "def _projected_entries" in source
    assert "insert_entry" not in source
    assert "update_entry" not in source
    start = source.index("    async def list_queue_entries")
    next_method = source.find("\n    async def ", start + 1)
    method_source = source[start: next_method if next_method != -1 else len(source)]
    assert "_workflow_entries" in method_source
    assert "_projected_entries" not in method_source
