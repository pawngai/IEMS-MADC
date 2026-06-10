# Domain Separation Module
# ========================
#
# STRICT MAPPING RULES:
# ---------------------
# UI Layer:
#   - Profile screens → write ONLY to employee_profile APIs
#   - Service events screens → write ONLY to service_book APIs
#
# API Layer:
#   - REJECT payloads containing mixed Profile + Service Book fields
#   - VALIDATE employment-type rules
#
# DB Layer:
#   - SEPARATE collections: employee_profiles, service_book_part_{i..viii}, workflow_audit_logs
#   - NO cross-contamination
#
# AUTOMATED TESTS:
#   - FAIL builds if Service Book fields appear in Profile schema
#   - FAIL builds if UPDATE/DELETE is attempted on approved ledger entries

from .schema_definitions import (
    PROFILE_FIELDS,
    SERVICE_BOOK_FIELDS,
    FORBIDDEN_IN_PROFILE,
    FORBIDDEN_IN_SERVICE_BOOK,
    PROFILE_EMPLOYMENT_TYPE_RULES,
)
from .validators import (
    validate_profile_payload,
    validate_service_book_payload,
    reject_mixed_payload,
    DomainSeparationError,
)
from .enforcement import (
    ProfilePayloadValidator,
    ServiceBookPayloadValidator,
)
from .context_responsibilities import (
    CONTEXT_RESPONSIBILITIES,
    get_context_responsibility,
)

__all__ = [
    "PROFILE_FIELDS",
    "SERVICE_BOOK_FIELDS",
    "FORBIDDEN_IN_PROFILE",
    "FORBIDDEN_IN_SERVICE_BOOK",
    "PROFILE_EMPLOYMENT_TYPE_RULES",
    "validate_profile_payload",
    "validate_service_book_payload",
    "reject_mixed_payload",
    "DomainSeparationError",
    "ProfilePayloadValidator",
    "ServiceBookPayloadValidator",
    "CONTEXT_RESPONSIBILITIES",
    "get_context_responsibility",
]
