"""Documents contracts."""

from contexts.documents.contracts.events import (
	DocumentDeletedPayload,
	DocumentLockedPayload,
	DocumentMetadataUpdatedPayload,
	DocumentUploadedPayload,
)
from contexts.documents.contracts.document_metadata import (
	download_subject_document_for_employee,
	get_accessible_document_metadata,
	get_subject_document_for_employee,
	list_subject_documents_for_employee,
)
from contexts.documents.contracts.document_lock import lock_documents_for_approved_request


__all__ = [
	"DocumentDeletedPayload",
	"DocumentLockedPayload",
	"DocumentMetadataUpdatedPayload",
	"DocumentUploadedPayload",
	"download_subject_document_for_employee",
	"get_accessible_document_metadata",
	"get_subject_document_for_employee",
	"list_subject_documents_for_employee",
	"lock_documents_for_approved_request",
]
