from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ServiceBookFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    part_code: str | None = None
    status: str | None = None
    statuses: list[str] | None = None
    from_date: str | None = None
    to_date: str | None = None


class ServiceBookQueueFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_state: str | None = None
    page_size: int = Field(default=200, ge=1, le=500)


def parse_status_filters(status: str | None, statuses: str | None) -> tuple[str | None, list[str] | None]:
    parsed_statuses = [value.strip().upper() for value in str(statuses or "").split(",") if value.strip()]
    parsed_status = str(status or "").strip().upper() or None
    if parsed_statuses:
        return None, parsed_statuses
    return parsed_status, None
