from __future__ import annotations

import ast
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
TARGET_FILES = [
    BACKEND_ROOT / "contexts" / "change_requests" / "application" / "service.py",
    BACKEND_ROOT / "contexts" / "leave_attendance" / "application" / "service.py",
    BACKEND_ROOT / "contexts" / "service_book" / "records" / "application" / "service.py",
]

MUTATION_VERBS = (
    "create",
    "update",
    "submit",
    "approve",
    "reject",
    "cancel",
    "patch",
    "save",
    "apply",
    "verify",
    "lock",
    "supersede",
)

READ_ONLY_METHOD_PREFIXES = ("get", "list", "read", "build", "generate")


def _has_outbox_or_gateway_publish(node: ast.AsyncFunctionDef) -> bool:
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        func = child.func
        if isinstance(func, ast.Attribute):
            if func.attr in {
                "_enqueue_event",
                "publish",
                "publish_raw",
                "_transition",
                "transition_to",
                "handle",
            }:
                return True
            if any(func.attr.startswith(verb) for verb in MUTATION_VERBS):
                return True
    return False


EXEMPT_METHODS = {
    "cancel_leave",
    "create_schema",
    "create_schema_version",
}


def test_state_changing_methods_emit_events() -> None:
    violations: list[str] = []

    for file_path in TARGET_FILES:
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
        rel = file_path.relative_to(BACKEND_ROOT).as_posix()
        for node in ast.walk(tree):
            if not isinstance(node, ast.AsyncFunctionDef):
                continue
            method_name = node.name.lower()
            if method_name.startswith("_"):
                continue
            if method_name in EXEMPT_METHODS:
                continue
            if method_name.startswith(READ_ONLY_METHOD_PREFIXES):
                continue
            if not any(method_name.startswith(verb) for verb in MUTATION_VERBS):
                continue
            if not _has_outbox_or_gateway_publish(node):
                violations.append(f"{rel}:{node.name}")

    assert not violations, (
        "State-changing methods must emit at least one outbox/gateway event:\n"
        + "\n".join(sorted(violations))
    )
