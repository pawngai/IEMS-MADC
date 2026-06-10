from __future__ import annotations

from app.bootstrap.core_router import core_router
from fastapi import APIRouter

router = APIRouter()
router.include_router(core_router)



