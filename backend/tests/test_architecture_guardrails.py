from __future__ import annotations

import asyncio
import ast
import re
from pathlib import Path

import pytest
from fastapi import HTTPException

from contexts.service_book.application.service import createServiceBookIfEligible
from contexts.documents.application.commands import validate_document_metadata
from contexts.workflow.services import workflow_service


BACKEND_ROOT = Path(__file__).resolve().parents[1]
CONTEXTS_ROOT = BACKEND_ROOT / "contexts"
WORKSPACE_ROOT = BACKEND_ROOT.parent

CROSS_CONTEXT_REPO_IMPORT = re.compile(
    r"^contexts\.([a-z_]+)\.infrastructure\.(repo|repository|repositories)(\.|$)"
)

AUTH_BYPASS_ALLOWED_FILES = {
    "contexts/identity_access/rbac/application/access_control.py",
    "contexts/identity_access/rbac/application/authorization_service.py",
    # Audit logs capture caller authority label; this is metadata, not authorization logic.
    "contexts/audit/api/router.py",
}

DEPRECATED_AUTH_IMPORTS = {
    "shared.auth",
    "shared.permissions",
    "models.auth_rbac",
    "app.security.policy_enforcer",
}

GENERIC_PROFILE_PERMISSION_TOKENS = {
    "Permission.PROFILE_READ_OWN",
    "Permission.PROFILE_READ_ALL",
    "Permission.PROFILE_CREATE",
    "Permission.PROFILE_UPDATE_ALL",
}

ALLOWED_GENERIC_PROFILE_PERMISSION_USAGE = {
    "app_platform/forms/api/helpers.py": {"Permission.PROFILE_UPDATE_ALL"},
    "contexts/change_requests/api/router.py": {
        "Permission.PROFILE_READ_OWN",
        "Permission.PROFILE_READ_ALL",
        "Permission.PROFILE_UPDATE_ALL",
    },
    "contexts/employee_master/profile/application/audit_delete.py": {
        "Permission.PROFILE_READ_OWN",
        "Permission.PROFILE_READ_ALL",
    },
    "contexts/employee_master/profile/application/read_profiles.py": {
        "Permission.PROFILE_READ_OWN",
        "Permission.PROFILE_READ_ALL",
    },
    "contexts/employee_master/profile/application/update_profile_extension.py": {
        "Permission.PROFILE_UPDATE_ALL",
    },
    "contexts/organization_master/services/sanctioned_strength_service.py": {
        "Permission.PROFILE_UPDATE_ALL",
    },
    # Reporting/analytics reads across all employees — read-only aggregation.
    "contexts/reporting_analytics/api/router.py": {
        "Permission.PROFILE_READ_ALL",
    },
}


class _FakePartProjectionCollection:
    def __init__(self) -> None:
        self.calls: list[tuple[dict, dict, bool]] = []

    async def update_one(self, query, update, upsert: bool = False):
        self.calls.append((query, update, upsert))


class _FakeDb:
    def __init__(self) -> None:
        self.service_book_part_projections = _FakePartProjectionCollection()


def _iter_context_py_files():
    for file_path in CONTEXTS_ROOT.rglob("*.py"):
        if "__pycache__" in file_path.parts:
            continue
        yield file_path


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8-sig").splitlines())


def _imports_from_ast(file_path: Path) -> list[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8-sig"), filename=str(file_path))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    return imported


def test_refactor_facades_stay_thin() -> None:
    facades = {
        "backend/app_platform/reference_data/infrastructure/employee_form_schema.py": 80,
        "backend/contexts/organization_master/services/department_portal_service.py": 240,
    }
    violations = []
    for rel_path, max_lines in facades.items():
        path = WORKSPACE_ROOT / rel_path
        line_count = _line_count(path)
        if line_count > max_lines:
            violations.append(f"{rel_path}: {line_count} lines (max {max_lines})")

    assert not violations, (
        "Compatibility facades must stay thin; move feature logic to focused modules:\n"
        + "\n".join(violations)
    )


def test_service_book_creation_rejects_non_regular_employee() -> None:
    db = _FakeDb()

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            createServiceBookIfEligible(
                db=db,
                employee_id="EMP-ARCH-001",
                employee_or_type={"employment_type": "CONTRACTUAL"},
            )
        )

    assert exc.value.status_code == 403
    assert "Service Book" in str(exc.value.detail)


