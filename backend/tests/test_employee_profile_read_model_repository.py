from __future__ import annotations

import asyncio

from contexts.employee_master.profile.read_model.infrastructure.repository import (
    EmployeeProfileReadModelRepository,
)


class _RecordingCollection:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def update_one(self, query: dict, update: dict, upsert: bool = False):
        self.calls.append(
            {
                "query": query,
                "update": update,
                "upsert": upsert,
            }
        )


class _RecordingDB:
    def __init__(self) -> None:
        self.employee_profile_read_models = _RecordingCollection()


def test_upsert_projection_uses_created_at_only_for_insert() -> None:
    async def _run() -> None:
        db = _RecordingDB()
        repo = EmployeeProfileReadModelRepository(db=db)

        await repo.upsert_projection(
            employee_id="EMP-TEST-1",
            projection={
                "employee_id": "EMP-TEST-1",
                "full_name": "Test Employee",
                "created_at": "2026-03-15T00:00:00Z",
            },
        )

        call = db.employee_profile_read_models.calls[0]
        assert call["upsert"] is True
        assert call["update"]["$set"]["employee_id"] == "EMP-TEST-1"
        assert "created_at" not in call["update"]["$set"]
        assert call["update"]["$setOnInsert"]["created_at"] == "2026-03-15T00:00:00Z"

    asyncio.run(_run())


def test_patch_projection_does_not_mutate_created_at_on_set() -> None:
    async def _run() -> None:
        db = _RecordingDB()
        repo = EmployeeProfileReadModelRepository(db=db)

        await repo.patch_projection(
            employee_id="EMP-TEST-2",
            patch={
                "mobile_primary": "9876543210",
                "created_at": "2026-03-15T00:00:00Z",
            },
        )

        call = db.employee_profile_read_models.calls[0]
        assert call["upsert"] is True
        assert call["update"]["$set"]["employee_id"] == "EMP-TEST-2"
        assert call["update"]["$set"]["mobile_primary"] == "9876543210"
        assert "created_at" not in call["update"]["$set"]
        assert call["update"]["$setOnInsert"]["created_at"] == "2026-03-15T00:00:00Z"

    asyncio.run(_run())
