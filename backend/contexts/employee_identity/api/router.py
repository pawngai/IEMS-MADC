from __future__ import annotations

from fastapi import APIRouter

from contexts.employee_identity.api.read_router import read_router
from contexts.employee_identity.api.write_router import write_router


employee_identities_router = APIRouter(
    prefix="/employee-identities",
    tags=["Employee Identities"],
)
employee_identities_router.include_router(read_router)
employee_identities_router.include_router(write_router)

__all__ = ["employee_identities_router"]
