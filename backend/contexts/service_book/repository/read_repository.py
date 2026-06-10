from __future__ import annotations

from app_platform.domain_separation.data_ownership import assert_collection_ownership
from contexts.service_book.read_side.read_model.projectors.part_vi_leave_projection import (
    LeaveLedgerPartVIProjectionSource,
)
from contexts.service_book.repository.mongo_entry_repository import MongoServiceBookEntryRepository
from contexts.service_book.repository.mongo_projection_repository import (
    MongoServiceBookProjectionRepository,
)
from shared_kernel.events import utc_now_iso


class ServiceBookReadRepository:
    def __init__(self, *, db, part_vi_projection_source=None) -> None:
        assert_collection_ownership(
            context="service_book",
            collection_name="service_book_entries",
            write=True,
        )
        assert_collection_ownership(
            context="service_book",
            collection_name="service_book_part_projections",
            write=True,
        )
        source = part_vi_projection_source or LeaveLedgerPartVIProjectionSource()
        self._entry_repo = MongoServiceBookEntryRepository(
            db=db,
            part_vi_projection_source=source,
        )
        self._projection_repo = MongoServiceBookProjectionRepository(
            db=db,
            entry_repo=self._entry_repo,
            part_vi_projection_source=source,
        )

    async def append_entry(
        self,
        *,
        employee_id: str,
        event_name: str,
        part_code: str | None,
        payload: dict,
        effective_date: str | None,
        fields_changed: list[str],
        source_event_id: str | None = None,
    ) -> str:
        return await self._entry_repo.append_entry(
            employee_id=employee_id,
            event_name=event_name,
            part_code=part_code,
            payload=payload,
            effective_date=effective_date,
            fields_changed=fields_changed,
            source_event_id=source_event_id,
        )

    async def upsert_part_projection(
        self,
        *,
        employee_id: str,
        part_code: str,
        patch: dict,
    ) -> None:
        await self._projection_repo.upsert_projection_patch(
            employee_id=employee_id,
            part_code=part_code,
            patch=patch,
        )

    async def get_service_book(self, *, employee_id: str) -> dict:
        return await self._projection_repo.get_service_book(employee_id=employee_id)

    async def get_part(self, *, employee_id: str, part_code: str) -> dict | None:
        return await self._projection_repo.get_part(
            employee_id=employee_id,
            part_code=part_code,
        )

    async def list_entries(self, *, employee_id: str, filters: dict) -> list[dict]:
        return await self._entry_repo.list_entries(employee_id=employee_id, filters=filters)

    async def update_projection_status(
        self,
        *,
        projection_name: str,
        last_event_id: str | None,
        version: int,
        status: str,
        error_message: str | None = None,
    ) -> None:
        await self._projection_repo.update_projection_status(
            projection_name=projection_name,
            last_event_id=last_event_id,
            last_processed_at=utc_now_iso(),
            version=version,
            status=status,
            error_message=error_message,
        )
