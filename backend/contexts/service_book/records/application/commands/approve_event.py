from __future__ import annotations

from pydantic import BaseModel, Field

from app_platform.contracts.registry import register_command


class ApproveServiceEventCommand(BaseModel):
    command_version: int = Field(default=1, ge=1)
    service_event_id: str


class LockServiceEventCommand(BaseModel):
    command_version: int = Field(default=1, ge=1)
    service_event_id: str


register_command(name="ApproveServiceEvent", version="v1", schema=ApproveServiceEventCommand)
register_command(name="LockServiceEvent", version="v1", schema=LockServiceEventCommand)
