from __future__ import annotations

import pytest

from contexts.system_admin.api import router as system_admin_router


@pytest.mark.asyncio
async def test_get_workflow_matrix_applies_transition_override(monkeypatch) -> None:
    async def _fake_get_system_config(_db):
        return {
            "workflow_matrix_overrides": {
                "transitions": {
                    "service_book:DRAFT:SUBMITTED": {
                        "authorities": ["HOD"],
                    }
                },
                "sod_rules": {},
            }
        }

    monkeypatch.setattr(system_admin_router, "identity_get_system_config", _fake_get_system_config)

    matrix = await system_admin_router.get_workflow_matrix(
        db=object(),
        current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
    )

    service_book_transitions = matrix["workflows"]["service_book"]["transitions"]
    submit_transition = next(t for t in service_book_transitions if t["from"] == "DRAFT" and t["to"] == "SUBMITTED")
    assert matrix["has_overrides"] is True
    assert submit_transition["required_authorities"] == ["HOD"]
    assert submit_transition["is_overridden"] is True


@pytest.mark.asyncio
async def test_get_workflow_matrix_does_not_leak_override_to_other_workflows(monkeypatch) -> None:
    async def _fake_get_system_config(_db):
        return {
            "workflow_matrix_overrides": {
                "transitions": {
                    "service_book:DRAFT:SUBMITTED": {
                        "authorities": ["HOD"],
                    }
                },
                "sod_rules": {},
            }
        }

    monkeypatch.setattr(system_admin_router, "identity_get_system_config", _fake_get_system_config)

    matrix = await system_admin_router.get_workflow_matrix(
        db=object(),
        current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-1"},
    )

    profile_transitions = matrix["workflows"]["profile"]["transitions"]
    service_book_transitions = matrix["workflows"]["service_book"]["transitions"]

    profile_submit_transition = next(t for t in profile_transitions if t["from"] == "DRAFT" and t["to"] == "SUBMITTED")
    service_book_submit_transition = next(t for t in service_book_transitions if t["from"] == "DRAFT" and t["to"] == "SUBMITTED")

    assert profile_submit_transition["required_authorities"] == ["DEPT_DATA_ENTRY", "GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT"]
    assert profile_submit_transition["is_overridden"] is False
    assert service_book_submit_transition["required_authorities"] == ["HOD"]
    assert service_book_submit_transition["is_overridden"] is True


@pytest.mark.asyncio
async def test_update_transition_override_persists_override(monkeypatch) -> None:
    captured = {}

    async def _fake_get_system_config(_db):
        return {}

    async def _fake_set_system_config_key(db, *, key, value, updated_by, reason):
        captured["db"] = db
        captured["key"] = key
        captured["value"] = value
        captured["updated_by"] = updated_by
        captured["reason"] = reason
        return {"workflow_matrix_overrides": value}

    monkeypatch.setattr(system_admin_router, "identity_get_system_config", _fake_get_system_config)
    monkeypatch.setattr(system_admin_router, "identity_set_system_config_key", _fake_set_system_config_key)

    payload = system_admin_router.TransitionOverrideRequest(
        workflow_type="service_book",
        from_stage="DRAFT",
        to_stage="SUBMITTED",
        authorities=["HOD"],
        reason="Route through HOD in pilot phase",
    )

    result = await system_admin_router.update_transition_override(
        payload=payload,
        db="db-token",
        current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-2"},
    )

    assert result["status"] == "updated"
    assert captured["db"] == "db-token"
    assert captured["key"] == "workflow_matrix_overrides"
    assert captured["updated_by"] == "admin-2"
    assert captured["reason"] == "Route through HOD in pilot phase"
    assert captured["value"]["transitions"]["service_book:DRAFT:SUBMITTED"]["authorities"] == ["HOD"]


