from __future__ import annotations

import ast
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
SERVICE_RECORDS_ROOT = BACKEND_ROOT / "contexts" / "service_book" / "records"


def _imports_from_ast(file_path: Path) -> list[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    return imported


def test_service_book_records_do_not_write_projection_collections_directly() -> None:
    violations: list[str] = []
    for file_path in SERVICE_RECORDS_ROOT.rglob("*.py"):
        if "__pycache__" in file_path.parts:
            continue
        rel = file_path.relative_to(BACKEND_ROOT).as_posix()
        source = file_path.read_text(encoding="utf-8")
        if "servicebook_entries" in source or "service_book_entries" in source:
            violations.append(f"{rel}: references ledger/projection collections")

    assert not violations, "Service Book records must not write projections directly:\n" + "\n".join(sorted(violations))


def test_service_book_records_repository_uses_official_record_collection() -> None:
    repository_file = SERVICE_RECORDS_ROOT / "repository" / "service_record_repository.py"
    source = repository_file.read_text(encoding="utf-8")

    assert "service_book_records" in source
    assert "service_book_record_streams" in source
    assert "service_event_records" not in source
    assert "service_event_streams" not in source
    assert "delete_many" not in source
    assert "_legacy_projection" not in source
    assert "self._db.service_events" not in source

