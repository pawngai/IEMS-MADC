from __future__ import annotations

from contexts.employee_identity.schemas.enums import (
    EmployeeStatus as IdentityEmployeeStatus,
    EmploymentType as IdentityEmploymentType,
    Gender as IdentityGender,
)
from contexts.employee_profile.schemas.profile_model import (
    EmployeeStatus as ProfileEmployeeStatus,
    EmploymentType as ProfileEmploymentType,
    Gender as ProfileGender,
)


def _enum_values(enum_cls) -> set[str]:
    return {member.value for member in enum_cls}


def test_profile_identity_snapshot_enums_match_canonical_identity_values() -> None:
    assert _enum_values(ProfileEmploymentType) == _enum_values(IdentityEmploymentType)
    assert _enum_values(ProfileEmployeeStatus) == _enum_values(IdentityEmployeeStatus)
    assert _enum_values(ProfileGender) == _enum_values(IdentityGender)
