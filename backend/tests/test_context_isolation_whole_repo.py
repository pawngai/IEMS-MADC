from __future__ import annotations

import ast
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]

ALLOWED_NON_CONTEXT_INFRA_IMPORT_PREFIXES_BY_FILE: dict[str, set[str]] = {}


def _iter_py_files(root: Path):
    for file_path in root.rglob("*.py"):
        rel = file_path.relative_to(root).as_posix()
        if "__pycache__" in file_path.parts:
            continue
        if rel.startswith("tests/"):
            continue
        yield file_path


def _imports_from_ast(file_path: Path) -> list[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    return imported


def _is_allowlisted(rel_path: str, import_path: str) -> bool:
    allowed_prefixes = ALLOWED_NON_CONTEXT_INFRA_IMPORT_PREFIXES_BY_FILE.get(
        rel_path, set()
    )
    return any(import_path.startswith(prefix) for prefix in allowed_prefixes)


def test_backend_repo_wide_infrastructure_import_isolation() -> None:
    violations: list[str] = []

    for file_path in _iter_py_files(BACKEND_ROOT):
        rel = file_path.relative_to(BACKEND_ROOT)
        rel_str = rel.as_posix()
        imports = _imports_from_ast(file_path)

        file_context = None
        if rel.parts and rel.parts[0] == "contexts" and len(rel.parts) > 1:
            file_context = rel.parts[1]

        for imp in imports:
            if not imp.startswith("contexts."):
                continue
            segments = imp.split(".")
            if len(segments) < 3:
                continue
            target_context = segments[1]
            if "infrastructure" not in segments:
                continue

            if file_context == target_context:
                continue

            if _is_allowlisted(rel_str, imp):
                continue

            violations.append(f"{rel}: imports {imp}")

    assert not violations, (
        "Repo-wide infrastructure import isolation violations found:\n"
        + "\n".join(sorted(violations))
    )
