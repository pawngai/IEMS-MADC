from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from app_platform.domain_separation.data_ownership import assert_collection_ownership
from contexts.employee_profile.infrastructure.gateway import (
    _compose_live_profile,
    _profile_ready_identity_query,
)


class EmployeeProfileReadModelRepository:
    def __init__(self, *, db) -> None:
        assert_collection_ownership(
            context="employee_profile",
            collection_name="employee_profile_read_models",
            write=True,
        )
        self._db = db

    async def upsert_projection(self, *, employee_id: str, projection: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        payload = deepcopy(projection)
        created_at = payload.pop("created_at", None) or now
        payload["employee_id"] = employee_id
        payload["read_model_updated_at"] = now
        await self._db.employee_profile_read_models.update_one(
            {"employee_id": employee_id},
            {
                "$set": payload,
                "$setOnInsert": {
                    "created_at": created_at,
                },
            },
            upsert=True,
        )

    async def patch_projection(self, *, employee_id: str, patch: dict[str, Any]) -> None:
        if not patch:
            return

        now = datetime.now(timezone.utc).isoformat()
        payload = deepcopy(patch)
        created_at = payload.pop("created_at", None) or now
        await self._db.employee_profile_read_models.update_one(
            {"employee_id": employee_id},
            {
                "$set": {
                    **payload,
                    "employee_id": employee_id,
                    "read_model_updated_at": now,
                },
                "$setOnInsert": {
                    "created_at": created_at,
                },
            },
            upsert=True,
        )

    async def get_profile(self, *, employee_id: str) -> dict[str, Any] | None:
        projected = await self._db.employee_profile_read_models.find_one(
            {"employee_id": employee_id},
            {"_id": 0},
        )
        if projected:
            return projected
        return await _compose_live_profile(self._db, employee_id)

    async def count_profiles(self, *, query: dict[str, Any]) -> int:
        projected_count = await self._db.employee_profile_read_models.count_documents(query)
        if projected_count > 0:
            return int(projected_count)
        return int(await self._db.employee_identities.count_documents(_profile_ready_identity_query(query)))

    async def list_profiles(self, *, query: dict[str, Any], skip: int = 0, limit: int = 20) -> list[dict[str, Any]]:
        projected_items = await (
            self._db.employee_profile_read_models.find(query, {"_id": 0})
            .skip(skip)
            .limit(limit)
            .to_list(length=limit)
        )
        if projected_items:
            return projected_items

        items = await (
            self._db.employee_identities.find(_profile_ready_identity_query(query), {"_id": 0})
            .skip(skip)
            .limit(limit)
            .to_list(length=limit)
        )
        return [
            await _compose_live_profile(self._db, item.get("employee_id")) or item
            for item in items
        ]
