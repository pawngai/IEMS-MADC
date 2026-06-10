from __future__ import annotations

import pytest

from contexts.system_admin.api import router as system_admin_router


@pytest.mark.asyncio
async def test_get_config_uses_identity_contract(monkeypatch) -> None:
    async def _fake_get_system_config(_db):
        return {"financial_year": "2026-27"}

    monkeypatch.setattr(system_admin_router, "identity_get_system_config", _fake_get_system_config)

    result = await system_admin_router.get_config(
        db=object(),
        current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
    )

    assert result == {"config": {"financial_year": "2026-27"}}


@pytest.mark.asyncio
async def test_update_config_persists_key_through_identity_contract(monkeypatch) -> None:
    captured = {}

    async def _fake_set_system_config_key(db, *, key, value, updated_by, reason):
        captured.update(
            {
                "db": db,
                "key": key,
                "value": value,
                "updated_by": updated_by,
                "reason": reason,
            }
        )
        return {key: value}

    monkeypatch.setattr(system_admin_router, "identity_set_system_config_key", _fake_set_system_config_key)

    payload = system_admin_router.SystemConfigUpdate(
        key="module_permissions",
        value={"matrix": {"SYSTEM_ADMIN": {"admin_console": True}}},
        reason="Enable module visibility management",
    )

    result = await system_admin_router.update_config(
        key="module_permissions",
        payload=payload,
        db="db-token",
        current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
    )

    assert captured["db"] == "db-token"
    assert captured["key"] == "module_permissions"
    assert captured["updated_by"] == "admin-1"
    assert captured["reason"] == "Enable module visibility management"
    assert result["status"] == "updated"
    assert result["key"] == "module_permissions"


@pytest.mark.asyncio
async def test_update_config_rejects_unsupported_key() -> None:
    payload = system_admin_router.SystemConfigUpdate(
        key="unknown_key",
        value="anything",
        reason="Attempt unsupported config write",
    )

    with pytest.raises(system_admin_router.HTTPException) as exc:
        await system_admin_router.update_config(
            key="unknown_key",
            payload=payload,
            db=object(),
            current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-2"},
        )

    assert exc.value.status_code == 400
    assert "Unsupported config key" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_update_config_rejects_invalid_module_permissions_shape() -> None:
    payload = system_admin_router.SystemConfigUpdate(
        key="module_permissions",
        value="invalid",
        reason="Reject malformed permissions payload",
    )

    with pytest.raises(system_admin_router.HTTPException) as exc:
        await system_admin_router.update_config(
            key="module_permissions",
            payload=payload,
            db=object(),
            current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-3"},
        )

    assert exc.value.status_code == 400
    assert "module_permissions must be an object" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_update_config_rejects_boolean_for_numeric_key() -> None:
    payload = system_admin_router.SystemConfigUpdate(
        key="session_timeout_minutes",
        value=True,
        reason="Reject boolean payload for numeric config",
    )

    with pytest.raises(system_admin_router.HTTPException) as exc:
        await system_admin_router.update_config(
            key="session_timeout_minutes",
            payload=payload,
            db=object(),
            current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-4"},
        )

    assert exc.value.status_code == 400
    assert "session_timeout_minutes must be an integer" in str(exc.value.detail)
