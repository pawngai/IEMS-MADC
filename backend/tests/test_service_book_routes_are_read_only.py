from __future__ import annotations

from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
SERVICE_BOOK_ROUTER = BACKEND_ROOT / "contexts" / "service_book" / "api" / "router.py"
SERVICE_BOOK_WRITE_ROUTER = BACKEND_ROOT / "contexts" / "service_book" / "api" / "write_router.py"
ROUTER_REGISTRY = BACKEND_ROOT / "app" / "bootstrap" / "router_registry.py"
SERVICE_BOOK_LEDGER_REGISTRATION = BACKEND_ROOT / "app" / "bootstrap" / "registrations" / "service_book_ledger.py"


def test_service_book_router_has_read_only_endpoints() -> None:
    source = SERVICE_BOOK_ROUTER.read_text(encoding="utf-8")
    assert "@service_book_router.post(" not in source
    assert "@service_book_router.patch(" not in source
    assert "@service_book_router.put(" not in source
    assert "@service_book_router.delete(" not in source
    assert "write_router" not in source
    assert "command_router" not in source


def test_service_book_write_router_is_removed() -> None:
    assert not SERVICE_BOOK_WRITE_ROUTER.exists()


def test_service_book_ledger_router_is_not_registered() -> None:
    source = ROUTER_REGISTRY.read_text(encoding="utf-8")
    assert "service_book_ledger" not in source
    assert not SERVICE_BOOK_LEDGER_REGISTRATION.exists()
