from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from app_platform.config.settings import settings
from app_platform.domain_separation.data_ownership import assert_collection_ownership
from contexts.employee_master.profile.infrastructure.gateway import (
    _compose_live_profile,
    _profile_ready_identity_query,
)

# Phase 1b expand/contract cutover: the composed employee record is mirrored into
# the canonical `employee_master` collection (dual-write) and reads prefer it
# (read-switch), both flag-gated, with the legacy read model retained as fallback
# and for rollback. employee_master is owned by the employee_master context, so
# these writes are same-context (no cross-context DB write).
CANONICAL_COLLECTION = "employee_master"


class EmployeeProfileReadModelRepository:
    def __init__(self, *, db) -> None:
        assert_collection_ownership(
            context="employee_master",
            collection_name="employee_profile_read_models",
            write=True,
        )
        assert_collection_ownership(
            context="employee_master",
            collection_name=CANONICAL_COLLECTION,
            write=True,
        )
        self._db = db

    def _master(self):
        """Return the employee_master collection, or None when the db handle does
        not expose it (e.g. lightweight unit-test doubles). Real Motor databases
        always return a collection for any name."""
        return getattr(self._db, CANONICAL_COLLECTION, None)

    async def upsert_projection(self, *, employee_id: str, projection: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        payload = deepcopy(projection)
        created_at = payload.pop("created_at", None) or now
        payload["employee_id"] = employee_id
        payload["read_model_updated_at"] = now
        set_update = {
            "$set": payload,
            "$setOnInsert": {"created_at": created_at},
        }
        await self._db.employee_profile_read_models.update_one(
            {"employee_id": employee_id}, set_update, upsert=True
        )
        master = self._master()
        if settings.employee_master_dual_write and master is not None:
            await master.update_one(
                {"employee_id": employee_id}, set_update, upsert=True
            )

    async def patch_projection(self, *, employee_id: str, patch: dict[str, Any]) -> None:
        if not patch:
            return

        now = datetime.now(timezone.utc).isoformat()
        payload = deepcopy(patch)
        created_at = payload.pop("created_at", None) or now
        set_update = {
            "$set": {
                **payload,
                "employee_id": employee_id,
                "read_model_updated_at": now,
            },
            "$setOnInsert": {"created_at": created_at},
        }
        await self._db.employee_profile_read_models.update_one(
            {"employee_id": employee_id}, set_update, upsert=True
        )
        master = self._master()
        if settings.employee_master_dual_write and master is not None:
            await master.update_one(
                {"employee_id": employee_id}, set_update, upsert=True
            )

    async def get_profile(self, *, employee_id: str) -> dict[str, Any] | None:
        master = self._master()
        if settings.employee_master_read and master is not None:
            master_doc = await master.find_one({"employee_id": employee_id}, {"_id": 0})
            if master_doc:
                return master_doc
        projected = await self._db.employee_profile_read_models.find_one(
            {"employee_id": employee_id},
            {"_id": 0},
        )
        if projected:
            return projected
        return await _compose_live_profile(self._db, employee_id)

    async def count_profiles(self, *, query: dict[str, Any]) -> int:
        master = self._master()
        if settings.employee_master_read and master is not None:
            master_count = await master.count_documents(query)
            if master_count > 0:
                return int(master_count)
        projected_count = await self._db.employee_profile_read_models.count_documents(query)
        if projected_count > 0:
            return int(projected_count)
        return int(await self._db.employee_identities.count_documents(_profile_ready_identity_query(query)))

    async def list_profiles(self, *, query: dict[str, Any], skip: int = 0, limit: int = 20) -> list[dict[str, Any]]:
        master = self._master()
        if settings.employee_master_read and master is not None:
            master_items = await (
                master.find(query, {"_id": 0})
                .skip(skip)
                .limit(limit)
                .to_list(length=limit)
            )
            if master_items:
                return master_items
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