def test_contexts_do_not_import_other_context_repository_internals() -> None:
    violations: list[str] = []

    for file_path in _iter_context_py_files():
        rel = file_path.relative_to(BACKEND_ROOT).as_posix()
        owner_context = file_path.relative_to(CONTEXTS_ROOT).parts[0]

        for module in _imports_from_ast(file_path):
            match = CROSS_CONTEXT_REPO_IMPORT.match(module)
            if not match:
                continue
            target_context = match.group(1)
            if target_context != owner_context:
                violations.append(
                    f"{rel}: imports {module} (cross-context repository internals)"
                )

    assert not violations, "Cross-context repository imports are forbidden:\n" + "\n".join(sorted(violations))


def test_workflow_rejects_service_history_truth_payloads() -> None:
    with pytest.raises(HTTPException):
        workflow_service._assert_workflow_payload_boundary(
            {"service_book_truth": "x", "workflow_status": "SUBMITTED"}
        )

    with pytest.raises(HTTPException):
        workflow_service._assert_workflow_payload_boundary(
            {"employee_snapshot": "x", "workflow_state": "PENDING"}
        )

    workflow_service._assert_workflow_payload_boundary(
        {"workflow_status": "SUBMITTED", "remarks": "route to verifier"}
    )


def test_pay_context_emits_events_via_outbox() -> None:
    """Pay application service must emit PayRevised/AllowanceChanged events via outbox."""
    pay_service_path = (
        CONTEXTS_ROOT / "pay_benefits" / "application" / "service.py"
    )
    source = pay_service_path.read_text(encoding="utf-8")
    assert "EventName.PAY_REVISED" in source, (
        "PayApplicationService must emit PAY_REVISED events"
    )
    assert "EventName.ALLOWANCE_CHANGED" in source, (
        "PayApplicationService must emit ALLOWANCE_CHANGED events"
    )
    assert "OutboxRepository" in source, (
        "PayApplicationService must use outbox for event emission"
    )


def test_seniority_lists_registered_in_collection_ownership() -> None:
    """seniority_lists must be registered in the COLLECTION_OWNERSHIP map."""
    from app_platform.domain_separation.data_ownership import COLLECTION_OWNERSHIP
    import re

    matched = any(
        re.match(pattern, "seniority_lists")
        for pattern in COLLECTION_OWNERSHIP
    )
    assert matched, "seniority_lists is not registered in COLLECTION_OWNERSHIP"
    owner = next(
        owner
        for pattern, owner in COLLECTION_OWNERSHIP.items()
        if re.match(pattern, "seniority_lists")
    )
    assert owner == "seniority", (
        f"seniority_lists should be owned by 'seniority', got '{owner}'"
    )


def test_documents_context_cannot_store_service_history_truth() -> None:
    with pytest.raises(ValueError):
        validate_document_metadata(
            {
                "entity_type": "SERVICE_BOOK",
                "entity_id": "EMP-1",
                "service_history": "truth",
            }
        )

    frontend_guard = (
        WORKSPACE_ROOT
        / "frontend"
        / "src"
        / "contexts"
        / "documents"
        / "services"
        / "documentDomainService.js"
    )
    source = frontend_guard.read_text(encoding="utf-8")
    for token in ("service_history", "service_book_truth", "official_history"):
        assert token in source


def test_role_checks_do_not_bypass_access_control() -> None:
    violations: list[str] = []

    for file_path in _iter_context_py_files():
        rel = file_path.relative_to(BACKEND_ROOT).as_posix()
        if rel in AUTH_BYPASS_ALLOWED_FILES:
            continue

        source = file_path.read_text(encoding="utf-8-sig")
        imports = _imports_from_ast(file_path)

        if ".get(\"authorities\")" in source or ".get(\"authority\")" in source:
            violations.append(f"{rel}: direct authority extraction bypasses access_control")

        for module in imports:
            if module in DEPRECATED_AUTH_IMPORTS or any(
                module.startswith(f"{prefix}.") for prefix in DEPRECATED_AUTH_IMPORTS
            ):
                violations.append(f"{rel}: imports deprecated auth helper {module}")

    assert not violations, "Authorization bypass patterns detected:\n" + "\n".join(sorted(violations))


