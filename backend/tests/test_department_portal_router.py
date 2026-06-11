from __future__ import annotations

import pytest

from contexts.organization_master.api import router as department_router


@pytest.mark.asyncio
async def test_get_employees_route_accepts_service_filter_without_shadowing(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_get_employees(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return {"ok": True, "employees": []}

    monkeypatch.setattr(department_router.department_service, "get_employees", _fake_get_employees)

    db = object()
    current_user = {"sub": "user-1", "authorities": ["DEPT_DATA_ENTRY"]}

    result = await department_router.get_employees(
        q=None,
        search=None,
        service="MCS",
        db=db,
        current_user=current_user,
    )

    assert result == {"ok": True, "employees": []}
    assert captured["db"] is db
    assert captured["current_user"] == current_user
    assert captured["service"] == "MCS"
    assert captured["search"] is None