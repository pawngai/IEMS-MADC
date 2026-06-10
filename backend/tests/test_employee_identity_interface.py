from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from contexts.employee_identity.application import identity_interface
from contexts.employee_identity.api import read_router
from contexts.rbac.domain.models import Permission


def test_build_identity_query_filters_workflow_status_not_employee_status() -> None:
    query = identity_interface._build_identity_query(status="draft")

    assert query == {"workflow_status": "DRAFT"}


def test_build_identity_query_filters_multiple_workflow_statuses() -> None:
    query = identity_interface._build_identity_query(status=["submitted", "verified"])

    assert query == {"workflow_status": {"$in": ["SUBMITTED", "VERIFIED"]}}


@pytest.mark.asyncio
async def test_verifier_identity_list_excludes_draft_and_includes_active_by_default(monkeypatch) -> None:
    captured: dict[str, dict] = {}

    async def fake_list_identity_records(db, **kwargs):
        captured["list"] = kwargs
        return []

    async def fake_count_employee_identities(db, **kwargs):
        captured["count"] = kwargs
        return 0

    monkeypatch.setattr(read_router, "list_identity_records", fake_list_identity_records)
    monkeypatch.setattr(read_router, "count_employee_identities", fake_count_employee_identities)

    result = await read_router.list_employee_identities(
        page=1,
        page_size=20,
        db=object(),
        current_user={
            "permissions": [Permission.IDENTITY_READ_ALL.value],
            "authorities": ["VERIFIER"],
            "active_role": "VERIFIER",
        },
    )

    assert result["identities"] == []
    assert captured["list"]["status"] == ["SUBMITTED", "VERIFIED", "ACTIVE"]
    assert captured["count"]["status"] == ["SUBMITTED", "VERIFIED", "ACTIVE"]


@pytest.mark.asyncio
async def test_verifier_identity_list_rejects_explicit_draft_filter(monkeypatch) -> None:
    captured: dict[str, dict] = {}

    async def fake_list_identity_records(db, **kwargs):
        captured["list"] = kwargs
        return []

    async def fake_count_employee_identities(db, **kwargs):
        captured["count"] = kwargs
        return 0

    monkeypatch.setattr(read_router, "list_identity_records", fake_list_identity_records)
    monkeypatch.setattr(read_router, "count_employee_identities", fake_count_employee_identities)

    await read_router.list_employee_identities(
        status="DRAFT",
        page=1,
        page_size=20,
        db=object(),
        current_user={
            "permissions": [Permission.IDENTITY_READ_ALL.value],
            "authorities": ["VERIFIER"],
            "active_role": "VERIFIER",
        },
    )

    assert captured["list"]["status"] == read_router.NO_MATCH_WORKFLOW_STATUS
    assert captured["count"]["status"] == read_router.NO_MATCH_WORKFLOW_STATUS


@pytest.mark.asyncio
async def test_approving_authority_identity_list_shows_verified_and_active_by_default(monkeypatch) -> None:
    captured: dict[str, dict] = {}

    async def fake_list_identity_records(db, **kwargs):
        captured["list"] = kwargs
        return []

    async def fake_count_employee_identities(db, **kwargs):
        captured["count"] = kwargs
        return 0

    monkeypatch.setattr(read_router, "list_identity_records", fake_list_identity_records)
    monkeypatch.setattr(read_router, "count_employee_identities", fake_count_employee_identities)

    result = await read_router.list_employee_identities(
        page=1,
        page_size=20,
        db=object(),
        current_user={
            "permissions": [Permission.IDENTITY_READ_ALL.value],
            "authorities": ["APPROVING_AUTHORITY"],
            "active_role": "APPROVING_AUTHORITY",
        },
    )

    assert result["identities"] == []
    assert captured["list"]["status"] == ["VERIFIED", "ACTIVE"]
    assert captured["count"]["status"] == ["VERIFIED", "ACTIVE"]


@pytest.mark.asyncio
async def test_approving_authority_identity_list_rejects_submitted_filter(monkeypatch) -> None:
    captured: dict[str, dict] = {}

    async def fake_list_identity_records(db, **kwargs):
        captured["list"] = kwargs
        return []

    async def fake_count_employee_identities(db, **kwargs):
        captured["count"] = kwargs
        return 0

    monkeypatch.setattr(read_router, "list_identity_records", fake_list_identity_records)
    monkeypatch.setattr(read_router, "count_employee_identities", fake_count_employee_identities)

    await read_router.list_employee_identities(
        status="SUBMITTED",
        page=1,
        page_size=20,
        db=object(),
        current_user={
            "permissions": [Permission.IDENTITY_READ_ALL.value],
            "authorities": ["APPROVING_AUTHORITY"],
            "active_role": "APPROVING_AUTHORITY",
        },
    )

    assert captured["list"]["status"] == read_router.NO_MATCH_WORKFLOW_STATUS
    assert captured["count"]["status"] == read_router.NO_MATCH_WORKFLOW_STATUS


