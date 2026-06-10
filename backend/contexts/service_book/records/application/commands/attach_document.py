from __future__ import annotations

from pydantic import BaseModel, Field

from app_platform.contracts.registry import register_command


class AttachDocumentCommand(BaseModel):
    command_version: int = Field(default=1, ge=1)
    service_event_id: str
    document_id: str
    document_type: str | None = None


register_command(name="AttachServiceEventDocument", version="v1", schema=AttachDocumentCommand)
