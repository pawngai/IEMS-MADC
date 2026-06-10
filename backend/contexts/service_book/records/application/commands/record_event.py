from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app_platform.contracts.registry import register_command
from contexts.service_book.records.domain.value_objects import ServiceRecordType


class RecordServiceEventCommand(BaseModel):
    command_version: int = Field(default=1, ge=1)
    employee_id: str
    event_type: ServiceRecordType = Field(default=ServiceRecordType.GENERIC)
    record_type: str | None = None
    record_category: str | None = None
    part_code: str | None = None
    payload: dict = Field(default_factory=dict)
    document_ids: list[str] = Field(default_factory=list)
    effective_from: str | None = None
    effective_to: str | None = None
    order_number: str | None = None
    order_date: str | None = None
    issuing_authority: str | None = None
    source_context: str | None = None
    source_reference_id: str | None = None
    source_revision: int | None = None
    correlation_id: str | None = None
    causation_id: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_service_record_aliases(cls, data):
        if not isinstance(data, dict):
            return data
        next_data = dict(data)
        payload = dict(next_data.get("payload") or {})
        record_type = next_data.get("record_type") or payload.get("record_type")
        record_category = next_data.get("record_category") or payload.get("record_category")
        effective_date = next_data.get("effective_date") or payload.get("effective_date")
        for field_name in ("order_number", "order_date", "issuing_authority"):
            value = next_data.get(field_name) or payload.get(field_name)
            if value is not None:
                next_data[field_name] = value
                payload.setdefault(field_name, value)
        if record_type and not next_data.get("event_type"):
            next_data["event_type"] = record_type
        if record_type:
            next_data["record_type"] = record_type
            payload.setdefault("record_type", record_type)
        if record_category:
            next_data["record_category"] = record_category
            payload.setdefault("record_category", record_category)
        if effective_date and not next_data.get("effective_from"):
            next_data["effective_from"] = effective_date
        if next_data.get("document_ids") is not None:
            payload.setdefault("document_ids", next_data.get("document_ids") or [])
        next_data["payload"] = payload
        return next_data


register_command(name="RecordServiceEvent", version="v1", schema=RecordServiceEventCommand)
