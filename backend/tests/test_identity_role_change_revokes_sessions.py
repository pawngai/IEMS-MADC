from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.identity.contracts.schemas import AuthorityPatch, UserUpdate
from contexts.identity.infrastructure import user_management_service


async def _fake_empty_list(*_args, **_kwargs):
    return []


@pytest.mark.asyncio
async def test_update_user_revokes_refresh_tokens_when_authorities_change(monkeypatch) -> None:
    current_user = {"sub": "admin-1", "authorities": ["SYSTEM_ADMIN"]}

    original_user = {
        "id": "user-1",
        "email": "person@example.com",
        "name": "Person",
        "authorities": ["EMPLOYEE"],
        "employee_id": "EMP-100",
        "is_active": True,
    }
    updated_user = {
        "id": "user-1",
        "email": "person@example.com",
        "name": "Person",
        "authorities": ["GLOBAL_DATA_ENTRY"],
        "employee_id": "EMP-100",
        "is_active": True,
    }

    calls = {"revoke": 0, "update": 0}

    async def _fake_find_user_by_id(_db, _user_id, projection=None):
        if projection is None:
            return original_user
        return updated_user

    async def _fake_update_user(_db, _user_id, _payload):
        calls["update"] += 1

    async def _fake_log_activity(*_args, **_kwargs):
        return {}

    async def _fake_log_role_change(*_args, **_kwargs):
        return {}

    async def _fake_revoke_all_refresh_tokens(_db, _user_id):
        calls["revoke"] += 1

    async def _fake_find_identity(_db, *, employee_id: str, projection=None):
        assert employee_id == "EMP-100"
        return {"employee_id": employee_id, "current_department_id": "FIN"}

    monkeypatch.setattr(user_management_service, "require_system_admin", lambda _u: None)
    monkeypatch.setattr(user_management_service, "prevent_self_action", lambda *_a, **_k: None)
    monkeypatch.setattr(user_management_service.repo, "find_user_by_id", _fake_find_user_by_id)
    monkeypatch.setattr(user_management_service.repo, "update_user", _fake_update_user)
    monkeypatch.setattr(user_management_service.repo, "find_users_with_authority", lambda *_a, **_k: _fake_empty_list())
    monkeypatch.setattr(user_management_service, "_log_activity", _fake_log_activity)
    monkeypatch.setattr(user_management_service, "_log_role_change", _fake_log_role_change)
    monkeypatch.setattr(user_management_service, "_revoke_all_refresh_tokens", _fake_revoke_all_refresh_tokens)
    monkeypatch.setattr(user_management_service, "find_identity", _fake_find_identity)

    result = await user_management_service.update_user(
        object(),
        "user-1",
        UserUpdate(authorities=["GLOBAL_DATA_ENTRY"]),
        current_user=current_user,
    )

    assert result.authorities == ["GLOBAL_DATA_ENTRY"]
    assert calls["update"] == 1
    assert calls["revoke"] == 1


@pytest.mark.asyncio
async def test_patch_user_authorities_revokes_refresh_tokens_when_changed(monkeypatch) -> None:
    current_user = {"sub": "admin-1", "authorities": ["SYSTEM_ADMIN"]}

    original_user = {
        "id": "user-2",
        "email": "person2@example.com",
        "name": "Person Two",
        "authorities": ["EMPLOYEE"],
        "employee_id": "EMP-200",
        "is_active": True,
    }
    patched_user = {
        "id": "user-2",
        "email": "person2@example.com",
        "name": "Person Two",
        "authorities": ["EMPLOYEE", "GLOBAL_DATA_ENTRY"],
        "employee_id": "EMP-200",
        "is_active": True,
    }

    calls = {"revoke": 0}

    async def _fake_find_user_by_id(_db, _user_id):
        return original_user

    async def _fake_patch_user_authorities(_db, _user_id, add=None, remove=None, extra_set=None):
        assert add == ["GLOBAL_DATA_ENTRY"]
        assert remove is None
        assert isinstance(extra_set, dict)
        return patched_user

    async def _fake_log_role_change(*_args, **_kwargs):
        return {}

    async def _fake_revoke_all_refresh_tokens(_db, _user_id):
        calls["revoke"] += 1

    async def _fake_find_identity(_db, *, employee_id: str, projection=None):
        assert employee_id == "EMP-200"
        return {"employee_id": employee_id, "current_department_id": "FIN"}

    monkeypatch.setattr(user_management_service, "require_system_admin", lambda _u: None)
    monkeypatch.setattr(user_management_service.repo, "find_user_by_id", _fake_find_user_by_id)
    monkeypatch.setattr(
        user_management_service.repo,
        "patch_user_authorities",
        _fake_patch_user_authorities,
    )
    monkeypatch.setattr(user_management_service.repo, "find_users_with_authority", lambda *_a, **_k: _fake_empty_list())
    monkeypatch.setattr(user_management_service, "_log_role_change", _fake_log_role_change)
    monkeypatch.setattr(user_management_service, "_revoke_all_refresh_tokens", _fake_revoke_all_refresh_tokens)
    monkeypatch.setattr(user_management_service, "find_identity", _fake_find_identity)

    result = await user_management_service.patch_user_authorities(
        object(),
        "user-2",
        AuthorityPatch(add=["GLOBAL_DATA_ENTRY"]),
        current_user=current_user,
    )

    assert sorted(result.authorities) == ["EMPLOYEE", "GLOBAL_DATA_ENTRY"]
    assert calls["revoke"] == 1


