from __future__ import annotations

from contexts.employee_master.identity.repository import EmployeeIdentityRepository


async def delete_employee_identity(
    db,
    *,
    employee_id: str,
) -> dict | None:
    repo = EmployeeIdentityRepository(db=db)
    return await repo.delete_identity(employee_id=employee_id)
