from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timezone

import pytest
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.identity_access.identity.domain.module_access_policy import module_access_fallback
from contexts.identity_access.identity.infrastructure import auth_session_service
from contexts.identity_access.identity.infrastructure import activity_service
from contexts.identity_access.identity.infrastructure import service
from contexts.identity_access.identity.infrastructure import user_management_service
from contexts.identity_access.identity.contracts.schemas import UserCreate


@pytest.mark.asyncio
async def test_get_module_access_allow_all_when_db_unavailable() -> None:
    result = await service.get_module_access(
        None,
        {"authorities": ["DEPT_DATA_ENTRY"]},
    )

    assert result == {"mode": "allow_all", "allowed_modules": None}


def test_module_access_fallback_denies_by_default_in_production() -> None:
    assert module_access_fallback(SimpleNamespace(is_production=True)) == {
        "mode": "deny_by_default",
        "allowed_modules": [],
    }


@pytest.mark.asyncio
async def test_get_module_access_denies_by_default_when_production_config_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(auth_session_service, "settings", SimpleNamespace(is_production=True))

    result = await service.get_module_access(
        None,
        {"authorities": ["DEPT_DATA_ENTRY"]},
    )

    assert result == {
        "mode": "deny_by_default",
        "allowed_modules": ["data_entry", "ess_portal", "leave", "service_book"],
    }


@pytest.mark.asyncio
async def test_get_module_access_preserves_system_admin_defaults_when_production_config_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(auth_session_service, "settings", SimpleNamespace(is_production=True))

    result = await service.get_module_access(
        None,
        {"authorities": ["SYSTEM_ADMIN"]},
    )

    assert result == {
        "mode": "deny_by_default",
        "allowed_modules": [
            "admin_console",
            "audit",
            "department_management",
            "ess_portal",
            "leave",
            "service_book",
            "user_management",
        ],
    }


@pytest.mark.asyncio
async def test_get_module_access_keeps_hod_distinct_from_approving_authority(monkeypatch) -> None:
    async def _fake_get_system_config(_db):
        return {
            "module_permissions": {
                "matrix": {
                    "HOD": {"leave": True},
                    "APPROVING_AUTHORITY": {"audit": True},
                }
            }
        }

    monkeypatch.setattr(service.repo, "get_system_config", _fake_get_system_config)

    result = await service.get_module_access(
        object(),
        {"authorities": ["HOD"]},
    )

    assert result["mode"] == "config"
    assert result["allowed_modules"] == ["leave"]


@pytest.mark.asyncio
async def test_get_module_access_infers_verifier_baseline_when_production_config_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(auth_session_service, "settings", SimpleNamespace(is_production=True))

    result = await service.get_module_access(
        None,
        {"authorities": ["VERIFIER"]},
    )

    assert result == {
        "mode": "deny_by_default",
        "allowed_modules": ["ess_portal", "leave", "service_book", "verification"],
    }


@pytest.mark.asyncio
async def test_get_module_access_uses_config_as_source_of_truth(monkeypatch) -> None:
    async def _fake_get_system_config(_db):
        return {
            "module_permissions": {
                "matrix": {
                    "SYSTEM_ADMIN": {"audit": True},
                }
            }
        }

    monkeypatch.setattr(service.repo, "get_system_config", _fake_get_system_config)

    result = await service.get_module_access(
        object(),
        {"authorities": ["SYSTEM_ADMIN"]},
    )

    assert result["mode"] == "config"
    assert result["allowed_modules"] == ["audit"]


@pytest.mark.asyncio
async def test_get_module_access_config_can_disable_inferred_baseline(monkeypatch) -> None:
    async def _fake_get_system_config(_db):
        return {
            "module_permissions": {
                "matrix": {
                    "GLOBAL_DATA_ENTRY": {"data_entry": False},
                }
            }
        }

    monkeypatch.setattr(service.repo, "get_system_config", _fake_get_system_config)

    result = await service.get_module_access(
        object(),
        {"authorities": ["GLOBAL_DATA_ENTRY"]},
    )

    assert result == {"mode": "config", "allowed_modules": []}


