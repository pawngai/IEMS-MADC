from __future__ import annotations

from contexts.employee_master.profile.api.completion_router import completion_router
from contexts.employee_master.profile.api.read_router import read_router
from fastapi import APIRouter

# Query-only endpoints for employee profile read/completion use cases.
employee_query_router = APIRouter()
employee_query_router.include_router(completion_router)
employee_query_router.include_router(read_router)

__all__ = ["employee_query_router"]
