from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GenericCommandPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    command_version: int = Field(default=1, ge=1)


__all__ = ["GenericCommandPayload"]