def test_generic_profile_permissions_are_confined_to_profile_owned_flows() -> None:
    violations: list[str] = []

    for file_path in BACKEND_ROOT.rglob("*.py"):
        if "__pycache__" in file_path.parts or "tests" in file_path.parts:
            continue

        rel = file_path.relative_to(BACKEND_ROOT).as_posix()
        source = file_path.read_text(encoding="utf-8-sig")
        hits = {token for token in GENERIC_PROFILE_PERMISSION_TOKENS if token in source}
        if not hits:
            continue

        allowed = ALLOWED_GENERIC_PROFILE_PERMISSION_USAGE.get(rel, set())
        disallowed = sorted(hits - allowed)
        if disallowed:
            violations.append(f"{rel}: unexpected generic profile permissions {', '.join(disallowed)}")

    assert not violations, (
        "Generic PROFILE_* permission usage should be limited to true profile-owned flows:\n"
        + "\n".join(sorted(violations))
    )


def test_employee_profile_runtime_reads_do_not_fallback_to_legacy_employee_profiles() -> None:
    profile_interface = (
        CONTEXTS_ROOT
        / "employee_master"
        / "profile"
        / "application"
        / "profile_interface.py"
    )
    source = profile_interface.read_text(encoding="utf-8-sig")

    assert "employee_profiles" not in source, (
        "employee_profile runtime read helpers must not depend on the legacy "
        "employee_profiles collection after hard cutover"
    )


def test_workflow_context_does_not_reintroduce_employee_profile_specific_application_modules() -> None:
    obsolete_files = [
        CONTEXTS_ROOT / "workflow" / "application" / "actions" / "employee_profile_actions.py",
        CONTEXTS_ROOT / "workflow" / "application" / "services" / "employee_profile_workflow_rules.py",
        CONTEXTS_ROOT / "workflow" / "application" / "services" / "employee_profile_workflow_service.py",
    ]

    lingering = [path.relative_to(BACKEND_ROOT).as_posix() for path in obsolete_files if path.exists()]

    assert not lingering, (
        "workflow should stay generic; employee_profile-specific application modules must remain deleted:\n"
        + "\n".join(sorted(lingering))
    )


def test_employee_profile_runtime_code_does_not_call_split_legacy_employee_record() -> None:
    runtime_files = [
        CONTEXTS_ROOT / "employee_master" / "profile" / "application" / "profile_interface.py",
        CONTEXTS_ROOT / "employee_master" / "profile" / "infrastructure" / "gateway.py",
    ]

    violations: list[str] = []
    for file_path in runtime_files:
        source = file_path.read_text(encoding="utf-8-sig")
        if "split_legacy_employee_record" in source:
            violations.append(file_path.relative_to(BACKEND_ROOT).as_posix())

    assert not violations, (
        "employee_profile runtime code must use split-only helpers instead of legacy split adapters:\n"
        + "\n".join(sorted(violations))
    )


def test_employee_profile_domain_does_not_define_split_legacy_employee_record() -> None:
    identity_layers = (
        CONTEXTS_ROOT
        / "employee_master"
        / "profile"
        / "domain"
        / "identity_layers.py"
    )
    source = identity_layers.read_text(encoding="utf-8-sig")

    assert "def split_legacy_employee_record" not in source, (
        "employee_profile domain identity layers must not retain the legacy split helper after cutover"
    )


def test_employee_identity_domain_does_not_define_split_legacy_employee_record() -> None:
    identity_layers = (
        CONTEXTS_ROOT
        / "employee_master"
        / "identity"
        / "domain"
        / "identity_layers.py"
    )
    source = identity_layers.read_text(encoding="utf-8-sig")

    assert "def split_legacy_employee_record" not in source, (
        "employee_identity domain identity layers must not retain the legacy split helper after cutover"
    )


def test_employee_profile_domain_services_compat_shim_remains_deleted() -> None:
    compat_shim = (
        CONTEXTS_ROOT
        / "employee_master"
        / "profile"
        / "services"
        / "domain_services.py"
    )

    assert not compat_shim.exists(), (
        "employee_profile services/domain_services.py was a transitional compat shim and must remain deleted"
    )


def test_employee_identity_domain_services_compat_shim_remains_deleted() -> None:
    compat_shim = (
        CONTEXTS_ROOT
        / "employee_master"
        / "identity"
        / "services"
        / "domain_services.py"
    )

    assert not compat_shim.exists(), (
        "employee_identity services/domain_services.py was a transitional compat shim and must remain deleted"
    )


