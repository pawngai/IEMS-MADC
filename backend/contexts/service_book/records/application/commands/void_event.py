from __future__ import annotations

from pydantic import BaseModel, Field

from app_platform.contracts.registry import register_command


class VoidServiceEventCommand(BaseModel):
    command_version: int = Field(default=1, ge=1)
    service_event_id: str
    reason: str


register_command(name="VoidServiceEvent", version="v1", schema=VoidServiceEventCommand)
