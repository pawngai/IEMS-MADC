"""Phase 1b guardrail: employee_master expand/contract cutover correctness.

Verifies the dual-write + read-switch behavior of the read-model repository:
- dual_write ON  -> projection writes mirror into the employee_master collection
- read ON        -> composed reads prefer employee_master, fall back to the
                    legacy read model when employee_master has no doc
- flags OFF      -> behavior is exactly the legacy read-model path
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import contexts.employee_master.profile.read_model.infrastructure.repository as repo_module
from contexts.employee_master.profile.read_model.infrastructure.repository import (
    EmployeeProfileReadModelRepository,
)


class _FakeCollection:
    def __init__(self):
        self.docs: dict[str, dict] = {}

    async def update_one(self, flt, update, upsert=False):
        emp = flt["employee_id"]
        doc = self.docs.get(emp, {})
        doc.update(update.get("$set", {}))
        if emp not in self.docs:
            doc.update(update.get("$setOnInsert", {}))
        self.docs[emp] = doc

    async def find_one(self, flt, projection=None):
        return self.docs.get(flt["employee_id"])

    async def count_documents(self, query):
        return len(self.docs)

    def find(self, query, projection=None):
        items = list(self.docs.values())
        return _FakeCursor(items)


class _FakeCursor:
    def __init__(self, items):
        self._items = items

    def skip(self, n):
        self._items = self._items[n:]
        return self

    def limit(self, n):
        self._items = self._items[:n]
        return self

    async def to_list(self, length=None):
        return self._items


class _FakeDb:
    def __init__(self):
        self.employee_profile_read_models = _FakeCollection()
        self.employee_master = _FakeCollection()
        self.employee_identities = _FakeCollection()


def _flags(monkeypatch, *, dual_write: bool, read: bool):
    monkeypatch.setattr(
        repo_module,
        "settings",
        SimpleNamespace(employee_master_dual_write=dual_write, employee_master_read=read),
    )


@pytest.mark.asyncio
async def test_dual_write_mirrors_into_employee_master(monkeypatch):
    _flags(monkeypatch, dual_write=True, read=False)
    db = _FakeDb()
    repo = EmployeeProfileReadModelRepository(db=db)

    await repo.upsert_projection(employee_id="E1", projection={"full_name": "Alice"})

    assert db.employee_profile_read_models.docs["E1"]["full_name"] == "Alice"
    assert db.employee_master.docs["E1"]["full_name"] == "Alice"  # mirrored


@pytest.mark.asyncio
async def test_dual_write_off_does_not_touch_employee_master(monkeypatch):
    _flags(monkeypatch, dual_write=False, read=False)
    db = _FakeDb()
    repo = EmployeeProfileReadModelRepository(db=db)

    await repo.upsert_projection(employee_id="E1", projection={"full_name": "Bob"})

    assert "E1" in db.employee_profile_read_models.docs
    assert db.employee_master.docs == {}


@pytest.mark.asyncio
async def test_read_prefers_employee_master_then_falls_back(monkeypatch):
    _flags(monkeypatch, dual_write=True, read=True)
    db = _FakeDb()
    repo = EmployeeProfileReadModelRepository(db=db)

    # only in legacy read model -> fallback returns it
    db.employee_profile_read_models.docs["LEGACY"] = {"employee_id": "LEGACY", "full_name": "Old"}
    got = await repo.get_profile(employee_id="LEGACY")
    assert got["full_name"] == "Old"

    # present in employee_master -> preferred
    db.employee_master.docs["NEW"] = {"employee_id": "NEW", "full_name": "Master"}
    db.employee_profile_read_models.docs["NEW"] = {"employee_id": "NEW", "full_name": "Stale"}
    got = await repo.get_profile(employee_id="NEW")
    assert got["full_name"] == "Master"


@pytest.mark.asyncio
async def test_read_off_uses_legacy_read_model(monkeypatch):
    _flags(monkeypatch, dual_write=True, read=False)
    db = _FakeDb()
    repo = EmployeeProfileReadModelRepository(db=db)

    db.employee_master.docs["X"] = {"employee_id": "X", "full_name": "MasterOnly"}
    db.employee_profile_read_models.docs["X"] = {"employee_id": "X", "full_name": "LegacyWins"}
    got = await repo.get_profile(employee_id="X")
    assert got["full_name"] == "LegacyWins"
