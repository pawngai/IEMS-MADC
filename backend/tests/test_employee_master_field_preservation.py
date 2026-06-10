"""Phase 1 guardrail: prove employee_master preserves every legacy field.

Asserts that every field declared in the legacy employee_identity and
employee_profile schemas (plus the write-path upsert/policy surface) is
representable in EmployeeMasterSnapshot — either as a top-level field, inside the
embedded `contact`/`identifiers` objects, or (by design) under `legacy_fields`.

This is the executable form of docs/refactor/employee_identity_profile_field_mapping.md.
If this test fails, a field was about to be lost.
"""

from __future__ import annotations

from contexts.employee_master.schemas.commands import (
    EmployeeMasterCreate,
    EmployeeMasterUpdate,
)
from contexts.employee_master.schemas.employee_master_model import EmployeeMasterSnapshot
from contexts.employee_master.schemas.value_objects import (
    ContactDetails as MasterContact,
    IdentityDocuments as MasterIds,
)

# Legacy sources
from contexts.employee_identity.schemas.identity_model import (
    EmployeeIdentity as LegacyIdentity,
)
from contexts.employee_identity.schemas.commands import EmployeeIdentityCreate
from contexts.employee_profile.schemas.profile_model import (
    EmployeeProfileExtension as LegacyExtension,
    EmployeeIdentity as LegacyProfileSnapshot,
    ContactDetails as LegacyContact,
    IdentityDocuments as LegacyIds,
)
from contexts.employee_profile.schemas.commands import EmployeeProfileExtensionUpsert
from contexts.employee_profile.schemas.field_policies import (
    PROFILE_EXTENSION_EDITABLE_FIELDS,
)


def _master_fields() -> set[str]:
    return set(EmployeeMasterSnapshot.model_fields.keys())


def _master_contact_fields() -> set[str]:
    return set(MasterContact.model_fields.keys())


def _master_identifier_fields() -> set[str]:
    return set(MasterIds.model_fields.keys())


def _representable(field: str) -> bool:
    """A field is preserved if it lands top-level, in contact, in identifiers,
    or is the legacy_fields catch-all itself."""
    return (
        field in _master_fields()
        or field in _master_contact_fields()
        or field in _master_identifier_fields()
        or field == "legacy_fields"
    )


def test_master_snapshot_covers_identity_doc():
    missing = {f for f in LegacyIdentity.model_fields if not _representable(f)}
    assert not missing, f"identity fields not preserved: {sorted(missing)}"


def test_master_snapshot_covers_profile_snapshot():
    missing = {f for f in LegacyProfileSnapshot.model_fields if not _representable(f)}
    assert not missing, f"profile snapshot fields not preserved: {sorted(missing)}"


def test_master_snapshot_covers_profile_extension():
    missing = {f for f in LegacyExtension.model_fields if not _representable(f)}
    assert not missing, f"extension fields not preserved: {sorted(missing)}"


def test_master_covers_legacy_contact_and_identifiers():
    missing_contact = {
        f for f in LegacyContact.model_fields if f not in _master_contact_fields()
    }
    missing_ids = {
        f for f in LegacyIds.model_fields if f not in _master_identifier_fields()
    }
    assert not missing_contact, f"contact fields lost: {sorted(missing_contact)}"
    assert not missing_ids, f"identifier fields lost: {sorted(missing_ids)}"


def test_master_covers_upsert_and_policy_surface():
    """The 35 employment-type fields + flat contact fields accepted by the write
    path must all be representable."""
    surface = set(EmployeeProfileExtensionUpsert.model_fields.keys())
    surface |= set(PROFILE_EXTENSION_EDITABLE_FIELDS)
    missing = {f for f in surface if not _representable(f)}
    assert not missing, f"write-path fields not preserved: {sorted(missing)}"


def test_create_command_is_identity_first_subset():
    """EmployeeMasterCreate keeps the identity-first contract (same keys as the
    legacy identity create)."""
    assert set(EmployeeMasterCreate.model_fields.keys()) == set(
        EmployeeIdentityCreate.model_fields.keys()
    )


def test_update_command_covers_all_editable_fields():
    editable = set(PROFILE_EXTENSION_EDITABLE_FIELDS)
    update_fields = set(EmployeeMasterUpdate.model_fields.keys())
    # every data-entry editable field is accepted by the update command
    missing = {f for f in editable if f not in update_fields}
    assert not missing, f"update command missing editable fields: {sorted(missing)}"
