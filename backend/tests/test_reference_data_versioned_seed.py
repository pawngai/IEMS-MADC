from __future__ import annotations

from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest

from app.bootstrap import app_factory
from app_platform.reference_data.infrastructure.versioned_seed import (
    SYSTEM_SEED_CREATED_BY,
    seed_system_managed_masters,
)
from app_platform.reference_data.infrastructure.schemas import DEFAULT_EMPLOYMENT_TYPES
from app_platform.reference_data.infrastructure import service as reference_data_service
from app_platform.reference_data.contracts.employment_type_master import RETAINED_EMPLOYMENT_TYPE_CODES
from contexts.identity_access.rbac.domain.models import Authority, WorkflowStage


class _FakeCollection:
    def __init__(self, docs: list[dict] | None = None):
        self.docs = list(docs or [])

    async def find_one(self, query: dict, _projection: dict | None = None):
        for doc in self.docs:
            matches = True
            for key, value in query.items():
                if doc.get(key) != value:
                    matches = False
                    break
            if matches:
                return doc
        return None

    async def insert_one(self, doc: dict):
        self.docs.append(dict(doc))
        return None


class _FakeDb:
    def __init__(self):
        self._collections: dict[str, _FakeCollection] = {
            "master_audit_logs": _FakeCollection(),
        }

    def __getitem__(self, name: str):
        if name not in self._collections:
            self._collections[name] = _FakeCollection()
        return self._collections[name]

    @property
    def master_audit_logs(self):
        return self["master_audit_logs"]


@pytest.mark.asyncio
async def test_seed_system_managed_masters_populates_empty_collections() -> None:
    db = _FakeDb()

    result = await seed_system_managed_masters(db)

    assert result["employment_types"] > 0
    assert result["pay_levels"] > 0
    assert result["service_event_types"] > 0
    assert result["leave_types"] > 0
    assert result["roles"] == len(Authority)
    assert result["workflow_stages"] == len(WorkflowStage)
    assert result["document_types"] > 0
    assert result["qualifications"] > 0

    employment_type = db["employment_types"].docs[0]
    assert employment_type["version"] == 1
    assert employment_type["is_active"] is True
    assert employment_type["created_by"] == SYSTEM_SEED_CREATED_BY

    assert len(db.master_audit_logs.docs) == sum(result.values())


def test_default_employment_types_are_limited_to_retained_codes() -> None:
    codes = [record["code"] for record in DEFAULT_EMPLOYMENT_TYPES]

    assert codes == list(RETAINED_EMPLOYMENT_TYPE_CODES)


@pytest.mark.asyncio
async def test_get_employment_types_filters_legacy_database_records(monkeypatch) -> None:
    async def _fake_list_employment_types(_db):
        return [
            {"code": "REGULAR", "name": "Regular"},
            {"code": "CONTRACTUAL", "name": "Contractual"},
            {"code": "CONTRACT", "name": "Contract"},
            {"code": "MUSTER_ROLL", "name": "Muster Roll"},
            {"code": "DEPUTATION", "name": "Deputation"},
            {"code": "FIXED_PAY", "name": "Fixed Pay"},
            {"code": "OUTSOURCED", "name": "Outsourced"},
            {"code": "CO_TERMINUS", "name": "Co-Terminus"},
            {"code": "WAGES", "name": "Wages"},
        ]

    monkeypatch.setattr(reference_data_service.repo, "list_employment_types", _fake_list_employment_types)

    records = await reference_data_service.get_employment_types(object())

    assert [record["code"] for record in records] == list(RETAINED_EMPLOYMENT_TYPE_CODES)


@pytest.mark.asyncio
async def test_seed_system_managed_masters_is_idempotent() -> None:
    db = _FakeDb()

    first = await seed_system_managed_masters(db)
    second = await seed_system_managed_masters(db)

    assert sum(first.values()) > 0
    assert sum(second.values()) == 0
    assert len(db.master_audit_logs.docs) == sum(first.values())


@pytest.mark.asyncio
async def test_seed_system_managed_masters_respects_existing_codes() -> None:
    db = _FakeDb()
    db["employment_types"].docs.append(
        {
            "id": "existing-reg",
            "code": "REG",
            "name": "Regular",
            "description": "Regular",
            "metadata": {},
            "version": 1,
            "is_active": True,
            "created_at": "2026-01-01T00:00:00+00:00",
            "created_by": "manual",
            "superseded_by": None,
            "superseded_at": None,
        }
    )

    result = await seed_system_managed_masters(db)

    reg_records = [doc for doc in db["employment_types"].docs if doc["code"] == "REG"]
    assert len(reg_records) == 1
    assert result["employment_types"] >= 1


@pytest.mark.asyncio
async def test_app_lifespan_seeds_masters_on_startup(monkeypatch) -> None:
    seeded_with: list[object] = []
    db = object()

    @asynccontextmanager
    async def _fake_db_lifespan(app):
        app.state.db = db
        yield

    async def _fake_sync_admin(_db):
        return True

    async def _fake_sync_workflow(_db):
        return 0

    async def _fake_seed(_db):
        seeded_with.append(_db)
        return {"employment_types": 1}

    monkeypatch.setattr(app_factory, "db_lifespan", _fake_db_lifespan)
    monkeypatch.setattr(app_factory, "sync_canonical_dev_admin", _fake_sync_admin)
    monkeypatch.setattr(app_factory, "sync_canonical_dev_workflow_users", _fake_sync_workflow)
    monkeypatch.setattr(app_factory, "seed_system_managed_masters", _fake_seed)
    monkeypatch.setattr(
        app_factory,
        "wire_app_container",
        lambda _app: SimpleNamespace(outbox_dispatcher=None),
    )
    monkeypatch.setattr(app_factory, "register_app_subscribers", lambda _app: None)

    app = SimpleNamespace(state=SimpleNamespace())

    async with app_factory.app_lifespan(app):
        assert getattr(app.state, "db") is db

    assert seeded_with == [db]


@pytest.mark.asyncio
async def test_app_lifespan_skips_dev_account_sync_in_production(monkeypatch) -> None:
    calls: list[str] = []
    db = object()

    @asynccontextmanager
    async def _fake_db_lifespan(app):
        app.state.db = db
        yield

    async def _fake_sync_admin(_db):
        calls.append("admin")
        return True

    async def _fake_sync_workflow(_db):
        calls.append("workflow")
        return 0

    async def _fake_seed(_db):
        calls.append("seed")
        return {}

    monkeypatch.setattr(app_factory, "settings", SimpleNamespace(is_production=True))
    monkeypatch.setattr(app_factory, "db_lifespan", _fake_db_lifespan)
    monkeypatch.setattr(app_factory, "sync_canonical_dev_admin", _fake_sync_admin)
    monkeypatch.setattr(app_factory, "sync_canonical_dev_workflow_users", _fake_sync_workflow)
    monkeypatch.setattr(app_factory, "seed_system_managed_masters", _fake_seed)
    monkeypatch.setattr(
        app_factory,
        "wire_app_container",
        lambda _app: SimpleNamespace(outbox_dispatcher=None),
    )
    monkeypatch.setattr(app_factory, "register_app_subscribers", lambda _app: None)

    app = SimpleNamespace(state=SimpleNamespace())

    async with app_factory.app_lifespan(app):
        assert getattr(app.state, "db") is db

    assert calls == ["seed"]