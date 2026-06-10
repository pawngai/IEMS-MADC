"""Production-hardening guards on app settings.

Covers the three production-only safety rules added to the Settings dataclass:

1. CORS_ORIGINS must be explicitly configured; localhost defaults are
   refused so a misconfigured production deploy fails fast at startup.
2. CORS_ORIGIN_REGEX defaults to empty (no LAN allowance) unless
   ``CORS_ALLOW_PRIVATE_NETWORK_REGEX=1`` is set.
3. Document local-disk fallback defaults to ``False`` in production so a
   broken GCS client never silently writes to the container filesystem.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app_platform.config.settings import Settings


def _env(monkeypatch, **values):
    # Wipe every env var that influences Settings so we get a clean slate.
    for key in (
        "ENVIRONMENT",
        "APP_ENV",
        "ENV",
        "CORS_ORIGINS",
        "CORS_ORIGIN_REGEX",
        "CORS_ALLOW_PRIVATE_NETWORK_REGEX",
        "DOCUMENT_STORAGE_BACKEND",
        "DOCUMENT_STORAGE_LOCAL_FALLBACK_ENABLED",
        "RATE_LIMIT_STORAGE_URI",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("JWT_SECRET", "ci-test-secret-minimum-32-characters-long")
    for key, value in values.items():
        monkeypatch.setenv(key, value)


def test_production_without_cors_origins_raises(monkeypatch) -> None:
    _env(monkeypatch, ENVIRONMENT="production")
    with pytest.raises(ValueError, match="CORS_ORIGINS must be explicitly configured"):
        Settings()


def test_production_with_wildcard_origin_raises(monkeypatch) -> None:
    _env(monkeypatch, ENVIRONMENT="production", CORS_ORIGINS="*")
    with pytest.raises(ValueError, match=r"CORS_ORIGINS='\*' is not allowed in production"):
        Settings()


def test_production_with_explicit_origins_succeeds(monkeypatch) -> None:
    _env(
        monkeypatch,
        ENVIRONMENT="production",
        CORS_ORIGINS="https://app.example.com,https://admin.example.com",
    )
    s = Settings()
    assert s.is_production is True
    assert s.cors_origins == ["https://app.example.com", "https://admin.example.com"]


def test_production_disables_private_network_regex_by_default(monkeypatch) -> None:
    _env(monkeypatch, ENVIRONMENT="production", CORS_ORIGINS="https://app.example.com")
    s = Settings()
    assert s.cors_origin_regex == ""


def test_production_can_opt_in_to_private_network_regex(monkeypatch) -> None:
    _env(
        monkeypatch,
        ENVIRONMENT="production",
        CORS_ORIGINS="https://app.example.com",
        CORS_ALLOW_PRIVATE_NETWORK_REGEX="1",
    )
    s = Settings()
    assert s.cors_origin_regex.startswith("^https?://")


def test_production_respects_explicit_cors_origin_regex(monkeypatch) -> None:
    _env(
        monkeypatch,
        ENVIRONMENT="production",
        CORS_ORIGINS="https://app.example.com",
        CORS_ORIGIN_REGEX=r"^https://[a-z0-9-]+\.example\.com$",
    )
    s = Settings()
    assert s.cors_origin_regex == r"^https://[a-z0-9-]+\.example\.com$"


def test_development_keeps_localhost_defaults(monkeypatch) -> None:
    _env(monkeypatch, ENVIRONMENT="development")
    s = Settings()
    assert any(o.startswith("http://localhost") for o in s.cors_origins)
    assert s.cors_origin_regex.startswith("^https?://")
    assert s.document_storage_local_fallback_enabled is True


def test_production_disables_document_local_fallback_by_default(monkeypatch) -> None:
    _env(
        monkeypatch,
        ENVIRONMENT="production",
        CORS_ORIGINS="https://app.example.com",
        DOCUMENT_STORAGE_BACKEND="gcs",
    )
    s = Settings()
    assert s.document_storage_local_fallback_enabled is False


def test_production_local_fallback_can_be_explicitly_enabled(monkeypatch) -> None:
    _env(
        monkeypatch,
        ENVIRONMENT="production",
        CORS_ORIGINS="https://app.example.com",
        DOCUMENT_STORAGE_BACKEND="gcs",
        DOCUMENT_STORAGE_LOCAL_FALLBACK_ENABLED="1",
    )
    s = Settings()
    assert s.document_storage_local_fallback_enabled is True


def test_rate_limit_storage_uri_is_env_driven(monkeypatch) -> None:
    _env(monkeypatch, RATE_LIMIT_STORAGE_URI="redis://localhost:6379/0")
    s = Settings()
    assert s.rate_limit_storage_uri == "redis://localhost:6379/0"


def test_rate_limit_storage_uri_defaults_empty(monkeypatch) -> None:
    _env(monkeypatch)
    s = Settings()
    assert s.rate_limit_storage_uri == ""
