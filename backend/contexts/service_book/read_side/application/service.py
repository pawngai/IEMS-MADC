from __future__ import annotations

from contexts.service_book.read_side.application.queries.get_print_view import (
    build_full_print_view,
    build_part_print_view,
)
from contexts.service_book.read_side.application.queries.get_service_book import (
    get_part_schema,
    get_service_book,
    get_service_book_part,
    list_service_book_entries,
    normalize_part_code,
)
from contexts.service_book.read_side.application.projection_rebuilder import (
    rebuild_from_approved_service_events,
)


class ServiceBookReadService:
    def __init__(self, *, repo, db=None) -> None:
        self._repo = repo
        self._db = db

    async def get_service_book(self, *, employee_id: str) -> dict:
        return await get_service_book(repo=self._repo, employee_id=employee_id)

    async def get_service_book_part(self, *, employee_id: str, part_code: str) -> dict | None:
        return await get_service_book_part(
            repo=self._repo,
            employee_id=employee_id,
            part_code=part_code,
        )

    async def list_service_book_entries(self, *, employee_id: str, filters: dict) -> list[dict]:
        return await list_service_book_entries(
            repo=self._repo,
            employee_id=employee_id,
            filters=filters,
        )

    def normalize_part_code(self, part_value: str | None) -> str | None:
        return normalize_part_code(part_value)

    async def get_part_schema(self, *, part_key: str) -> dict:
        return await get_part_schema(part_key=part_key)

    async def build_part_print_view(self, *, employee_id: str, part_key: str) -> dict:
        return await build_part_print_view(
            repo=self._repo,
            employee_id=employee_id,
            part_key=part_key,
            normalize_part_code_fn=self.normalize_part_code,
        )

    async def build_full_print_view(self, *, employee_id: str) -> dict:
        return await build_full_print_view(repo=self._repo, employee_id=employee_id)

    async def rebuild_from_approved_events(self, *, employee_id: str | None = None) -> dict:
        if self._db is None:
            raise ValueError("ServiceBookReadService requires db to rebuild projections")
        return await rebuild_from_approved_service_events(
            db=self._db,
            repo=self._repo,
            employee_id=employee_id,
        )


