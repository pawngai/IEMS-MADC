from __future__ import annotations

from app.bootstrap.registrations import department as department_registration
from app.bootstrap.registrations import employee_profile as employee_profile_registration
from app.bootstrap.registrations import system_admin as system_admin_registration


class _FakeApiRouter:
    def __init__(self) -> None:
        self.included = []

    def include_router(self, router) -> None:
        self.included.append(router)


def test_employee_profile_registration_owns_employee_profile_routes() -> None:
    api_router = _FakeApiRouter()

    employee_profile_registration.register(api_router)

    prefixes = [router.prefix for router in api_router.included]
    assert "/employee-profiles" in prefixes
    assert "/departments/manage" not in prefixes


def test_department_registration_owns_department_portal_routes() -> None:
    api_router = _FakeApiRouter()

    department_registration.register(api_router)

    prefixes = [router.prefix for router in api_router.included]
    assert "/department" in prefixes
    assert "/departments/manage" not in prefixes


def test_system_admin_registration_owns_department_governance_routes() -> None:
    api_router = _FakeApiRouter()

    system_admin_registration.register(api_router)

    prefixes = [router.prefix for router in api_router.included]
    assert "/system-admin" in prefixes
    assert "/sysadmin" not in prefixes
    assert "/departments/manage" in prefixes