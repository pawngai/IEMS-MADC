from __future__ import annotations

import asyncio

from app_platform.db.runtime import get_db_optional
from fastapi import APIRouter, Depends, HTTPException
from contexts.rbac.domain.models import Permission
from contexts.rbac.application.access_control import get_permissions
from app_platform.auth.current_user import get_current_user

core_router = APIRouter()


@core_router.get("/")
async def root():
    return {
        "message": "MADC-HRMS API",
        "version": "2.0.0",
        "compliance": ["Service Book Rules", "Authority-Based RBAC"],
    }


@core_router.get("/health")
async def health():
    return {"status": "healthy"}


@core_router.get("/dashboard/stats")
async def get_dashboard_stats(
    db=Depends(get_db_optional), current_user: dict = Depends(get_current_user)
):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    permissions = get_permissions(current_user)
    stats: dict = {"user_authorities": current_user.get("authorities", [])}

    tasks: dict[str, any] = {}
    if Permission.IDENTITY_READ_ALL.value in permissions:
        tasks["total_employees"] = db.employee_identities.count_documents({})
    if Permission.AUDIT_READ_ALL.value in permissions:
        tasks["total_audit_logs"] = db.audit_logs.count_documents({})

    if tasks:
        keys = list(tasks.keys())
        results = await asyncio.gather(*tasks.values())
        for key, val in zip(keys, results):
            stats[key] = val

    return stats
