from __future__ import annotations

import pytest
from fastapi import HTTPException

from contexts.system_admin.department.api.management_helpers import (
    ensure_distinct_role_holders,
)


def test_ensure_distinct_role_holders_rejects_same_employee_for_both_roles() -> None:
    with pytest.raises(HTTPException) as exc:
        ensure_distinct_role_holders(
            hod_employee_id="EMP-1",
            data_entry_employee_id="EMP-1",
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == (
        "The same employee cannot hold both HOD and Data Entry Operator roles in a department."
    )