@pytest.mark.asyncio
async def test_identity_directory_rows_include_profile_workflow_status(monkeypatch) -> None:
    async def fake_list_identity_records(db, **kwargs):
        return [
            {
                "employee_id": "EMP-UUID-1",
                "employee_code": "MADC-2024-R0002",
                "full_name": "Directory Employee",
                "workflow_status": "ACTIVE",
            }
        ]

    async def fake_count_employee_identities(db, **kwargs):
        return 1

    async def fake_list_profile_workflow_statuses(db, *, employee_ids):
        assert employee_ids == ["EMP-UUID-1"]
        return {"EMP-UUID-1": "LOCKED"}

    monkeypatch.setattr(read_router, "list_identity_records", fake_list_identity_records)
    monkeypatch.setattr(read_router, "count_employee_identities", fake_count_employee_identities)
    monkeypatch.setattr(read_router, "list_profile_workflow_statuses", fake_list_profile_workflow_statuses)

    result = await read_router.list_employee_identities(
        page=1,
        page_size=20,
        db=object(),
        current_user={
            "permissions": [Permission.IDENTITY_READ_ALL.value],
            "authorities": ["GLOBAL_DATA_ENTRY"],
            "active_role": "GLOBAL_DATA_ENTRY",
        },
    )

    identity = result["identities"][0]
    assert identity["workflow_status"] == "ACTIVE"
    assert identity["identity_workflow_status"] == "ACTIVE"
    assert identity["profile_workflow_status"] == "LOCKED"


@pytest.mark.asyncio
async def test_identity_directory_sorts_employee_code_for_global_roles(monkeypatch) -> None:
    async def fake_list_identity_records(db, **kwargs):
        return [
            {
                "employee_id": "EMP-2",
                "employee_code": "MADC-0002",
                "full_name": "Beta Employee",
                "workflow_status": "ACTIVE",
            },
            {
                "employee_id": "EMP-1",
                "employee_code": "MADC-0001",
                "full_name": "Alpha Employee",
                "workflow_status": "ACTIVE",
            },
        ]

    async def fake_count_employee_identities(db, **kwargs):
        return 2

    async def fake_list_profile_workflow_statuses(db, *, employee_ids):
        return {employee_id: "LOCKED" for employee_id in employee_ids}

    monkeypatch.setattr(read_router, "list_identity_records", fake_list_identity_records)
    monkeypatch.setattr(read_router, "count_employee_identities", fake_count_employee_identities)
    monkeypatch.setattr(read_router, "list_profile_workflow_statuses", fake_list_profile_workflow_statuses)

    result = await read_router.list_employee_identities(
        sort_by="employee_code",
        sort_dir="desc",
        page=1,
        page_size=20,
        db=object(),
        current_user={
            "permissions": [Permission.IDENTITY_READ_ALL.value],
            "authorities": ["GLOBAL_DATA_ENTRY"],
            "active_role": "GLOBAL_DATA_ENTRY",
        },
    )

    assert [identity["employee_code"] for identity in result["identities"]] == [
        "MADC-0002",
        "MADC-0001",
    ]


@pytest.mark.asyncio
async def test_identity_directory_sorts_profile_workflow_after_enrichment(monkeypatch) -> None:
    async def fake_list_identity_records(db, **kwargs):
        return [
            {
                "employee_id": "EMP-3",
                "employee_code": "MADC-0003",
                "full_name": "Gamma Employee",
                "workflow_status": "ACTIVE",
            },
            {
                "employee_id": "EMP-1",
                "employee_code": "MADC-0001",
                "full_name": "Alpha Employee",
                "workflow_status": "ACTIVE",
            },
            {
                "employee_id": "EMP-2",
                "employee_code": "MADC-0002",
                "full_name": "Beta Employee",
                "workflow_status": "ACTIVE",
            },
        ]

    async def fake_count_employee_identities(db, **kwargs):
        return 3

    async def fake_list_profile_workflow_statuses(db, *, employee_ids):
        assert employee_ids == ["EMP-3", "EMP-1", "EMP-2"]
        return {
            "EMP-3": "VERIFIED",
            "EMP-1": "DRAFT",
            "EMP-2": "LOCKED",
        }

    monkeypatch.setattr(read_router, "list_identity_records", fake_list_identity_records)
    monkeypatch.setattr(read_router, "count_employee_identities", fake_count_employee_identities)
    monkeypatch.setattr(read_router, "list_profile_workflow_statuses", fake_list_profile_workflow_statuses)

    result = await read_router.list_employee_identities(
        sort_by="workflow_status",
        sort_dir="asc",
        page=1,
        page_size=20,
        db=object(),
        current_user={
            "permissions": [Permission.IDENTITY_READ_ALL.value],
            "authorities": ["GLOBAL_DATA_ENTRY"],
            "active_role": "GLOBAL_DATA_ENTRY",
        },
    )

    assert [identity["employee_id"] for identity in result["identities"]] == [
        "EMP-1",
        "EMP-2",
        "EMP-3",
    ]


@pytest.mark.asyncio
async def test_get_employee_identity_falls_back_to_employee_code(monkeypatch) -> None:
    repo = SimpleNamespace(get_identity=AsyncMock(return_value=None))
    collection = SimpleNamespace(
        find_one=AsyncMock(
            return_value={
                "employee_id": "EMP-UUID-1",
                "employee_code": "MADC-2020-R0001",
                "full_name": "Demo Employee",
            }
        )
    )
    db = SimpleNamespace(employee_identities=collection)

    monkeypatch.setattr(identity_interface, "_repo", lambda _db: repo)

    identity = await identity_interface.get_employee_identity(
        db,
        employee_id="MADC-2020-R0001",
    )

    repo.get_identity.assert_awaited_once_with(
        employee_id="MADC-2020-R0001",
        projection=None,
    )
    collection.find_one.assert_awaited_once_with(
        {"employee_code": "MADC-2020-R0001"},
        {"_id": 0},
    )
    assert identity["full_name"] == "Demo Employee"