@pytest.mark.asyncio
async def test_update_user_allows_non_system_admin_without_employee_link(monkeypatch) -> None:
    current_user = {"sub": "admin-1", "authorities": ["SYSTEM_ADMIN"]}

    original_user = {
        "id": "user-3",
        "email": "admin.user@example.com",
        "name": "Admin User",
        "authorities": ["SYSTEM_ADMIN"],
        "employee_id": None,
        "is_active": True,
    }
    updated_user = {
        **original_user,
        "authorities": ["EMPLOYEE"],
    }

    calls = {"update": 0}

    async def _fake_find_user_by_id(_db, _user_id, projection=None):
        if projection is None:
            return original_user
        return updated_user

    async def _fake_update_user(_db, _user_id, _payload):
        calls["update"] += 1

    async def _fake_log_activity(*_args, **_kwargs):
        return {}

    async def _fake_log_role_change(*_args, **_kwargs):
        return {}

    async def _fake_revoke_all_refresh_tokens(*_args, **_kwargs):
        return None

    monkeypatch.setattr(user_management_service, "require_system_admin", lambda _u: None)
    monkeypatch.setattr(user_management_service.repo, "find_user_by_id", _fake_find_user_by_id)
    monkeypatch.setattr(user_management_service.repo, "update_user", _fake_update_user)
    monkeypatch.setattr(user_management_service, "_log_activity", _fake_log_activity)
    monkeypatch.setattr(user_management_service, "_log_role_change", _fake_log_role_change)
    monkeypatch.setattr(user_management_service, "_revoke_all_refresh_tokens", _fake_revoke_all_refresh_tokens)

    result = await user_management_service.update_user(
        object(),
        "user-3",
        UserUpdate(authorities=["EMPLOYEE"]),
        current_user=current_user,
    )

    assert result.authorities == ["EMPLOYEE"]
    assert result.employee_id is None
    assert calls["update"] == 1


@pytest.mark.asyncio
async def test_patch_user_authorities_allows_non_system_admin_without_employee_link(monkeypatch) -> None:
    current_user = {"sub": "admin-1", "authorities": ["SYSTEM_ADMIN"]}

    original_user = {
        "id": "user-4",
        "email": "admin.patch@example.com",
        "name": "Patch Admin",
        "authorities": ["SYSTEM_ADMIN"],
        "employee_id": None,
        "is_active": True,
    }
    patched_user = {
        **original_user,
        "authorities": [],
    }

    async def _fake_find_user_by_id(_db, _user_id):
        return original_user

    async def _fake_patch_user_authorities(_db, _user_id, add=None, remove=None, extra_set=None):
        assert add is None
        assert remove == ["SYSTEM_ADMIN"]
        assert isinstance(extra_set, dict)
        return patched_user

    async def _fake_log_role_change(*_args, **_kwargs):
        return {}

    async def _fake_revoke_all_refresh_tokens(*_args, **_kwargs):
        return None

    monkeypatch.setattr(user_management_service, "require_system_admin", lambda _u: None)
    monkeypatch.setattr(user_management_service.repo, "find_user_by_id", _fake_find_user_by_id)
    monkeypatch.setattr(
        user_management_service.repo,
        "patch_user_authorities",
        _fake_patch_user_authorities,
    )
    monkeypatch.setattr(user_management_service, "_log_role_change", _fake_log_role_change)
    monkeypatch.setattr(user_management_service, "_revoke_all_refresh_tokens", _fake_revoke_all_refresh_tokens)

    result = await user_management_service.patch_user_authorities(
        object(),
        "user-4",
        AuthorityPatch(remove=["SYSTEM_ADMIN"]),
        current_user=current_user,
    )

    assert result.authorities == []
    assert result.employee_id is None
