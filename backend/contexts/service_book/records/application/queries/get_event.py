from __future__ import annotations

from pydantic import BaseModel, Field


class GetServiceEventQuery(BaseModel):
    service_event_id: str
    include_employee_id: bool = Field(default=True)
