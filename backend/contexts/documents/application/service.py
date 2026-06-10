"""Documents application service — orchestration and query re-exports.

Commands (write operations) live in ``application.commands``.
Infrastructure query/storage ops are re-exported for read consumers.
"""
from __future__ import annotations

from contexts.documents.application.commands import (  # noqa: F401
    attach_document_to_entity,
    validate_document_metadata,
)

from contexts.documents.infrastructure.storage_ops import (  # noqa: F401, E402
    delete_photo,
    delete_signature,
    download_document,
    download_subject_document,
    get_document,
    get_photo,
    get_signature,
    get_subject_document,
    upload_document,
    upload_photo,
    upload_signature,
    delete_document,
)

from contexts.documents.infrastructure.query import (  # noqa: F401, E402
    get_document_metadata,
    list_documents,
    list_subject_documents,
)

from contexts.documents.infrastructure.lock_ops import (  # noqa: F401, E402
    apply_legal_hold,
    lock_documents_for_approved_request,
    release_legal_hold,
)

__all__ = [
    "apply_legal_hold",
    "attach_document_to_entity",
    "delete_document",
    "delete_photo",
    "delete_signature",
    "download_document",
    "download_subject_document",
    "get_document",
    "get_document_metadata",
    "get_photo",
    "get_signature",
    "get_subject_document",
    "list_documents",
    "list_subject_documents",
    "lock_documents_for_approved_request",
    "release_legal_hold",
    "upload_document",
    "upload_photo",
    "upload_signature",
    "validate_document_metadata",
]
