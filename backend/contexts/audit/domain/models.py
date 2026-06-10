"""Audit domain models — immutable audit log entry."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ImmutableAuditLog(BaseModel):
    """
    Immutable audit log for all workflow actions.
    Once written, CANNOT be modified or deleted.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # WHO performed the action
    user_id: str
    user_name: str
    user_role: str
    user_authorities: List[str]

    # WHAT was done
    entity_type: str  # EmployeeProfile, ServiceBookEntry
    entity_id: str
    action: str       # submit, verify, approve, reject, attest

    # FROM -> TO status
    from_status: Optional[str] = None
    to_status: Optional[str] = None

    # ADDITIONAL CONTEXT
    remarks: Optional[str] = None
    rejection_reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Computed hash for integrity verification
    integrity_hash: Optional[str] = None

    # Make model immutable after creation
    model_config = ConfigDict(frozen=True)