@pytest.mark.asyncio
async def test_list_employee_directory_uses_profile_contracts(monkeypatch) -> None:
    async def _fake_list_profiles(_db, **kwargs):
        assert kwargs == {
            "search": "alice",
            "workflow_status": "APPROVED",
            "employment_type": "REGULAR",
            "department_code": "FIN",
            "designation_id": "DESIG-1",
            "office_id": "OFF-1",
            "employee_status": "ACTIVE",
            "recruitment_mode": "DIRECT",
            "pay_level": "L10",
            "service": "IAS",
            "service_group": "A",
            "date_from": "2026-01-01",
            "date_to": "2026-12-31",
            "limit": 25,
            "offset": 5,
            "sort_by": "employee_code",
            "sort_dir": "desc",
        }
        return [{"employee_id": "EMP-1", "full_name": "Alice"}]

    monkeypatch.setattr(user_management_service, "list_profiles", _fake_list_profiles)

    result = await user_management_service.list_employee_directory(
        object(),
        skip=5,
        limit=25,
        search="alice",
        department="FIN",
        employment_type="REGULAR",
        workflow_status="APPROVED",
        designation_id="DESIG-1",
        office_id="OFF-1",
        employee_status="ACTIVE",
        recruitment_mode="DIRECT",
        pay_level="L10",
        service="IAS",
        service_group="A",
        date_from="2026-01-01",
        date_to="2026-12-31",
        sort_by="employee_code",
        sort_dir="desc",
        current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
    )

    assert result == [{"employee_id": "EMP-1", "full_name": "Alice"}]


@pytest.mark.asyncio
async def test_get_employee_directory_count_uses_profile_contracts(monkeypatch) -> None:
    async def _fake_count_profiles(_db, **kwargs):
        assert kwargs == {
            "search": "alice",
            "workflow_status": "APPROVED",
            "employment_type": "REGULAR",
            "department_code": "FIN",
            "designation_id": "DESIG-1",
            "office_id": "OFF-1",
            "employee_status": "ACTIVE",
            "recruitment_mode": "DIRECT",
            "pay_level": "L10",
            "service": "IAS",
            "service_group": "A",
            "date_from": "2026-01-01",
            "date_to": "2026-12-31",
        }
        return 7

    monkeypatch.setattr(user_management_service, "count_employee_profiles", _fake_count_profiles)

    result = await user_management_service.get_employee_directory_count(
        object(),
        search="alice",
        department="FIN",
        employment_type="REGULAR",
        workflow_status="APPROVED",
        designation_id="DESIG-1",
        office_id="OFF-1",
        employee_status="ACTIVE",
        recruitment_mode="DIRECT",
        pay_level="L10",
        service="IAS",
        service_group="A",
        date_from="2026-01-01",
        date_to="2026-12-31",
        current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
    )

    assert result == {"count": 7}


@pytest.mark.asyncio
async def test_me_from_token_prefers_live_db_authorities(monkeypatch) -> None:
    async def _fake_find_user_by_email(_db, _email):
        return {
            "id": "u-1",
            "email": "live@example.com",
            "name": "Live User",
            "authorities": ["GLOBAL_DATA_ENTRY", "EMPLOYEE"],
            "employee_id": "EMP-10",
            "department_code": "FIN",
        }

    monkeypatch.setattr(service.repo, "find_user_by_email", _fake_find_user_by_email)
    monkeypatch.setattr(
        service,
        "get_permissions_for_authorities",
        lambda authorities: {f"perm:{a}" for a in authorities},
    )

    current_user = {
        "sub": "jwt-user",
        "email": "jwt@example.com",
        "name": "JWT User",
        "authorities": ["EMPLOYEE"],
    }

    result = await service.me_from_token(object(), current_user)

    assert result.id == "u-1"
    assert result.email == "live@example.com"
    assert result.authorities == ["GLOBAL_DATA_ENTRY", "EMPLOYEE"]
    assert set(result.permissions) == {"perm:GLOBAL_DATA_ENTRY", "perm:EMPLOYEE"}


@pytest.mark.asyncio
async def test_me_from_token_falls_back_to_jwt_when_user_not_found(monkeypatch) -> None:
    async def _fake_find_user_by_email(_db, _email):
        return None

    monkeypatch.setattr(service.repo, "find_user_by_email", _fake_find_user_by_email)

    current_user = {
        "sub": "jwt-user",
        "email": "jwt@example.com",
        "name": "JWT User",
        "authorities": ["EMPLOYEE"],
        "employee_id": "EMP-11",
        "department_code": "HR",
    }

    result = await service.me_from_token(object(), current_user)

    assert result.id == "jwt-user"
    assert result.email == "jwt@example.com"
    assert result.authorities == ["EMPLOYEE"]
    assert result.employee_id == "EMP-11"
    assert result.department_code == "HR"


