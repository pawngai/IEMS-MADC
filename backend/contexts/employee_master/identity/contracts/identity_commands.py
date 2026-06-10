from __future__ import annotations

from contexts.employee_master.identity.application.admin_service import delete_employee_identity as _delete_employee_identity


async def delete_identity(
    db,
    *,
    employee_id: str,
) -> dict | None:
    return await _delete_employee_identity(db, employee_id=employee_id)


__all__ = ["delete_identity"]