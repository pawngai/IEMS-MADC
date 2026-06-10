from __future__ import annotations

import ast
import re
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
CONTEXTS_ROOT = BACKEND_ROOT / "contexts"


def _iter_python_files(root: Path):
    for file_path in root.rglob("*.py"):
        if "__pycache__" in file_path.parts:
            continue
        yield file_path


def _is_exempt_path(rel_path: str) -> bool:
    if rel_path.startswith("tests/"):
        return True
    if rel_path.endswith("/legacy_service.py"):
        return True
    return False


def _imports_from_ast(file_path: Path) -> list[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    return imported


def test_no_new_production_legacy_service_imports() -> None:
    violations: list[str] = []

    for file_path in _iter_python_files(BACKEND_ROOT):
        rel = file_path.relative_to(BACKEND_ROOT)
        rel_str = rel.as_posix()
        if _is_exempt_path(rel_str):
            continue

        imports = _imports_from_ast(file_path)
        for imp in imports:
            if ".legacy_service" in imp:
                violations.append(f"{rel}: imports {imp}")

        text = file_path.read_text(encoding="utf-8")
        dynamic_refs = re.findall(r"contexts\.[a-zA-Z0-9_\.]*legacy_service", text)
        if dynamic_refs:
            for ref in sorted(set(dynamic_refs)):
                violations.append(f"{rel}: dynamic reference {ref}")

    assert not violations, (
        "Production files must not import legacy_service modules directly. "
        "Keep legacy references confined to compatibility wrappers/tests only:\n"
        + "\n".join(sorted(violations))
    )


def test_no_legacy_service_modules_remain() -> None:
    legacy_files = [
        path.relative_to(BACKEND_ROOT).as_posix()
        for path in CONTEXTS_ROOT.rglob("legacy_service.py")
        if "__pycache__" not in path.parts
    ]
    assert not legacy_files, (
        "No legacy_service modules should remain after cutover:\n"
        + "\n".join(sorted(legacy_files))
    )


def test_no_legacy_named_python_modules_remain() -> None:
    legacy_named = [
        path.relative_to(BACKEND_ROOT).as_posix()
        for path in BACKEND_ROOT.rglob("legacy_*.py")
        if "__pycache__" not in path.parts and not path.relative_to(BACKEND_ROOT).as_posix().startswith("tests/")
    ]
    assert not legacy_named, (
        "No legacy_*.py modules should remain in backend production paths:\n"
        + "\n".join(sorted(legacy_named))
    )
