from __future__ import annotations

from contexts.rbac.domain.models import AUTHORITY_PERMISSIONS, Authority, Permission


def test_employee_authority_can_complete_own_profile_section() -> None:
    employee_permissions = AUTHORITY_PERMISSIONS[Authority.EMPLOYEE]

    assert Permission.PROFILE_READ_OWN in employee_permissions
    assert Permission.PROFILE_UPDATE_OWN_LIMITED in employee_permissions
    assert Permission.DOCUMENT_READ_OWN in employee_permissions


def test_global_data_entry_can_submit_service_book_entries() -> None:
    global_data_entry_permissions = AUTHORITY_PERMISSIONS[Authority.GLOBAL_DATA_ENTRY]

    assert Permission.SERVICE_BOOK_ENTRY_CREATE in global_data_entry_permissions
    assert Permission.SERVICE_BOOK_ENTRY_SUBMIT in global_data_entry_permissions
    assert Permission.SERVICE_BOOK_OPENING_CREATE in global_data_entry_permissions
    assert Permission.SERVICE_BOOK_OPENING_UPDATE in global_data_entry_permissions
    assert Permission.SERVICE_BOOK_OPENING_SUBMIT in global_data_entry_permissions


def test_service_book_opening_permissions_are_limited_to_global_and_dealing_data_entry_authorities() -> None:
    opening_permissions = {
        Permission.SERVICE_BOOK_OPENING_CREATE,
        Permission.SERVICE_BOOK_OPENING_UPDATE,
        Permission.SERVICE_BOOK_OPENING_SUBMIT,
    }

    allowed_authorities = [
        Authority.GLOBAL_DATA_ENTRY,
        Authority.DEALING_ASSISTANT,
    ]

    for authority in allowed_authorities:
        assert {
            Permission.SERVICE_BOOK_OPENING_CREATE,
            Permission.SERVICE_BOOK_OPENING_UPDATE,
            Permission.SERVICE_BOOK_OPENING_SUBMIT,
        }.issubset(AUTHORITY_PERMISSIONS[authority])

    blocked_authorities = [
        Authority.DEPT_DATA_ENTRY,
        Authority.SECTION_OFFICER,
        Authority.VERIFIER,
        Authority.DDO,
        Authority.APPROVING_AUTHORITY,
        Authority.HOD,
    ]

    for authority in blocked_authorities:
        assert AUTHORITY_PERMISSIONS[authority].isdisjoint(opening_permissions)


def test_service_book_opening_verify_permission_is_limited_to_verifier_authority() -> None:
    assert Permission.SERVICE_BOOK_OPENING_VERIFY in AUTHORITY_PERMISSIONS[Authority.VERIFIER]

    blocked_authorities = [
        Authority.DEPT_DATA_ENTRY,
        Authority.GLOBAL_DATA_ENTRY,
        Authority.DEALING_ASSISTANT,
        Authority.SECTION_OFFICER,
        Authority.DDO,
        Authority.APPROVING_AUTHORITY,
        Authority.HOD,
    ]

    for authority in blocked_authorities:
        assert Permission.SERVICE_BOOK_OPENING_VERIFY not in AUTHORITY_PERMISSIONS[authority]


def test_service_book_opening_approve_permission_is_limited_to_ddo_and_approving_authority() -> None:
    allowed_authorities = [
        Authority.DDO,
        Authority.APPROVING_AUTHORITY,
    ]

    for authority in allowed_authorities:
        assert Permission.SERVICE_BOOK_OPENING_APPROVE in AUTHORITY_PERMISSIONS[authority]

    blocked_authorities = [
        Authority.DEPT_DATA_ENTRY,
        Authority.GLOBAL_DATA_ENTRY,
        Authority.DEALING_ASSISTANT,
        Authority.SECTION_OFFICER,
        Authority.VERIFIER,
        Authority.HOD,
    ]

    for authority in blocked_authorities:
        assert Permission.SERVICE_BOOK_OPENING_APPROVE not in AUTHORITY_PERMISSIONS[authority]
