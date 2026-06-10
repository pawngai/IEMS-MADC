from __future__ import annotations

from contexts.change_requests.api.router import (
    change_request_admin_router,
    change_request_ess_router,
)
from app.bootstrap.registrations import (
    core,
    department,
    employee_identity,
    employee_profile,
    ess,
    identity,
    leave,
    pay,
    reporting,
    seniority,
    service_book,
    system_admin,
    workflow,
)
from app.bootstrap.router import router as bootstrap_router
from fastapi import APIRouter


def build_api_router() -> APIRouter:
    api_router = APIRouter(prefix="/api")
    api_router.include_router(bootstrap_router)

    # Preserve historical include order from backend/server.py.
    core.register(api_router)
    employee_identity.register(api_router)
    employee_profile.register(api_router)
    department.register(api_router)
    workflow.register(api_router)
    system_admin.register(api_router)
    seniority.register(api_router)
    leave.register(api_router)
    pay.register(api_router)
    identity.register(api_router)
    ess.register(api_router)
    api_router.include_router(change_request_ess_router)
    api_router.include_router(change_request_admin_router)
    service_book.register(api_router)
    reporting.register(api_router)
    return api_router
