from __future__ import annotations

from pydantic import BaseModel, Field


class ServiceBookQuery(BaseModel):
    employee_id: str = Field(min_length=1)


class ServiceBookPartQuery(ServiceBookQuery):
    part_key: str = Field(min_length=1)