@pytest.mark.asyncio
async def test_update_transition_override_rejects_unknown_authority(monkeypatch) -> None:
    async def _fake_get_system_config(_db):
        return {}

    async def _fake_set_system_config_key(db, *, key, value, updated_by, reason):
        _ = (db, key, value, updated_by, reason)
        return {"workflow_matrix_overrides": value}

    monkeypatch.setattr(system_admin_router, "identity_get_system_config", _fake_get_system_config)
    monkeypatch.setattr(system_admin_router, "identity_set_system_config_key", _fake_set_system_config_key)

    payload = system_admin_router.TransitionOverrideRequest(
        workflow_type="service_book",
        from_stage="DRAFT",
        to_stage="SUBMITTED",
        authorities=["NOT_A_REAL_AUTHORITY"],
        reason="Attempting invalid override authority",
    )

    with pytest.raises(system_admin_router.HTTPException) as exc:
        await system_admin_router.update_transition_override(
            payload=payload,
            db="db-token",
            current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-2"},
        )

    assert exc.value.status_code == 400
    assert "Invalid authority" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_update_transition_override_rejects_invalid_transition_for_workflow(monkeypatch) -> None:
    async def _fake_get_system_config(_db):
        return {}

    async def _fake_set_system_config_key(db, *, key, value, updated_by, reason):
        _ = (db, key, value, updated_by, reason)
        return {"workflow_matrix_overrides": value}

    monkeypatch.setattr(system_admin_router, "identity_get_system_config", _fake_get_system_config)
    monkeypatch.setattr(system_admin_router, "identity_set_system_config_key", _fake_set_system_config_key)

    payload = system_admin_router.TransitionOverrideRequest(
        workflow_type="leave",
        from_stage="RECOMMENDED",
        to_stage="LOCKED",
        authorities=["HOD"],
        reason="Attempting invalid leave transition",
    )

    with pytest.raises(system_admin_router.HTTPException) as exc:
        await system_admin_router.update_transition_override(
            payload=payload,
            db="db-token",
            current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-2"},
        )

    assert exc.value.status_code == 400
    assert "Invalid transition for workflow_type" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_reset_workflow_config_clears_overrides(monkeypatch) -> None:
    captured = {}

    async def _fake_set_system_config_key(db, *, key, value, updated_by, reason):
        captured["db"] = db
        captured["key"] = key
        captured["value"] = value
        captured["updated_by"] = updated_by
        captured["reason"] = reason
        return {"workflow_matrix_overrides": value}

    monkeypatch.setattr(system_admin_router, "identity_set_system_config_key", _fake_set_system_config_key)

    payload = system_admin_router.WorkflowConfigResetRequest(
        reason="Rollback all temporary overrides",
    )

    result = await system_admin_router.reset_workflow_config(
        payload=payload,
        db="db-token",
        current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-3"},
    )

    assert result["status"] == "reset"
    assert captured["db"] == "db-token"
    assert captured["key"] == "workflow_matrix_overrides"
    assert captured["value"] == {"transitions": {}, "sod_rules": {}}
    assert captured["updated_by"] == "admin-3"


@pytest.mark.asyncio
async def test_get_workflow_matrix_exposes_frontend_contract_fields(monkeypatch) -> None:
    async def _fake_get_system_config(_db):
        return {"workflow_matrix_overrides": {"transitions": {}, "sod_rules": {}}}

    monkeypatch.setattr(system_admin_router, "identity_get_system_config", _fake_get_system_config)

    matrix = await system_admin_router.get_workflow_matrix(
        db=object(),
        current_user={"authorities": ["SYSTEM_ADMIN"], "sub": "admin-4"},
    )

    assert "authority_permissions" in matrix
    assert "all_permissions" in matrix
    assert "role_permissions" in matrix
    assert "separation_of_duties" in matrix
    assert isinstance(matrix["separation_of_duties"], list)


class _FakeCursor:
    def __init__(self, data):
        self._data = data

    async def to_list(self, length=None):
        _ = length
        return self._data


class _FakeEmploymentTypesCollection:
    def __init__(self, data):
        self._data = data

    def find(self, *args, **kwargs):
        _ = (args, kwargs)
        return _FakeCursor(self._data)


class _FakeDb:
    def __init__(self, employment_types):
        self.employment_types = _FakeEmploymentTypesCollection(employment_types)
