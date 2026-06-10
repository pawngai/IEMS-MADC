from __future__ import annotations

from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
READ_SIDE_API_ROOT = BACKEND_ROOT / "contexts" / "service_book" / "read_side" / "api"


def test_service_book_read_side_api_facade_stays_removed() -> None:
    removed = [
        READ_SIDE_API_ROOT / "__init__.py",
        READ_SIDE_API_ROOT / "router.py",
        READ_SIDE_API_ROOT / "query_router.py",
        READ_SIDE_API_ROOT / "print_router.py",
    ]

    lingering = [path.relative_to(BACKEND_ROOT).as_posix() for path in removed if path.exists()]
    assert not lingering, (
        "ServiceBook read-side API compatibility facades must stay deleted:\n"
        + "\n".join(lingering)
    )
