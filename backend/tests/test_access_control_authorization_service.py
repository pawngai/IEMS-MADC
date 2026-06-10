from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.rbac.application.authorization_service import (
    DEPARTMENT,
    EMPLOYEE,
    GLOBAL,
    canPerformAction,
    resolveScopeAccess,
)
from contexts.rbac.application.access_control import has_active_authority, has_authority


def test_department_scope_denies_when_target_department_mismatches() -> None:
    user = {"authorities": ["HOD"], "department_code": "FIN"}
    scope = resolveScopeAccess(user, target_department_code="HR")
    assert scope["scope"] == DEPARTMENT
    assert scope["allowed"] is False


def test_department_scope_allows_when_departments_match() -> None:
    user = {"authorities": ["HOD"], "department_code": "FIN"}
    scope = resolveScopeAccess(user, target_department_code="FIN")
    assert scope["scope"] == DEPARTMENT
    assert scope["allowed"] is True


def test_department_scope_denies_when_caller_department_missing() -> None:
    user = {"authorities": ["HOD"]}
    scope = resolveScopeAccess(user, target_department_code="FIN")
    assert scope["scope"] == DEPARTMENT
    assert scope["allowed"] is False


def test_employee_scope_requires_self_access() -> None:
    user = {"authorities": ["EMPLOYEE"], "employee_id": "EMP-1"}
    denied = resolveScopeAccess(user, target_employee_id="EMP-2")
    allowed = resolveScopeAccess(user, target_employee_id="EMP-1")

    assert denied["scope"] == EMPLOYEE
    assert denied["allowed"] is False
    assert allowed["scope"] == EMPLOYEE
    assert allowed["allowed"] is True


def test_global_scope_allows_without_target_constraints() -> None:
    user = {"authorities": ["SYSTEM_ADMIN"]}
    scope = resolveScopeAccess(user)
    assert scope["scope"] == GLOBAL
    assert scope["allowed"] is True


def test_mixed_case_hod_normalizes_for_scope_resolution() -> None:
    user = {"authorities": ["hod"], "department_code": "FIN"}
    scope = resolveScopeAccess(user, target_department_code="FIN")
    assert scope["scope"] == DEPARTMENT
    assert scope["allowed"] is True


def test_rbac_has_authority_parity_with_mixed_case_authority() -> None:
    user = {"authorities": ["hod"]}
    assert has_authority(user, "HOD") is True
    assert has_authority(user, "APPROVING_AUTHORITY") is False


def test_rbac_keeps_approving_authority_distinct_from_hod() -> None:
    user = {"authorities": ["APPROVING_AUTHORITY"]}
    assert has_authority(user, "APPROVING_AUTHORITY") is True
    assert has_authority(user, "HOD") is False


def test_has_active_authority_prefers_active_role_when_present() -> None:
    user = {
        "authorities": ["EMPLOYEE", "DEPT_DATA_ENTRY"],
        "active_role": "EMPLOYEE",
    }

    assert has_active_authority(user, "DEPT_DATA_ENTRY") is False
    assert has_active_authority(user, "EMPLOYEE") is True


def test_has_active_authority_falls_back_to_granted_authorities_without_active_role() -> None:
    user = {
        "authorities": ["EMPLOYEE", "DEPT_DATA_ENTRY"],
    }

    assert has_active_authority(user, "DEPT_DATA_ENTRY") is True


def test_has_active_authority_ignores_invalid_active_role_and_uses_authority_list() -> None:
    user = {
        "authorities": ["EMPLOYEE", "DEPT_DATA_ENTRY"],
        "active_role": "SYSTEM_ADMIN",
    }

    assert has_active_authority(user, "DEPT_DATA_ENTRY") is True


def test_can_perform_action_checks_permissions_then_scope() -> None:
    user = {
        "authorities": ["HOD"],
        "department_code": "FIN",
        "permissions": ["LEAVE_READ_ALL"],
    }

    allowed = canPerformAction(
        user,
        required_permissions=["LEAVE_READ_ALL"],
        target_department_code="FIN",
    )
    denied = canPerformAction(
        user,
        required_permissions=["LEAVE_READ_ALL"],
        target_department_code="HR",
    )

    assert allowed is True
    assert denied is False
