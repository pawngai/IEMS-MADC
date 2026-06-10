from __future__ import annotations

from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_leave_gateway_uses_leave_ledger_collection() -> None:
    source = (
        BACKEND_ROOT / "contexts" / "leave" / "infrastructure" / "gateway.py"
    ).read_text(encoding="utf-8")
    repo_source = (
        BACKEND_ROOT / "contexts" / "leave" / "repository" / "leave_repository.py"
    ).read_text(encoding="utf-8")

    assert "LEAVE_LEDGER_COLLECTION = \"leave_ledger_entries\"" in source
    assert "self._db.leave_ledger_entries.update_one" in repo_source


def test_leave_gateway_is_ledger_only_after_cutover() -> None:
    source = (
        BACKEND_ROOT / "contexts" / "leave" / "repository" / "leave_repository.py"
    ).read_text(encoding="utf-8")

    assert "service_book_part_vi" not in source
    assert "self._db.service_book_part_vi.update_one" not in source
    assert "self._db.service_book_part_vi.insert_one" not in source


def test_leave_gateway_no_legacy_fallback_flag_remains() -> None:
    source = (
        BACKEND_ROOT / "contexts" / "leave" / "repository" / "leave_repository.py"
    ).read_text(encoding="utf-8")

    assert "allow_legacy_snapshot_fallback" not in source
    assert "get_legacy_part_vi_snapshot" not in source
