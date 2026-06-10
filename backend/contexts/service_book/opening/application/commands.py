from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ServiceBookOpeningPayload(BaseModel):
    employee_id: str
    parts: dict[str, dict[str, Any]] = Field(default_factory=dict)
    documents: list[dict[str, Any]] = Field(default_factory=list)


class OpeningRemarks(BaseModel):
    remarks: str | None = None


class OpeningDocumentLink(BaseModel):
    document_id: str
    document_type: str | None = None
    name: str | None = None
    field_key: str | None = None
    field_label: str | None = None
    part_id: str | None = None