class _FakeUsersCollection:
    def __init__(self) -> None:
        self.docs: list[dict] = []

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if self._matches(doc, query):
                return self._project(doc, projection)
        return None

    async def insert_one(self, doc: dict) -> None:
        self.docs.append(dict(doc))

    def _matches(self, doc: dict, query: dict) -> bool:
        for key, expected in query.items():
            actual = doc.get(key)
            if isinstance(expected, dict) and "$regex" in expected:
                flags = re.IGNORECASE if "i" in str(expected.get("$options", "")) else 0
                if not re.match(str(expected["$regex"]), str(actual or ""), flags):
                    return False
                continue
            if actual != expected:
                return False
        return True

    def _project(self, doc: dict, projection):
        result = dict(doc)
        if projection is None:
            return result

        include_fields = [
            field
            for field, enabled in projection.items()
            if field != "_id" and enabled
        ]
        if include_fields:
            result = {field: result.get(field) for field in include_fields if field in result}

        if projection.get("_id") == 0:
            result.pop("_id", None)
        return result


class _FakeDb:
    def __init__(self) -> None:
        self.users = _FakeUsersCollection()


@pytest.mark.asyncio
async def test_create_user_allows_non_system_admin_without_employee_link(monkeypatch) -> None:
    inserted: dict[str, str | list[str] | None] = {}

    monkeypatch.setattr(user_management_service, "require_system_admin", lambda _u: None)
    monkeypatch.setattr(user_management_service, "hash_password", lambda value: f"hashed::{value}")

    async def _fake_find_user_by_email(_db, _email):
        return None

    async def _fake_insert_user(_db, payload):
        inserted.update(payload)

    async def _fake_log_activity(*_args, **_kwargs):
        return {}

    async def _fake_find_users_with_authority(_db, _auth, *, exclude_user_id=None):
        return []

    monkeypatch.setattr(user_management_service.repo, "find_user_by_email", _fake_find_user_by_email)
    monkeypatch.setattr(user_management_service.repo, "insert_user", _fake_insert_user)
    monkeypatch.setattr(user_management_service.repo, "find_users_with_authority", _fake_find_users_with_authority)
    monkeypatch.setattr(user_management_service, "_log_activity", _fake_log_activity)

    result = await user_management_service.create_user(
        object(),
        UserCreate(
            email="linked.user@example.com",
            password="Password1!",
            name="Linked User",
            authorities=["EMPLOYEE"],
        ),
        current_user={"sub": "admin-1", "authorities": ["SYSTEM_ADMIN"]},
    )

    assert result.authorities == ["EMPLOYEE"]
    assert result.employee_id is None
    assert inserted["employee_id"] is None


@pytest.mark.asyncio
async def test_create_user_allows_system_admin_without_employee_link(monkeypatch) -> None:
    inserted: dict[str, str | list[str] | None] = {}

    monkeypatch.setattr(user_management_service, "require_system_admin", lambda _u: None)
    monkeypatch.setattr(user_management_service, "hash_password", lambda value: f"hashed::{value}")

    async def _fake_find_user_by_email(_db, _email):
        return None

    async def _fake_insert_user(_db, payload):
        inserted.update(payload)

    async def _fake_log_activity(*_args, **_kwargs):
        return {}

    monkeypatch.setattr(user_management_service.repo, "find_user_by_email", _fake_find_user_by_email)
    monkeypatch.setattr(user_management_service.repo, "insert_user", _fake_insert_user)
    monkeypatch.setattr(user_management_service, "_log_activity", _fake_log_activity)

    async def _fake_find_users_with_authority(_db, authority, *, exclude_user_id=None):
        return []

    monkeypatch.setattr(user_management_service.repo, "find_users_with_authority", _fake_find_users_with_authority)

    result = await user_management_service.create_user(
        object(),
        UserCreate(
            email="admin.only@example.com",
            password="Password1!",
            name="System Admin",
            authorities=["SYSTEM_ADMIN"],
        ),
        current_user={"sub": "admin-1", "authorities": ["SYSTEM_ADMIN"]},
    )

    assert result.authorities == ["SYSTEM_ADMIN"]
    assert result.employee_id is None
    assert inserted["employee_id"] is None


