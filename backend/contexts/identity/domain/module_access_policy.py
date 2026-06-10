from __future__ import annotations

from typing import Any


ALLOW_ALL_MODULE_ACCESS = {"mode": "allow_all", "allowed_modules": None}
DENY_BY_DEFAULT_MODULE_ACCESS = {"mode": "deny_by_default", "allowed_modules": []}


def module_access_fallback(app_settings: Any) -> dict:
    """Return the safe fallback used when module-access config is unavailable.

    Development and tests can continue to run with permissive module access
    when configuration has not been created yet. Production must fail closed so
    missing database/configuration cannot silently expose optional modules.
    """

    if bool(getattr(app_settings, "is_production", False)):
        return dict(DENY_BY_DEFAULT_MODULE_ACCESS)
    return dict(ALLOW_ALL_MODULE_ACCESS)


def normalize_module_access_config(config: dict | None) -> dict | None:
    module_permissions = (config or {}).get("module_permissions") or {}
    if not isinstance(module_permissions, dict):
        return None

    matrix = module_permissions.get("matrix") or {}
    if not isinstance(matrix, dict) or not matrix:
        return None

    return matrix
