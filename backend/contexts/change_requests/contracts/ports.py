from __future__ import annotations

from typing import Protocol

from contexts.change_requests.contracts.dto import CreateChangeRequestDTO


class ChangeRequestGateway(Protocol):
    async def create_change_request(self, payload: CreateChangeRequestDTO, *, current_user: dict, session=None) -> dict: ...
    async def list_my_change_requests(self, *, current_user: dict, status: str | None = None) -> dict: ...
    async def get_change_request(self, request_id: str, *, current_user: dict) -> dict: ...
    async def cancel_change_request(self, request_id: str, *, current_user: dict, session=None) -> dict: ...
    async def list_change_requests(
        self,
        *,
        current_user: dict,
        status: str | None = None,
        employee_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict: ...
    async def review_change_request(
        self,
        request_id: str,
        *,
        action: str,
        remarks: str | None,
        current_user: dict,
        session=None,
    ) -> dict: ...
    async def get_pending_count(self, *, current_user: dict) -> int: ...
