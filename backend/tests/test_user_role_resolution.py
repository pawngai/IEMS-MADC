from contexts.identity.contracts.user_role import get_user_role


def test_get_user_role_uses_priority_without_active_role() -> None:
    user = {
        "authorities": ["EMPLOYEE", "GLOBAL_DATA_ENTRY", "DEPT_DATA_ENTRY"],
    }

    assert get_user_role(user) == "DEPT_DATA_ENTRY"


def test_get_user_role_honors_valid_active_role() -> None:
    user = {
        "authorities": ["EMPLOYEE", "GLOBAL_DATA_ENTRY", "DEPT_DATA_ENTRY"],
        "active_role": "GLOBAL_DATA_ENTRY",
    }

    assert get_user_role(user) == "GLOBAL_DATA_ENTRY"


def test_get_user_role_ignores_invalid_active_role() -> None:
    user = {
        "authorities": ["EMPLOYEE", "GLOBAL_DATA_ENTRY", "DEPT_DATA_ENTRY"],
        "active_role": "SYSTEM_ADMIN",
    }

    assert get_user_role(user) == "DEPT_DATA_ENTRY"
