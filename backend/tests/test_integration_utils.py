from __future__ import annotations

from types import SimpleNamespace

import requests

from tests import integration_utils


def test_is_live_backend_accepts_api_health(monkeypatch) -> None:
    def _fake_get(url: str, timeout: float):
        assert timeout == 1.5
        if url.endswith("/api/health"):
            return SimpleNamespace(status_code=200)
        raise AssertionError(f"Unexpected URL probed: {url}")

    monkeypatch.setattr(integration_utils.requests, "get", _fake_get)
    assert integration_utils._is_live_backend("http://localhost:8000") is True


def test_is_live_backend_falls_back_to_live_probe(monkeypatch) -> None:
    def _fake_get(url: str, timeout: float):
        assert timeout == 1.5
        if url.endswith("/api/health"):
            raise requests.RequestException("legacy probe missing")
        if url.endswith("/health/live"):
            return SimpleNamespace(status_code=200)
        raise AssertionError(f"Unexpected URL probed: {url}")

    monkeypatch.setattr(integration_utils.requests, "get", _fake_get)
    assert integration_utils._is_live_backend("http://localhost:8000") is True


def test_is_live_backend_returns_false_when_all_probes_fail(monkeypatch) -> None:
    def _fake_get(url: str, timeout: float):
        raise requests.RequestException(f"unreachable: {url}")

    monkeypatch.setattr(integration_utils.requests, "get", _fake_get)
    assert integration_utils._is_live_backend("http://localhost:8000") is False
