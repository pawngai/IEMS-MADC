"""Documents infrastructure service — re-export facade.

Downstream code that imported from ``contexts.documents.infrastructure.service``
continues to work via these re-exports.  New code should import from the
specific sub-modules (storage_ops, metadata_ops, query, lock_ops, event_publish,
access_control) directly.
"""
from __future__ import annotations

from contexts.documents.infrastructure import paths as _paths  # noqa: F401

# ── Path constants — live proxy via __getattr__ ──────────────────────
# Any read of ``service.DOCUMENT_DIR`` etc. delegates to ``paths``, so
# monkeypatching ``paths.DOCUMENT_DIR`` is the single source of truth.
_PATH_ATTRS = {"UPLOAD_DIR", "PHOTO_DIR", "SIGNATURE_DIR", "DOCUMENT_DIR", "DOCUMENT_META_DIR"}


def __getattr__(name: str):
	if name in _PATH_ATTRS:
		return getattr(_paths, name)
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# ── Re-exports from split modules ───────────────────────────────────
from contexts.documents.infrastructure.storage_ops import (  # noqa: F401, E402
	upload_photo,
	upload_signature,
	get_photo,
	get_signature,
	delete_photo,
	delete_signature,
	upload_document,
	get_document,
	download_document,
	get_subject_document,
	download_subject_document,
	delete_document,
	storage as _storage,
)

from contexts.documents.infrastructure.metadata_ops import (  # noqa: F401, E402
	write_document_metadata as _write_document_metadata,
	read_document_metadata as _read_document_metadata,
	read_document_metadata_by_document_id as _read_document_metadata_by_document_id,
	delete_document_metadata as _delete_document_metadata,
	metadata_repository as _metadata_repository,
	file_metadata as _file_metadata,
)

from contexts.documents.infrastructure.event_publish import (  # noqa: F401, E402
	publish_document_event as _publish_document_event,
)

from contexts.documents.infrastructure.access_control import (  # noqa: F401, E402
	can_manage_all_documents as _can_manage_all_documents,
	is_subject_document_owner as _is_subject_document_owner,
	require_document_access as _require_document_access,
	require_subject_document_access as _require_subject_document_access,
	get_user_id as _get_user_id,
	get_employee_id as _get_employee_id,
	get_employee_code as _get_employee_code,
	get_department_id as _get_department_id,
)

from contexts.documents.infrastructure.query import (  # noqa: F401, E402
	list_documents,
	list_subject_documents,
	get_document_metadata,
)

from contexts.documents.infrastructure.lock_ops import (  # noqa: F401, E402
	lock_documents_for_approved_request,
)

from contexts.documents.domain.validation import (  # noqa: F401, E402
	is_document_locked as _is_document_locked,
	extract_filename_from_attachment as _extract_filename,
)

__all__ = [
	"DOCUMENT_DIR",
	"DOCUMENT_META_DIR",
	"UPLOAD_DIR",
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
	"upload_document",
	"upload_photo",
	"upload_signature",
	# Private compat aliases for tests
	"_can_manage_all_documents",
	"_delete_document_metadata",
	"_extract_filename",
	"_file_metadata",
	"_get_department_id",
	"_get_employee_code",
	"_get_employee_id",
	"_get_user_id",
	"_is_document_locked",
	"_is_subject_document_owner",
	"_metadata_repository",
	"_publish_document_event",
	"_read_document_metadata",
	"_read_document_metadata_by_document_id",
	"_require_document_access",
	"_require_subject_document_access",
	"_storage",
	"_write_document_metadata",
]
