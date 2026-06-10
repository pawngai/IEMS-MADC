from __future__ import annotations

import pytest
from fastapi import HTTPException

from contexts.system_admin.department.api import management_router


class _ShouldNotHitDb:
    def __getitem__(self, _name: str):
        raise AssertionError("database should not be accessed for unauthorized department management reads")


class _FakeDepartmentCollection:
    def __init__(self, docs=None) -> None:
        self.docs = list(docs or [])

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if _matches_query(doc, query):
                result = dict(doc)
                if projection and projection.get("_id") == 0:
                    result.pop("_id", None)
                return result
        return None

    async def insert_one(self, document):
        stored = dict(document)
        stored.setdefault("_id", f"mongo-{len(self.docs) + 1}")
        self.docs.append(stored)

    async def update_one(self, query, update):
        target = await self.find_one(query)
        if target is None:
            raise AssertionError(f"document not found for query: {query}")
        for index, doc in enumerate(self.docs):
            if doc.get("_id") == target.get("_id"):
                if "$set" in update:
                    self.docs[index].update(update["$set"])
                return
        raise AssertionError(f"document not found for update query: {query}")


class _FakeDepartmentDb:
    def __init__(self, docs=None) -> None:
        self.departments = _FakeDepartmentCollection(docs)

    def __getitem__(self, name: str):
        return getattr(self, name)


def _matches_query(doc: dict, query: dict) -> bool:
    for key, value in query.items():
        if key == "$or":
            if not any(_matches_query(doc, clause) for clause in value):
                return False
            continue
        if isinstance(value, dict) and "$exists" in value:
            exists = key in doc
            if exists != value["$exists"]:
                return False
            continue
        if doc.get(key) != value:
            return False
    return True


@pytest.mark.asyncio
async def test_list_departments_requires_system_admin() -> None:
    with pytest.raises(HTTPException) as exc:
        await management_router.list_departments(
            include_inactive=False,
            db=_ShouldNotHitDb(),
            current_user={"authorities": ["DEPARTMENT_ADMIN"], "sub": "user-1"},
        )

    assert exc.value.status_code == 403
    assert exc.value.detail["error_code"] == "SYSTEM_ADMIN_REQUIRED"


@pytest.mark.asyncio
async def test_get_department_requires_system_admin() -> None:
    with pytest.raises(HTTPException) as exc:
        await management_router.get_department(
            code="HR",
            db=_ShouldNotHitDb(),
            current_user={"authorities": ["DEPARTMENT_ADMIN"], "sub": "user-2"},
        )

    assert exc.value.status_code == 403
    assert exc.value.detail["error_code"] == "SYSTEM_ADMIN_REQUIRED"


@pytest.mark.asyncio
async def test_sync_role_holders_assigns_hod_and_data_entry(monkeypatch) -> None:
    calls: list[tuple[str, dict]] = []

    async def _fake_sync_department_authority(_db, **kwargs):
        calls.append(("sync", kwargs))
        return {"granted_to": kwargs["employee_id"], "revoked_from": None}

    monkeypatch.setattr(
        management_router,
        "sync_department_authority",
        _fake_sync_department_authority,
    )

    result = await management_router._sync_role_holders(
        object(),
        department_code="HR",
        old_hod=None,
        new_hod="EMP-HOD-1",
        old_de=None,
        new_de="EMP-DE-1",
        actor_sub="admin-1",
    )

    assert calls == [
        (
            "sync",
            {
                "employee_id": "EMP-HOD-1",
                "authority": "HOD",
                "department_code": "HR",
                "actor_sub": "admin-1",
            },
        ),
        (
            "sync",
            {
                "employee_id": "EMP-DE-1",
                "authority": "DEPT_DATA_ENTRY",
                "department_code": "HR",
                "actor_sub": "admin-1",
            },
        ),
    ]
    assert result == {
        "hod_sync": {"granted_to": "EMP-HOD-1", "revoked_from": None},
        "de_sync": {"granted_to": "EMP-DE-1", "revoked_from": None},
    }


