from __future__ import annotations

import ast
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]

# Canonical RBAC path for permission checks is rbac_policy.access_control.
# These deprecated helper modules are still used in a few migration hotspots.
# Keep existing imports stable, but fail CI if new call-sites are introduced.
DEPRECATED_AUTH_MODULE_ALLOWLIST: dict[str, set[str]] = {
    "shared.permissions": set(),
    "app.security.policy_enforcer": set(),
}


def _iter_py_files(root: Path):
    for file_path in root.rglob("*.py"):
        if "__pycache__" in file_path.parts:
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


def test_deprecated_authorization_imports_are_allowlisted() -> None:
    violations: list[str] = []

    for file_path in _iter_py_files(BACKEND_ROOT):
        rel = file_path.relative_to(BACKEND_ROOT).as_posix()
        imports = _imports_from_ast(file_path)

        for deprecated_module, allowlist in DEPRECATED_AUTH_MODULE_ALLOWLIST.items():
            if any(
                imp == deprecated_module or imp.startswith(f"{deprecated_module}.")
                for imp in imports
            ):
                if rel not in allowlist:
                    violations.append(
                        f"{rel}: imports deprecated auth helper '{deprecated_module}' (use rbac_policy.access_control)"
                    )

    assert not violations, "Unauthorized deprecated auth imports found:\n" + "\n".join(
        sorted(violations)
    )