@pytest.mark.asyncio
async def test_provision_employee_account_creates_user_for_global_data_entry(monkeypatch) -> None:
    db = _FakeDb()

    async def _fake_find_identity(_db, *, employee_id: str, projection=None):
        assert projection == {"_id": 0}
        return {
            "employee_id": employee_id,
            "full_name": "Portal Employee",
            "current_department_id": "FIN",
            "date_of_birth": "1990-01-01",
            "workflow_status": "ACTIVE",
        }

    monkeypatch.setattr(user_management_service, "find_identity", _fake_find_identity)
    monkeypatch.setattr(user_management_service, "hash_password", lambda value: f"hashed::{value}")

    result = await user_management_service.provision_employee_account_for_employee(
        db,
        employee_id="EMP-2026-R0097",
        email="portal.employee@example.com",
        current_user={
            "sub": "gdo-1",
            "authorities": ["GLOBAL_DATA_ENTRY"],
        },
    )

    assert result["employee_id"] == "EMP-2026-R0097"
    assert result["email"] == "portal.employee@example.com"
    assert result["already_exists"] is False
    assert result["linked_existing_user"] is False
    assert result["must_change_password"] is True
    assert result["temp_password"]

    assert len(db.users.docs) == 1
    created_user = db.users.docs[0]
    assert created_user["employee_id"] == "EMP-2026-R0097"
    assert created_user["email"] == "portal.employee@example.com"
    assert created_user["department_code"] == "FIN"
    assert created_user["authorities"] == ["EMPLOYEE"]


@pytest.mark.asyncio
async def test_provision_employee_account_allows_system_admin(monkeypatch) -> None:
    db = _FakeDb()

    async def _fake_find_identity(_db, *, employee_id: str, projection=None):
        assert projection == {"_id": 0}
        return {
            "employee_id": employee_id,
            "full_name": "Portal Employee",
            "current_department_id": "FIN",
            "date_of_birth": "1990-01-01",
            "workflow_status": "ACTIVE",
        }

    monkeypatch.setattr(user_management_service, "find_identity", _fake_find_identity)
    monkeypatch.setattr(user_management_service, "hash_password", lambda value: f"hashed::{value}")

    result = await user_management_service.provision_employee_account_for_employee(
        db,
        employee_id="EMP-2026-R0098",
        email="admin.portal.employee@example.com",
        current_user={
            "sub": "admin-1",
            "authorities": ["SYSTEM_ADMIN"],
        },
    )

    assert result["employee_id"] == "EMP-2026-R0098"
    assert result["email"] == "admin.portal.employee@example.com"
    assert result["already_exists"] is False
    assert result["linked_existing_user"] is False
    assert result["must_change_password"] is True
    assert result["temp_password"]


@pytest.mark.asyncio
async def test_provision_employee_account_rejects_department_data_entry(monkeypatch) -> None:
    db = _FakeDb()

    async def _unexpected_find_identity(*_args, **_kwargs):
        raise AssertionError("identity lookup should not run for unauthorized caller")

    monkeypatch.setattr(user_management_service, "find_identity", _unexpected_find_identity)

    with pytest.raises(Exception) as exc_info:
        await user_management_service.provision_employee_account_for_employee(
            db,
            employee_id="EMP-2026-R0099",
            email="dept.employee@example.com",
            current_user={
                "sub": "dde-1",
                "authorities": ["DEPT_DATA_ENTRY"],
            },
        )

    exc = exc_info.value
    assert getattr(exc, "status_code", None) == 403
    detail = getattr(exc, "detail", {})
    assert detail["error_code"] == "ACCOUNT_PROVISIONING_FORBIDDEN"
    assert "GLOBAL_DATA_ENTRY" in detail["required_authorities"]
    assert "SYSTEM_ADMIN" in detail["required_authorities"]


