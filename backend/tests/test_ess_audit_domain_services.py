from __future__ import annotations

import pytest
from fastapi import HTTPException

from contexts.audit.services import audit_service as audit_domain
from contexts.ess.services import ess_service as ess_domain


def test_ess_self_scope_rejects_cross_employee() -> None:
    with pytest.raises(HTTPException):
        ess_domain._assert_self_scope(
            {"employee_id": "EMP-1"},
            employee_id="EMP-2",
        )


@pytest.mark.asyncio
async def test_build_audit_trail_routes(monkeypatch) -> None:
    async def _fake_get_audit_logs(*_args, **_kwargs):
        return [{"source": "audit"}]

    async def _fake_get_service_book_logs(*_args, **_kwargs):
        return [{"source": "service_book"}]

    monkeypatch.setattr(audit_domain.audit_app_service, "get_audit_logs", _fake_get_audit_logs)
    monkeypatch.setattr(
        audit_domain.audit_app_service,
        "get_service_book_logs",
        _fake_get_service_book_logs,
    )

    generic = await audit_domain.buildAuditTrail(
        object(),
        current_user={"sub": "u1"},
        resource_type="employee_profile",
        limit=10,
    )
    service_book = await audit_domain.buildAuditTrail(
        object(),
        current_user={"sub": "u1"},
        resource_type="service_book",
        employee_id="EMP-1",
        limit=10,
    )

    assert generic[0]["source"] == "audit"
    assert service_book[0]["source"] == "service_book"
