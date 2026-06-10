from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DocumentUploadedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_version: int = Field(default=1, ge=1)
    document_id: str
    filename: str
    original_name: str
    content_type: str
    file_size: int = Field(ge=0)
    uploaded_at: str
    uploaded_by_user_id: str | None = None
    uploaded_employee_id: str | None = None
    uploaded_employee_code: str | None = None
    subject_employee_id: str | None = None
    subject_employee_code: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    document_type: str | None = None
    category: str | None = None
    source_context: str | None = None
    version_number: int = Field(default=1, ge=1)
    is_current: bool = True
    supersedes_document_id: str | None = None


class DocumentLockedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_version: int = Field(default=1, ge=1)
    document_id: str
    filename: str
    locked_at: str
    lock_reason: str
    locked_by_request_id: str | None = None
    locked_status: str | None = None
    uploaded_employee_id: str | None = None
    uploaded_employee_code: str | None = None
    subject_employee_id: str | None = None
    subject_employee_code: str | None = None
    document_type: str | None = None
    category: str | None = None
    source_context: str | None = None
    version_number: int = Field(default=1, ge=1)
    is_current: bool = True
    supersedes_document_id: str | None = None


class DocumentMetadataUpdatedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_version: int = Field(default=1, ge=1)
    document_id: str
    filename: str
    updated_at: str
    updated_by_user_id: str | None = None
    uploaded_employee_id: str | None = None
    uploaded_employee_code: str | None = None
    subject_employee_id: str | None = None
    subject_employee_code: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    document_type: str | None = None
    category: str | None = None
    source_context: str | None = None
    version_number: int = Field(default=1, ge=1)
    is_current: bool = True
    supersedes_document_id: str | None = None
    updated_fields: list[str] = Field(default_factory=list)


class DocumentDeletedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_version: int = Field(default=1, ge=1)
    document_id: str
    filename: str
    original_name: str | None = None
    deleted_at: str
    deleted_by_user_id: str | None = None
    uploaded_employee_id: str | None = None
    uploaded_employee_code: str | None = None
    subject_employee_id: str | None = None
    subject_employee_code: str | None = None
    document_type: str | None = None
    category: str | None = None
    source_context: str | None = None
    version_number: int = Field(default=1, ge=1)
    is_current: bool = True
    supersedes_document_id: str | None = None


class DocumentLegalHoldAppliedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_version: int = Field(default=1, ge=1)
    document_id: str
    filename: str
    applied_at: str
    applied_by_user_id: str | None = None
    legal_hold_reason: str
    uploaded_employee_id: str | None = None
    uploaded_employee_code: str | None = None
    subject_employee_id: str | None = None
    subject_employee_code: str | None = None
    document_type: str | None = None
    category: str | None = None
    source_context: str | None = None


class DocumentLegalHoldReleasedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_version: int = Field(default=1, ge=1)
    document_id: str
    filename: str
    released_at: str
    released_by_user_id: str | None = None
    release_reason: str | None = None
    uploaded_employee_id: str | None = None
    uploaded_employee_code: str | None = None
    subject_employee_id: str | None = None
    subject_employee_code: str | None = None


class DocumentAccessedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_version: int = Field(default=1, ge=1)
    document_id: str
    filename: str
    accessed_at: str
    accessed_by_user_id: str | None = None
    access_mode: str  # "view" | "download" | "metadata"
    uploaded_employee_id: str | None = None
    subject_employee_id: str | None = None


class DocumentArchivedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_version: int = Field(default=1, ge=1)
    document_id: str
    filename: str
    archived_at: str
    archived_by_user_id: str | None = None
    retention_policy_key: str | None = None
    uploaded_employee_id: str | None = None
    subject_employee_id: str | None = None


class DocumentScanCompletedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_version: int = Field(default=1, ge=1)
    document_id: str
    filename: str
    scanned_at: str
    scan_status: str  # "CLEAN" | "INFECTED" | "ERROR"
    scanner_backend: str
    threat_name: str | None = None


class DocumentExpiringSoonPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_version: int = Field(default=1, ge=1)
    document_id: str
    filename: str
    expires_at: str
    days_until_expiry: int
    stage: str  # e.g. "T-30", "T-7", "T-1"
    uploaded_employee_id: str | None = None
    subject_employee_id: str | None = None
    document_type: str | None = None


class DocumentExpiredPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_version: int = Field(default=1, ge=1)
    document_id: str
    filename: str
    expires_at: str
    expired_at: str
    uploaded_employee_id: str | None = None
    subject_employee_id: str | None = None
    document_type: str | None = None