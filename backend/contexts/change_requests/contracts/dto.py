from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ChangeRequestType(str, Enum):
    PROFILE = "PROFILE"
    SERVICE_BOOK = "SERVICE_BOOK"


class FieldChangeDTO(BaseModel):
    field_name: str
    current_value: Optional[str] = None
    requested_value: str
    field_label: Optional[str] = None


class AttachmentDTO(BaseModel):
    url: str
    filename: str
    original_name: Optional[str] = None
    file_size: Optional[int] = None
    content_type: Optional[str] = None


class CreateChangeRequestDTO(BaseModel):
    request_type: ChangeRequestType
    category: str
    fields: List[FieldChangeDTO]
    reason: str = Field(..., min_length=10, max_length=1000)
    supporting_info: Optional[str] = None
    attachments: List[AttachmentDTO] = Field(default_factory=list)
    entry_id: Optional[str] = None
    entry_section: Optional[str] = None
    entry_label: Optional[str] = None


class ReviewChangeRequestDTO(BaseModel):
    action: str = Field(..., pattern="^(APPROVE|REJECT)$")
    remarks: Optional[str] = Field(None, max_length=500)