@pytest.mark.asyncio
async def test_sync_role_holders_revokes_cleared_assignments(monkeypatch) -> None:
    calls: list[tuple[str, dict]] = []

    async def _fake_revoke_department_authority(_db, **kwargs):
        calls.append(("revoke", kwargs))
        return {"revoked_from": kwargs["employee_id"]}

    monkeypatch.setattr(
        management_router,
        "revoke_department_authority",
        _fake_revoke_department_authority,
    )

    result = await management_router._sync_role_holders(
        object(),
        department_code="HR",
        old_hod="EMP-HOD-OLD",
        new_hod=None,
        old_de="EMP-DE-OLD",
        new_de=None,
        actor_sub="admin-2",
    )

    assert calls == [
        (
            "revoke",
            {
                "employee_id": "EMP-HOD-OLD",
                "authority": "HOD",
                "actor_sub": "admin-2",
            },
        ),
        (
            "revoke",
            {
                "employee_id": "EMP-DE-OLD",
                "authority": "DEPT_DATA_ENTRY",
                "actor_sub": "admin-2",
            },
        ),
    ]
    assert result == {
        "hod_revoke": {"revoked_from": "EMP-HOD-OLD"},
        "de_revoke": {"revoked_from": "EMP-DE-OLD"},
    }


@pytest.mark.asyncio
async def test_create_department_returns_authority_sync(monkeypatch) -> None:
    db = _FakeDepartmentDb()

    async def _fake_sync_role_holders(*_args, **_kwargs):
        return {"hod_sync": {"granted_to": "EMP-HOD-1", "revoked_from": None}}

    async def _fake_write_log(*_args, **_kwargs):
        return None

    monkeypatch.setattr(management_router, "_sync_role_holders", _fake_sync_role_holders)
    monkeypatch.setattr(management_router, "_write_log", _fake_write_log)

    result = await management_router.create_department(
        data=management_router.DepartmentCreate(
            code="HR",
            name="Human Resources",
            hod_employee_id="EMP-HOD-1",
        ),
        db=db,
        current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1", "email": "admin@example.com"},
    )

    assert result["success"] is True
    assert result["record"]["code"] == "HR"
    assert result["authority_sync"] == {
        "hod_sync": {"granted_to": "EMP-HOD-1", "revoked_from": None}
    }


@pytest.mark.asyncio
async def test_update_department_returns_authority_sync(monkeypatch) -> None:
    db = _FakeDepartmentDb(
        docs=[
            {
                "_id": "mongo-1",
                "id": "dept-1",
                "code": "HR",
                "name": "Human Resources",
                "description": None,
                "metadata": {
                    "hod_employee_id": "EMP-HOD-OLD",
                    "data_entry_employee_id": None,
                    "assigned_authorities": ["HOD"],
                    "allowed_authorities": ["HOD"],
                },
                "is_active": True,
                "created_at": "2026-01-01T00:00:00+00:00",
                "created_by": "admin@example.com",
                "updated_at": "2026-01-01T00:00:00+00:00",
                "updated_by": "admin@example.com",
            }
        ]
    )

    async def _fake_sync_role_holders(*_args, **_kwargs):
        return {"hod_sync": {"granted_to": "EMP-HOD-NEW", "revoked_from": "user-old"}}

    async def _fake_write_log(*_args, **_kwargs):
        return None

    monkeypatch.setattr(management_router, "_sync_role_holders", _fake_sync_role_holders)
    monkeypatch.setattr(management_router, "_write_log", _fake_write_log)

    result = await management_router.update_department(
        code="HR",
        data=management_router.DepartmentUpdate(
            hod_employee_id="EMP-HOD-NEW",
            reason="Rotate HOD assignment",
        ),
        db=db,
        current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1", "email": "admin@example.com"},
    )

    assert result["success"] is True
    assert result["record"]["hod_employee_id"] == "EMP-HOD-NEW"
    assert result["authority_sync"] == {
        "hod_sync": {"granted_to": "EMP-HOD-NEW", "revoked_from": "user-old"}
    }
    assert result["changes"]["authority_sync"] == result["authority_sync"]