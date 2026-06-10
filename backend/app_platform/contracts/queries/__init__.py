from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GenericQueryPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    query_version: int = Field(default=1, ge=1)


__all__ = ["GenericQueryPayload"]