@pytest.mark.asyncio
async def test_provision_employee_account_requires_active_identity(monkeypatch) -> None:
    db = _FakeDb()

    async def _fake_find_identity(_db, *, employee_id: str, projection=None):
        return {
            "employee_id": employee_id,
            "full_name": "Draft Employee",
            "current_department_id": "FIN",
            "date_of_birth": "1990-01-01",
            "workflow_status": "DRAFT",
        }

    monkeypatch.setattr(user_management_service, "find_identity", _fake_find_identity)

    with pytest.raises(Exception) as exc_info:
        await user_management_service.provision_employee_account_for_employee(
            db,
            employee_id="EMP-2026-R0100",
            email="draft.employee@example.com",
            current_user={
                "sub": "gdo-1",
                "authorities": ["GLOBAL_DATA_ENTRY"],
            },
        )

    exc = exc_info.value
    assert getattr(exc, "status_code", None) == 409
    assert "identity is ACTIVE" in str(getattr(exc, "detail", ""))


@pytest.mark.asyncio
async def test_reset_employee_temp_password_clears_lockout_state(monkeypatch) -> None:
    captured_update: dict[str, object] = {}
    revoked_user_ids: list[str] = []

    async def _fake_find_user_by_email(_db, _email):
        return {
            "id": "user-1",
            "email": "employee@example.com",
            "authorities": ["EMPLOYEE"],
            "failed_login_attempts": 5,
            "locked_until": "2026-03-15T12:15:00+00:00",
        }

    async def _fake_update_user(_db, _user_id, payload):
        captured_update.update(payload)

    async def _fake_revoke_all_refresh_tokens(_db, user_id):
        revoked_user_ids.append(user_id)

    monkeypatch.setattr(user_management_service.repo, "find_user_by_email", _fake_find_user_by_email)
    monkeypatch.setattr(user_management_service.repo, "update_user", _fake_update_user)
    monkeypatch.setattr(
        user_management_service,
        "_revoke_all_refresh_tokens",
        _fake_revoke_all_refresh_tokens,
    )
    monkeypatch.setattr(
        user_management_service,
        "hash_password",
        lambda value: f"hashed::{value}",
    )

    result = await user_management_service.reset_employee_temp_password(
        object(),
        "employee@example.com",
        current_user={
            "sub": "admin-1",
            "authorities": ["SYSTEM_ADMIN"],
        },
    )

    assert result["email"] == "employee@example.com"
    assert result["temp_password"].startswith("Reset@")
    assert captured_update["must_change_password"] is True
    assert captured_update["failed_login_attempts"] == 0
    assert captured_update["locked_until"] is None
    assert captured_update["password_hash"] == f"hashed::{result['temp_password']}"
    assert revoked_user_ids == ["user-1"]


@pytest.mark.asyncio
async def test_get_role_change_stats_computes_weekly_slice_separately(monkeypatch) -> None:
    fixed_now = datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc)

    class _FixedDateTime:
        @staticmethod
        def now(tz=None):
            if tz is None:
                return fixed_now.replace(tzinfo=None)
            return fixed_now.astimezone(tz)

        @staticmethod
        def fromtimestamp(ts, tz=None):
            return datetime.fromtimestamp(ts, tz=tz)

    seen_match_windows: list[str] = []

    async def _fake_aggregate_role_change_stats(_db, pipeline):
        since_iso = pipeline[0]["$match"]["timestamp"]["$gte"]
        seen_match_windows.append(since_iso)
        if since_iso == "2026-03-08T12:00:00+00:00":
            return [{"_id": "grant", "count": 3}, {"_id": "revoke", "count": 1}]
        if since_iso == "2026-02-13T12:00:00+00:00":
            return [{"_id": "grant", "count": 8}, {"_id": "revoke", "count": 4}]
        raise AssertionError(f"Unexpected stats window: {since_iso}")

    monkeypatch.setattr(activity_service, "datetime", _FixedDateTime)
    monkeypatch.setattr(
        activity_service.repo,
        "aggregate_role_change_stats",
        _fake_aggregate_role_change_stats,
    )

    result = await service.get_role_change_stats(
        object(),
        days=30,
        current_user={"authorities": ["SYSTEM_ADMIN"]},
    )

    assert result == {
        "days": 30,
        "stats": [{"_id": "grant", "count": 8}, {"_id": "revoke", "count": 4}],
        "total_changes": 12,
        "changes_last_7_days": 4,
    }
    assert seen_match_windows == [
        "2026-02-13T12:00:00+00:00",
        "2026-03-08T12:00:00+00:00",
    ]
