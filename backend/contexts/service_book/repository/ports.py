from __future__ import annotations

from typing import Any, Protocol


class ServiceBookEntryRepositoryPort(Protocol):
    async def list_queue_entries(
        self,
        *,
        workflow_state: str | None,
        page_size: int,
        workflow_states: list[str] | None = None,
    ) -> list[dict[str, Any]]: ...

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
    ) -> str: ...

    async def list_entries(self, *, employee_id: str, filters: dict) -> list[dict]: ...


class ServiceBookProjectionRepositoryPort(Protocol):
    async def upsert_part_projection(
        self,
        *,
        employee_id: str,
        part_key: str,
        entry_id: str,
        workflow_state: str,
    ) -> None: ...

    async def upsert_projection_patch(
        self,
        *,
        employee_id: str,
        part_code: str,
        patch: dict,
    ) -> None: ...

    async def get_service_book(self, *, employee_id: str) -> dict: ...

    async def get_part(self, *, employee_id: str, part_code: str) -> dict | None: ...

class ServiceBookRevisionRepositoryPort(Protocol):
    async def get_latest_revision(self, *, entry_id: str) -> dict[str, Any] | None: ...

    async def insert_revision(self, revision: dict[str, Any]) -> None: ...
