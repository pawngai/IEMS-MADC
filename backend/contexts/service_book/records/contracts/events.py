from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SourceRefContract(BaseModel):
    context: str
    reference_id: str
    revision: int | None = None


class ServiceEventRecordedPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_version: int = Field(default=1, ge=1)
    service_event_id: str
    employee_id: str
    event_type: str
    part_code: str | None = None
    effective_from: str | None = None
    effective_to: str | None = None
    payload: dict = Field(default_factory=dict)
    source_ref: SourceRefContract | None = None


class ServiceEventCorrectedPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_version: int = Field(default=1, ge=1)
    service_event_id: str
    employee_id: str
    revision: int
    reason: str
    payload: dict = Field(default_factory=dict)


class ServiceEventVoidedPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_version: int = Field(default=1, ge=1)
    service_event_id: str
    employee_id: str
    reason: str


class ServiceEventDocumentAttachedPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_version: int = Field(default=1, ge=1)
    service_event_id: str
    employee_id: str
    document_id: str
    document_type: str | None = None


class ServiceEventLifecyclePayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_version: int = Field(default=1, ge=1)
    service_event_id: str
    employee_id: str
    part_code: str | None = None
    status: str
    effective_date: str | None = None
    payload: dict = Field(default_factory=dict)
