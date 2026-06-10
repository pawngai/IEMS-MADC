from __future__ import annotations

from typing import List

from app_platform.db.runtime import get_db
from contexts.pay.application.service import PayApplicationService
from contexts.pay.contracts.dto import (
    AllowanceChangeCreateDTO,
    PayLedgerEntryResponseDTO,
    PayRevisionCreateDTO,
    PaySnapshotResponseDTO,
)
from contexts.pay.infrastructure.gateway import PayMongoGateway
from contexts.rbac.contracts.operational import can_read_pay, require_pay_write
from fastapi import APIRouter, Depends, HTTPException, Request
from app_platform.auth.current_user import get_current_user

pay_router = APIRouter(prefix="/pay", tags=["Pay Management"])


def get_pay_service(request: Request, db=Depends(get_db)) -> PayApplicationService:
    container = getattr(request.app.state, "container", None)
    outbox_repo = container.outbox_repo if container is not None else None
    gateway = PayMongoGateway(db=db)
    return PayApplicationService(gateway=gateway, outbox_repo=outbox_repo)


def _require_pay_read_access(current_user: dict, employee_id: str) -> None:
    if can_read_pay(current_user=current_user, employee_id=employee_id):
        return
    raise HTTPException(status_code=403, detail="Insufficient permission to view pay records")


def _require_pay_write_access(current_user: dict) -> None:
    require_pay_write(current_user)


@pay_router.post("/revisions", response_model=PayLedgerEntryResponseDTO)
async def revise_pay(
    payload: PayRevisionCreateDTO,
    service: PayApplicationService = Depends(get_pay_service),
    current_user: dict = Depends(get_current_user),
):
    _require_pay_write_access(current_user)
    return await service.revise_pay(payload, current_user=current_user)


@pay_router.post("/allowances", response_model=PayLedgerEntryResponseDTO)
async def change_allowance(
    payload: AllowanceChangeCreateDTO,
    service: PayApplicationService = Depends(get_pay_service),
    current_user: dict = Depends(get_current_user),
):
    _require_pay_write_access(current_user)
    return await service.change_allowance(payload, current_user=current_user)


@pay_router.get("/ledger/{employee_id}", response_model=List[PayLedgerEntryResponseDTO])
async def list_pay_ledger_entries(
    employee_id: str,
    service: PayApplicationService = Depends(get_pay_service),
    current_user: dict = Depends(get_current_user),
):
    _require_pay_read_access(current_user, employee_id)
    return await service.list_ledger_entries(employee_id, current_user=current_user)


@pay_router.get("/snapshot/{employee_id}", response_model=PaySnapshotResponseDTO)
async def get_pay_snapshot(
    employee_id: str,
    service: PayApplicationService = Depends(get_pay_service),
    current_user: dict = Depends(get_current_user),
):
    _require_pay_read_access(current_user, employee_id)
    return await service.get_pay_snapshot(employee_id,
        current_user=current_user,
    )
