"""Documents application — template render orchestration."""
from __future__ import annotations

import io
import uuid
from datetime import datetime, timezone
from typing import Any

from contexts.documents.domain.template import (
    can_substitute_inline,
    render_text,
    validate_render_values,
)
from contexts.documents.infrastructure.access_control import (
    can_manage_all_documents,
    get_employee_code,
    get_employee_id,
    get_user_id,
)
from contexts.documents.infrastructure.metadata_ops import write_document_metadata
from contexts.documents.infrastructure.storage import StorageBucket
from contexts.documents.infrastructure.storage_ops import storage
from contexts.documents.repository.template_repository import DocumentTemplateRepository
from fastapi import HTTPException


async def render_template(
    *,
    template_id: str,
    values: dict[str, Any],
    current_user: dict,
    db,
    entity_type: str | None = None,
    entity_id: str | None = None,
    subject_employee_code: str | None = None,
) -> dict[str, Any]:
    if not can_manage_all_documents(current_user):
        raise HTTPException(
            status_code=403,
            detail="Only document managers may render templates",
        )

    template = await DocumentTemplateRepository(db=db).get(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")

    normalized_values = validate_render_values(template, values or {})
    s = storage()
    if not s.exists(StorageBucket.DOCUMENT, template.base_filename):
        raise HTTPException(
            status_code=500,
            detail=f"Template base file '{template.base_filename}' is missing from storage",
        )

    base_bytes = s.read_bytes(StorageBucket.DOCUMENT, template.base_filename)

    if can_substitute_inline(template.content_type):
        try:
            rendered = render_text(base_bytes, normalized_values)
        except KeyError as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Template references undefined placeholder: {exc.args[0]}",
            ) from exc
    else:
        # Binary templates (PDF/Office) are passed through; the field values
        # are persisted on metadata so downstream tooling can complete the
        # fill out-of-band.
        rendered = base_bytes

    now = datetime.now(timezone.utc).isoformat()
    rendered_filename = _build_rendered_filename(template.base_filename, template_id, now)
    document_id = uuid.uuid4().hex
    s.write_bytes(
        StorageBucket.DOCUMENT,
        rendered_filename,
        rendered,
        content_type=template.content_type,
    )

    metadata = {
        "document_id": document_id,
        "filename": rendered_filename,
        "original_name": f"{template.name}.rendered",
        "content_type": template.content_type,
        "file_size": len(rendered),
        "uploaded_by_user_id": get_user_id(current_user),
        "uploaded_employee_id": get_employee_id(current_user),
        "uploaded_employee_code": get_employee_code(current_user),
        "uploaded_at": now,
        "document_type": template.document_type,
        "source_context": "documents.template",
        "tags": ["template-rendered"],
        "template_id": template_id,
        "template_field_values": normalized_values,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "subject_employee_code": subject_employee_code,
        "version_number": 1,
        "is_current": True,
        "scan_status": "CLEAN",
        "scan_completed_at": now,
    }
    await write_document_metadata(rendered_filename, metadata, db=db)

    return {
        "success": True,
        "document_id": document_id,
        "filename": rendered_filename,
        "url": f"/api/documents/files/{rendered_filename}",
        "template_id": template_id,
        "values": normalized_values,
    }


def _build_rendered_filename(base_filename: str, template_id: str, now_iso: str) -> str:
    stem, sep, ext = base_filename.rpartition(".")
    suffix = uuid.uuid4().hex[:8]
    if not sep:
        return f"{template_id}_{suffix}_{now_iso[:10]}"
    return f"{template_id}_{suffix}_{now_iso[:10]}.{ext}"
