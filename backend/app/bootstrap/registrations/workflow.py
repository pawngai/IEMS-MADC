from __future__ import annotations

from contexts.audit.api.router import audit_router
from contexts.documents.api.router import documents_router
from app_platform.forms.api.router import forms_router
from app_platform.reference_data.api.router import versioned_masters_router
from contexts.workflow.api.router import workflow_router
from fastapi import APIRouter


def register(api_router: APIRouter) -> None:
    api_router.include_router(audit_router)
    api_router.include_router(forms_router)
    api_router.include_router(workflow_router)
    api_router.include_router(documents_router)
    api_router.include_router(versioned_masters_router)

