from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class DocumentMetadataDTO:
    document_id: str
    filename: str
    original_name: str
    content_type: str
    file_size: int
    uploaded_at: Optional[str] = None
    uploaded_by_user_id: Optional[str] = None
    uploaded_employee_id: Optional[str] = None
    uploaded_employee_code: Optional[str] = None
    subject_employee_id: Optional[str] = None
    subject_employee_code: Optional[str] = None
    is_locked: bool = False
    locked_at: Optional[str] = None
    lock_reason: Optional[str] = None
    locked_by_request_id: Optional[str] = None
