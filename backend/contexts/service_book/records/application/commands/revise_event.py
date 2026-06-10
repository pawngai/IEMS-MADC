from __future__ import annotations

from pydantic import BaseModel, Field

from app_platform.contracts.registry import register_command


class ReviseServiceEventCommand(BaseModel):
    command_version: int = Field(default=1, ge=1)
    service_event_id: str
    corrected_payload: dict = Field(default_factory=dict)
    reason: str


register_command(name="CorrectServiceEvent", version="v1", schema=ReviseServiceEventCommand)
