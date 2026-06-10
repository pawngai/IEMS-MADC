from __future__ import annotations

from copy import deepcopy

import pytest

from app.bootstrap import dev_admin_sync
from contexts.identity_access.identity.infrastructure.auth_session_service import verify_password


class _FakeUsersCollection:
    def __init__(self, doc: dict | None = None) -> None:
        self.docs: dict[str, dict] = {}
        if doc is not None and doc.get("email"):
            self.docs[doc["email"]] = deepcopy(doc)
        self.update_calls: list[tuple[dict, dict, bool]] = []

    @property
    def doc(self) -> dict | None:
        if not self.docs:
            return None
        return deepcopy(next(iter(self.docs.values())))

    async def find_one(self, query: dict) -> dict | None:
        email = query.get("email")
        if not email:
            return None
        doc = self.docs.get(email)
        return deepcopy(doc) if doc is not None else None

    async def update_one(self, query: dict, update: dict, upsert: bool = False) -> None:
        self.update_calls.append((deepcopy(query), deepcopy(update), upsert))
        email = query.get("email")
        if email is None:
            return None
        doc = self.docs.get(email)
        if doc is None:
            doc = {"email": email}
            self.docs[email] = doc

        if upsert:
            for key, value in update.get("$setOnInsert", {}).items():
                doc.setdefault(key, value)
        for key, value in update.get("$set", {}).items():
            doc[key] = value
        return None


class _FakeDb:
    def __init__(self, user_doc: dict | None = None) -> None:
        self.users = _FakeUsersCollection(user_doc)


@pytest.mark.asyncio
async def test_sync_canonical_dev_admin_upserts_canonical_password(monkeypatch) -> None:
    monkeypatch.setenv("IEMS_SEED_ADMIN_PASSWORD", "ResetAdmin!2026")

    db = _FakeDb()

    changed = await dev_admin_sync.sync_canonical_dev_admin(db)

    assert changed is True
    assert db.users.doc is not None
    assert db.users.doc["email"] == "admin@madc.gov.in"
    assert db.users.doc["authorities"] == ["SYSTEM_ADMIN"]
    assert db.users.doc["failed_login_attempts"] == 0
    assert db.users.doc["locked_until"] is None
    assert verify_password("ResetAdmin!2026", db.users.doc["password_hash"])


@pytest.mark.asyncio
async def test_sync_canonical_dev_admin_clears_lockout_and_resets_password(monkeypatch) -> None:
    monkeypatch.setenv("IEMS_SEED_ADMIN_PASSWORD", "FreshAdmin!2026")

    db = _FakeDb(
        {
            "id": "admin-1",
            "email": "admin@madc.gov.in",
            "password_hash": dev_admin_sync.hash_password("OldAdmin!2025"),
            "authorities": ["SYSTEM_ADMIN"],
            "failed_login_attempts": 4,
            "locked_until": "2026-03-16T12:00:00+00:00",
            "is_active": True,
        }
    )

    changed = await dev_admin_sync.sync_canonical_dev_admin(db)

    assert changed is True
    assert db.users.doc is not None
    assert db.users.doc["id"] == "admin-1"
    assert db.users.doc["failed_login_attempts"] == 0
    assert db.users.doc["locked_until"] is None
    assert verify_password("FreshAdmin!2026", db.users.doc["password_hash"])


@pytest.mark.asyncio
async def test_sync_canonical_dev_admin_skips_without_database(monkeypatch) -> None:
    monkeypatch.setenv("IEMS_SEED_ADMIN_PASSWORD", "GeneratedAdmin!2026")

    db = None

    changed = await dev_admin_sync.sync_canonical_dev_admin(db)

    assert changed is False


@pytest.mark.asyncio
async def test_sync_canonical_dev_admin_skips_without_explicit_password(monkeypatch) -> None:
    monkeypatch.delenv("IEMS_SEED_ADMIN_PASSWORD", raising=False)

    db = _FakeDb()

    changed = await dev_admin_sync.sync_canonical_dev_admin(db)

    assert changed is False
    assert db.users.doc is None


@pytest.mark.asyncio
async def test_sync_canonical_dev_workflow_users_upserts_when_password_envs_present(monkeypatch) -> None:
    monkeypatch.setenv("IEMS_E2E_DE_PASSWORD", "dataentry123")
    monkeypatch.setenv("IEMS_E2E_VERIFIER_PASSWORD", "verifier123")
    monkeypatch.setenv("IEMS_E2E_ESTABLISHMENT_PASSWORD", "establishment123")
    monkeypatch.setenv("IEMS_E2E_HOO_PASSWORD", "hoo123")
    monkeypatch.setenv("IEMS_E2E_DEALING_PASSWORD", "dealing123")
    monkeypatch.setenv("IEMS_E2E_AUDITOR_PASSWORD", "auditor123")

    db = _FakeDb()

    changed = await dev_admin_sync.sync_canonical_dev_workflow_users(db)

    assert changed == 5
    assert verify_password("dataentry123", db.users.docs["global.dataentry@madc.gov.in"]["password_hash"])
    assert db.users.docs["global.dataentry@madc.gov.in"]["authorities"] == ["GLOBAL_DATA_ENTRY"]
    assert verify_password("verifier123", db.users.docs["verifier@madc.gov.in"]["password_hash"])
    assert db.users.docs["verifier@madc.gov.in"]["authorities"] == ["VERIFIER"]
    assert verify_password("auditor123", db.users.docs["auditor@madc.gov.in"]["password_hash"])
    assert db.users.docs["auditor@madc.gov.in"]["authorities"] == ["AUDITOR"]


@pytest.mark.asyncio
async def test_sync_canonical_dev_workflow_users_skips_when_password_envs_missing(monkeypatch) -> None:
    monkeypatch.delenv("IEMS_E2E_DE_PASSWORD", raising=False)
    monkeypatch.delenv("IEMS_E2E_VERIFIER_PASSWORD", raising=False)
    monkeypatch.delenv("IEMS_E2E_ESTABLISHMENT_PASSWORD", raising=False)
    monkeypatch.delenv("IEMS_E2E_HOO_PASSWORD", raising=False)
    monkeypatch.delenv("IEMS_E2E_DEALING_PASSWORD", raising=False)
    monkeypatch.delenv("IEMS_E2E_AUDITOR_PASSWORD", raising=False)

    db = _FakeDb()

    changed = await dev_admin_sync.sync_canonical_dev_workflow_users(db)

    assert changed == 0
    assert db.users.docs == {}
