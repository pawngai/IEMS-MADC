from __future__ import annotations

from app_platform.domain_separation.data_ownership import assert_collection_ownership
from shared_kernel.events import utc_now_iso


class MongoServiceBookProjectionRepository:
    def __init__(self, *, db, entry_repo=None, part_vi_projection_source=None) -> None:
        assert_collection_ownership(
            context="service_book",
            collection_name="service_book_part_projections",
            write=True,
        )
        self._db = db
        self._entry_repo = entry_repo
        self._part_vi_projection_source = part_vi_projection_source

    async def upsert_part_projection(
        self,
        *,
        employee_id: str,
        part_key: str,
        entry_id: str,
        workflow_state: str,
    ) -> None:
        await self._db.service_book_part_projections.update_one(
            {"employee_id": employee_id, "part_code": part_key},
            {
                "$set": {
                    "employee_id": employee_id,
                    "part_code": part_key,
                    "current_entry_id": entry_id,
                    "workflow_state": workflow_state,
                    "last_event_name": f"ServiceBookEntry{workflow_state.title()}",
                    "updated_at": utc_now_iso(),
                }
            },
            upsert=True,
        )

    async def upsert_projection_patch(
        self,
        *,
        employee_id: str,
        part_code: str,
        patch: dict,
    ) -> None:
        await self._db.service_book_part_projections.update_one(
            {"employee_id": employee_id, "part_code": part_code},
            {
                "$set": {
                    "employee_id": employee_id,
                    "part_code": part_code,
                    "updated_at": utc_now_iso(),
                    **(patch or {}),
                }
            },
            upsert=True,
        )

    async def get_service_book(self, *, employee_id: str) -> dict:
        parts = await self._db.service_book_part_projections.find(
            {"employee_id": employee_id}, {"_id": 0}
        ).to_list(length=200)
        entries = []
        if self._entry_repo is not None:
            entries = await self._entry_repo.list_entries(employee_id=employee_id, filters={})
        return {
            "employee_id": employee_id,
            "parts": await self._merge_part_vi_parts(parts=parts, employee_id=employee_id),
            "entries": entries,
        }

    async def get_part(self, *, employee_id: str, part_code: str) -> dict | None:
        projection = await self._db.service_book_part_projections.find_one(
            {"employee_id": employee_id, "part_code": part_code},
            {"_id": 0},
        )
        if self._part_vi_projection_source is None:
            return projection
        return await self._part_vi_projection_source.resolve_part(
            db=self._db,
            existing_projection=projection,
            employee_id=employee_id,
            part_code=part_code,
        )

    async def _merge_part_vi_parts(self, *, parts: list[dict], employee_id: str) -> list[dict]:
        if self._part_vi_projection_source is None:
            return parts
        return await self._part_vi_projection_source.merge_parts(
            db=self._db,
            parts=parts,
            employee_id=employee_id,
        )

    async def update_projection_status(
        self,
        *,
        projection_name: str,
        last_event_id: str | None,
        last_processed_at: str,
        version: int,
        status: str,
        error_message: str | None = None,
    ) -> None:
        await self._db.service_book_projection_status.update_one(
            {"projection_name": projection_name},
            {
                "$set": {
                    "projection_name": projection_name,
                    "last_event_id": last_event_id,
                    "last_processed_at": last_processed_at,
                    "version": version,
                    "status": status,
                    "error_message": error_message,
                }
            },
            upsert=True,
        )
