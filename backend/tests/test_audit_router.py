from __future__ import annotations

import pytest
from fastapi import HTTPException

from contexts.audit.api import router as audit_router


@pytest.mark.asyncio
async def test_get_audit_logs_requires_audit_read_permission(monkeypatch) -> None:
	async def _should_not_run(*_args, **_kwargs):
		raise AssertionError("buildAuditTrail should not run for unauthorized audit log reads")

	monkeypatch.setattr(audit_router, "buildAuditTrail", _should_not_run)

	with pytest.raises(HTTPException) as exc:
		await audit_router.get_audit_logs(
			resource_type="employee_profile",
			action="UPDATE",
			limit=25,
			db=object(),
			current_user={"sub": "u-1", "permissions": []},
		)

	assert exc.value.status_code == 403
	assert exc.value.detail["error_code"] == "INSUFFICIENT_PERMISSION"
	assert exc.value.detail["required_permissions"] == ["AUDIT_READ_ALL"]


@pytest.mark.asyncio
async def test_get_service_book_logs_requires_audit_read_permission(monkeypatch) -> None:
	async def _should_not_run(*_args, **_kwargs):
		raise AssertionError("buildAuditTrail should not run for unauthorized service-book audit reads")

	monkeypatch.setattr(audit_router, "buildAuditTrail", _should_not_run)

	with pytest.raises(HTTPException) as exc:
		await audit_router.get_service_book_logs(
			employee_id="EMP-1",
			limit=10,
			db=object(),
			current_user={"sub": "u-2", "permissions": []},
		)

	assert exc.value.status_code == 403
	assert exc.value.detail["error_code"] == "INSUFFICIENT_PERMISSION"
	assert exc.value.detail["required_permissions"] == ["AUDIT_READ_ALL"]


@pytest.mark.asyncio
async def test_get_audit_logs_delegates_after_router_permission_check(monkeypatch) -> None:
	async def _fake_build_audit_trail(db, **kwargs):
		assert db == "db-handle"
		assert kwargs["current_user"]["permissions"] == ["AUDIT_READ_ALL"]
		assert kwargs["resource_type"] == "employee_profile"
		assert kwargs["action"] == "UPDATE"
		assert kwargs["limit"] == 15
		return [{"source": "router"}]

	monkeypatch.setattr(audit_router, "buildAuditTrail", _fake_build_audit_trail)

	result = await audit_router.get_audit_logs(
		resource_type="employee_profile",
		action="UPDATE",
		limit=15,
		db="db-handle",
		current_user={"sub": "u-3", "permissions": ["AUDIT_READ_ALL"]},
	)

	assert result == [{"source": "router"}]