"""Cross-context contract: read the per-document audit timeline."""
from __future__ import annotations

from typing import Any


async def list_audit_timeline_for_document(
    *,
    db,
    document_id: str | None = None,
    filename: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    from contexts.documents.repository import DocumentAuditTimelineRepository

    return await DocumentAuditTimelineRepository(db=db).list_for_document(
        document_id=document_id,
        filename=filename,
        limit=limit,
    )


__all__ = ["list_audit_timeline_for_document"]
