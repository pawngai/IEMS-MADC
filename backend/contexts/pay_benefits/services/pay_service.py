from __future__ import annotations

from typing import Any

from contexts.pay_benefits.contracts.dto import AllowanceChangeCreateDTO, PayRevisionCreateDTO


async def computePayRecord(*, service, employee_id: str, current_user: dict) -> dict[str, Any]:
    # Pay context owns salary/pay records; this computes the canonical current pay snapshot.
    return await service.get_pay_snapshot(employee_id, current_user=current_user)


async def applyPayChange(
    *,
    service,
    payload: PayRevisionCreateDTO | AllowanceChangeCreateDTO,
    current_user: dict,
) -> dict[str, Any]:
    if isinstance(payload, PayRevisionCreateDTO):
        return await service.revise_pay(payload, current_user=current_user)
    return await service.change_allowance(payload, current_user=current_user)
