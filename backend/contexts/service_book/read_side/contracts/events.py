from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ServiceBookProjectionEvent(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_version: int = Field(default=1, ge=1)
    employee_id: str
    part_code: str | None = None
    part_key: str | None = None


class ServiceBookServiceEventProjection(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_version: int = Field(default=1, ge=1)
    service_event_id: str | None = None
    employee_id: str
    part_code: str | None = None
    part_key: str | None = None
    payload: dict = Field(default_factory=dict)