def test_employee_profile_commands_do_not_reintroduce_ess_update_alias() -> None:
    commands_module = CONTEXTS_ROOT / "employee_master" / "profile" / "schemas" / "commands.py"
    source = commands_module.read_text(encoding="utf-8-sig")

    assert "class EmployeeProfileESSUpdate" not in source, (
        "employee_profile schemas.commands must not reintroduce the dead EmployeeProfileESSUpdate alias"
    )


def test_employee_profile_model_does_not_reintroduce_profile_alias() -> None:
    profile_model = CONTEXTS_ROOT / "employee_master" / "profile" / "schemas" / "profile_model.py"
    source = profile_model.read_text(encoding="utf-8-sig")

    assert "class EmployeeProfile(" not in source, (
        "employee_profile schemas.profile_model must not reintroduce the dead EmployeeProfile alias"
    )


def test_employee_profile_schema_enum_reexport_shim_remains_deleted() -> None:
    compat_shim = CONTEXTS_ROOT / "employee_master" / "profile" / "schemas" / "enums.py"

    assert not compat_shim.exists(), (
        "employee_profile schemas/enums.py was a compatibility re-export and must remain deleted"
    )


def test_employee_profile_schema_value_object_reexport_shim_remains_deleted() -> None:
    compat_shim = CONTEXTS_ROOT / "employee_master" / "profile" / "schemas" / "value_objects.py"

    assert not compat_shim.exists(), (
        "employee_profile schemas/value_objects.py was a compatibility re-export and must remain deleted"
    )


def test_final_compatibility_packages_stay_deleted() -> None:
    removed_paths = [
        CONTEXTS_ROOT / "documents" / "services",
        CONTEXTS_ROOT / "leave_attendance" / "schemas",
        CONTEXTS_ROOT / "pay_benefits" / "repository",
        CONTEXTS_ROOT / "service_book" / "read_side" / "api",
        CONTEXTS_ROOT / "service_book" / "records" / "application" / "commands.py",
    ]

    lingering: list[str] = []
    for path in removed_paths:
        if path.is_file():
            lingering.append(path.relative_to(BACKEND_ROOT).as_posix())
        elif path.is_dir():
            lingering.extend(
                py_file.relative_to(BACKEND_ROOT).as_posix()
                for py_file in path.rglob("*.py")
                if "__pycache__" not in py_file.parts
            )
    assert not lingering, (
        "Final cleanup compatibility packages must stay deleted:\n"
        + "\n".join(sorted(lingering))
    )


def test_app_platform_events_does_not_define_business_event_schemas() -> None:
    """Business event schemas (Employee*, ServiceEvent*) must live in their
    owning bounded context's contracts/events module, never in app_platform.

    The platform may only host domain-neutral primitives such as
    ``LenientEventPayload``.
    """
    events_dir = BACKEND_ROOT / "app_platform" / "contracts" / "events"
    forbidden_business_names = {
        "EmployeeCreatedEvent",
        "EmployeeIdentityCreatedEvent",
        "EmployeeUpdatedEvent",
        "EmployeeStatusChangedEvent",
        "EmployeePromotedEvent",
        "ServiceEventRecordedPayload",
        "ServiceEventCorrectedPayload",
        "ServiceEventVoidedPayload",
        "ServiceEventDocumentAttachedPayload",
        "ServiceEventLifecyclePayload",
        "DocumentUploadedPayload",
        "DocumentDeletedPayload",
        "DocumentLockedPayload",
        "DocumentMetadataUpdatedPayload",
    }

    violations: list[str] = []
    for py_file in events_dir.rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8-sig"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name in forbidden_business_names:
                rel = py_file.relative_to(BACKEND_ROOT).as_posix()
                violations.append(f"{rel}: defines business event {node.name}")

    assert not violations, (
        "Business event schemas must be DEFINED in their owning bounded "
        "context's contracts/events module, not in app_platform. Move them and "
        "have app_platform/contracts/events/__init__.py import them for "
        "registration:\n" + "\n".join(sorted(violations))
    )


