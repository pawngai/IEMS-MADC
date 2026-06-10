from __future__ import annotations

from contexts.identity_access.rbac.domain.models import Permission
from app_platform.forms.api import helpers as forms_helpers
from contexts.identity_access.rbac.policies import operational


def test_require_forms_access_uses_identity_aliases(monkeypatch) -> None:
    recorded: list[Permission] = []

    def _fake_require_permissions(current_user: dict, *permissions: Permission) -> None:
        assert current_user == {"sub": "user-1"}
        recorded.extend(permissions)

    monkeypatch.setattr(forms_helpers, "require_permissions", _fake_require_permissions)

    forms_helpers.require_forms_access({"sub": "user-1"})

    assert recorded[:3] == [
        Permission.IDENTITY_READ_OWN,
        Permission.IDENTITY_READ_ALL,
        Permission.IDENTITY_CREATE,
    ]
    assert recorded[3:] == [
        Permission.PROFILE_UPDATE_OWN_LIMITED,
        Permission.PROFILE_UPDATE_ALL,
    ]


def test_can_read_pay_uses_identity_read_own_for_self(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake_can_perform_action(current_user: dict, **kwargs):
        captured["current_user"] = current_user
        captured.update(kwargs)
        return True

    monkeypatch.setattr(operational, "canPerformAction", _fake_can_perform_action)

    assert operational.can_read_pay(
        current_user={"employee_id": "EMP-1", "permissions": [Permission.IDENTITY_READ_OWN.value]},
        employee_id="EMP-1",
    ) is True
    assert captured["required_permissions"] == [Permission.IDENTITY_READ_OWN.value]
    assert captured["target_employee_id"] == "EMP-1"


def test_can_read_pay_uses_identity_read_all_for_admin_lookup(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake_can_perform_action(current_user: dict, **kwargs):
        captured["current_user"] = current_user
        captured.update(kwargs)
        return True

    monkeypatch.setattr(operational, "canPerformAction", _fake_can_perform_action)

    assert operational.can_read_pay(
        current_user={"employee_id": "EMP-1", "permissions": [Permission.IDENTITY_READ_ALL.value]},
        employee_id="EMP-9",
    ) is True
    assert captured["required_permissions"] == [
        Permission.IDENTITY_READ_ALL.value,
        Permission.SERVICE_BOOK_READ_ALL.value,
        Permission.ESTABLISHMENT_PAY_FIXATION.value,
    ]
    assert captured["target_employee_id"] == "EMP-9"