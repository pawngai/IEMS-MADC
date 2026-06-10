from __future__ import annotations

import pytest
from fastapi import HTTPException

from contexts.employee_profile.application.profile_interface import (
    get_employee_profile_view,
    require_employee_profile,
)


class _FakeCollection:
    def __init__(self, document=None) -> None:
        self.document = document
        self.find_one_calls: list[tuple[dict, dict]] = []

    async def find_one(self, query, projection):
        self.find_one_calls.append((query, projection))
        return self.document


class _FakeDb:
    def __init__(
        self,
        *,
        identity=None,
        extension=None,
        projected=None,
        legacy=None,
    ) -> None:
        self.employee_identities = _FakeCollection(identity)
        self.employee_profile_extensions = _FakeCollection(extension)
        self.employee_profile_read_models = _FakeCollection(projected)
        self.employee_profiles = _FakeCollection(legacy)


@pytest.mark.asyncio
async def test_get_employee_profile_view_composes_split_documents_without_projection() -> None:
    db = _FakeDb(
        identity={
            "employee_id": "EMP-1",
            "full_name": "Split Employee",
            "employment_type": "REGULAR",
        },
        extension={
            "employee_id": "EMP-1",
            "father_name": "Parent Employee",
            "workflow_status": "VERIFIED",
        },
    )

    profile = await get_employee_profile_view(
        db,
        employee_id="EMP-1",
        projection={"_id": 0},
    )

    assert profile is not None
    assert profile["employee_id"] == "EMP-1"
    assert profile["full_name"] == "Split Employee"
    assert profile["father_name"] == "Parent Employee"
    assert profile["workflow_status"] == "VERIFIED"


@pytest.mark.asyncio
async def test_require_employee_profile_rejects_legacy_only_record_after_cutover() -> None:
    db = _FakeDb(
        legacy={
            "employee_id": "EMP-LEGACY-1",
            "full_name": "Legacy Only",
        }
    )

    with pytest.raises(HTTPException) as exc:
        await require_employee_profile(
            db,
            employee_id="EMP-LEGACY-1",
            projection={"_id": 0},
        )

    assert exc.value.status_code == 404
    assert db.employee_profiles.find_one_calls == []