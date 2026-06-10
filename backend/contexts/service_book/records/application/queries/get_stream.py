from __future__ import annotations

from pydantic import BaseModel


class GetServiceEventStreamQuery(BaseModel):
    employee_id: str