def test_employee_event_schemas_live_in_employee_identity_context() -> None:
    """Canonical employee event schemas must be defined in
    ``contexts.employee_master.identity.contracts.events`` (Published Language)."""
    events_module = (
        CONTEXTS_ROOT / "employee_master" / "identity" / "contracts" / "events.py"
    )
    assert events_module.exists(), (
        "Employee event contracts module must exist at "
        "contexts/employee_master/identity/contracts/events.py"
    )

    tree = ast.parse(events_module.read_text(encoding="utf-8-sig"))
    defined = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    required = {
        "EmployeeCreatedEvent",
        "EmployeeIdentityCreatedEvent",
        "EmployeeUpdatedEvent",
        "EmployeeStatusChangedEvent",
        "EmployeePromotedEvent",
    }
    missing = sorted(required - defined)
    assert not missing, (
        "employee_identity.contracts.events must define the canonical "
        f"employee event schemas. Missing: {missing}"
    )


def test_app_platform_employee_events_module_stays_deleted() -> None:
    """The legacy module ``app_platform.contracts.events.employee_events`` was
    a business-event surface in a platform location. It has been moved to
    ``contexts.employee_master.identity.contracts.events`` and must not be recreated."""
    legacy = (
        BACKEND_ROOT / "app_platform" / "contracts" / "events" / "employee_events.py"
    )
    assert not legacy.exists(), (
        "Legacy module app_platform/contracts/events/employee_events.py must "
        "stay deleted. Define employee event schemas in "
        "contexts/employee_master/identity/contracts/events.py instead."
    )


def test_policy_engine_is_platform_primitive_only() -> None:
    """``app_platform.policy_engine`` must host ONLY the technical
    ``Decision`` value object. Any business-domain facts/rules (leave,
    change-request, etc.) must live in their owning bounded context."""
    pe_root = BACKEND_ROOT / "app_platform" / "policy_engine"
    permitted_files = {"__init__.py", "decision.py"}

    violations: list[str] = []
    for py_file in pe_root.rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue
        rel = py_file.relative_to(pe_root).as_posix()
        if rel not in permitted_files:
            violations.append(py_file.relative_to(BACKEND_ROOT).as_posix())

    assert not violations, (
        "app_platform/policy_engine/ must contain only Decision. Move "
        "business-domain policies into their owning context (e.g. "
        "contexts/leave_attendance/domain/leave_request_policy.py):\n"
        + "\n".join(sorted(violations))
    )


def test_leave_request_policy_lives_in_leave_context() -> None:
    """The CCS leave-rule set (LeaveFacts + LEAVE_RULES) must live in the
    leave bounded context."""
    policy_module = (
        CONTEXTS_ROOT / "leave_attendance" / "domain" / "leave_request_policy.py"
    )
    source = policy_module.read_text(encoding="utf-8-sig")
    assert "class LeaveFacts" in source, (
        "LeaveFacts must be defined in contexts/leave_attendance/domain/leave_request_policy.py"
    )
    assert "LEAVE_RULES" in source, (
        "LEAVE_RULES must be defined in contexts/leave_attendance/domain/leave_request_policy.py"
    )


def test_change_request_policy_lives_in_change_requests_context() -> None:
    """ChangeRequestFacts must live in the change_requests bounded context."""
    policy_module = (
        CONTEXTS_ROOT
        / "change_requests"
        / "domain"
        / "change_request_policy.py"
    )
    source = policy_module.read_text(encoding="utf-8-sig")
    assert "class ChangeRequestFacts" in source, (
        "ChangeRequestFacts must be defined in "
        "contexts/change_requests/domain/change_request_policy.py"
    )


def test_employee_profile_profile_normalization_mirror_stays_deleted() -> None:
    """``employee_profile.domain.profile_normalization`` was a transitional
    mirror of ``employee_identity.domain.identity_normalization``. Identity
    normalization is owned by employee_identity and the mirror must not
    return — other code must call the identity context directly via its
    contract surface."""
    mirror = (
        CONTEXTS_ROOT
        / "employee_master"
        / "profile"
        / "domain"
        / "profile_normalization.py"
    )
    assert not mirror.exists(), (
        "employee_profile/domain/profile_normalization.py must stay deleted. "
        "Use contexts.employee_master.identity.contracts.employee_domain instead."
    )

    legacy_contract = (
        CONTEXTS_ROOT / "employee_master" / "profile" / "contracts" / "employee_domain.py"
    )
    assert not legacy_contract.exists(), (
        "employee_profile/contracts/employee_domain.py was a re-export shim "
        "over the deleted profile_normalization mirror and must stay deleted."
    )
