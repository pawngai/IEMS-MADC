from __future__ import annotations


async def lock_documents_for_approved_request(*args, **kwargs):
	from contexts.documents.application.service import (
		lock_documents_for_approved_request as _lock_documents_for_approved_request,
	)

	return await _lock_documents_for_approved_request(*args, **kwargs)


__all__ = ["lock_documents_for_approved_request"]