# Domain Separation Enforcement
# ==============================
#
# Middleware and validators to enforce strict domain boundaries at the API layer.

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import HTTPException, Request

from .schema_definitions import (
    FORBIDDEN_IN_PROFILE,
    FORBIDDEN_IN_SERVICE_BOOK,
    PROFILE_EMPLOYMENT_TYPE_RULES,
)
from .validators import (
    DomainSeparationError,
    reject_mixed_payload,
    validate_profile_payload,
    validate_service_book_payload,
)


class ProfilePayloadValidator:
    """
    Validator class for Profile API payloads.

    ENFORCES:
    - No Service Book fields in Profile payloads
    - Employment type-specific field rules
    - Immutability rules for locked records
    """

    @staticmethod
    def validate_create(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate payload for profile creation"""
        employment_type = payload.get("employment_type")

        # First, reject any mixed payload
        reject_mixed_payload(payload)

        # Then validate profile-specific rules
        result = validate_profile_payload(
            payload=payload,
            employment_type=employment_type,
            is_create=True,
        )

        return result

    @staticmethod
    def validate_update(payload: Dict[str, Any], current_status: str) -> Dict[str, Any]:
        """
        Validate payload for profile update.

        RULES:
        - LOCKED profiles cannot be updated
        - Finalized profiles require supersession
        - Service Book fields are always rejected
        """
        # LOCKED records cannot be modified
        if current_status == "LOCKED":
            raise DomainSeparationError(
                error_code="RECORD_LOCKED",
                message="This profile is LOCKED and cannot be modified. Create a correction request if changes are needed.",
                domain="PROFILE",
                details={"current_status": current_status},
            )

        # Validate no Service Book fields
        result = validate_profile_payload(
            payload=payload,
            employment_type=payload.get("employment_type"),
            is_create=False,
        )

        return result

    @staticmethod
    def get_forbidden_fields() -> List[str]:
        """Get list of fields forbidden in Profile payloads"""
        return list(FORBIDDEN_IN_PROFILE)


class ServiceBookPayloadValidator:
    """
    Validator class for Service Book API payloads.

    ENFORCES:
    - No Profile fields in Service Book payloads
    - Event type-specific required fields
    - Immutability of finalized entries
    - Append-only nature (no UPDATE/DELETE)
    """

    @staticmethod
    def validate_create(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate payload for entry creation"""
        event_type = payload.get("event_type")

        # First, reject any mixed payload
        reject_mixed_payload(payload)

        # Then validate service book-specific rules
        result = validate_service_book_payload(
            payload=payload,
            event_type=event_type,
        )

        return result

    @staticmethod
    def validate_update_blocked(entry_status: str) -> None:
        """
        BLOCK all updates to Service Book entries.

        Service Book is APPEND-ONLY. Updates are forbidden.
        Corrections must be made via SUPERSESSION entries.
        """
        raise DomainSeparationError(
            error_code="UPDATE_FORBIDDEN",
            message=(
                "UPDATE operations are NOT ALLOWED on Service Book entries. "
                "The Service Book is an APPEND-ONLY legal ledger. "
                "To correct an error, create a new SUPERSESSION entry."
            ),
            domain="SERVICE_BOOK",
            details={
                "entry_status": entry_status,
                "legal_requirement": (
                    "Government Service Books are legal documents. "
                    "Modifications to historical entries would constitute tampering. "
                    "All corrections must be made by adding new entries that reference the original."
                ),
            },
        )

    @staticmethod
    def validate_delete_blocked(entry_status: str) -> None:
        """
        BLOCK all deletes on Service Book entries.

        Service Book entries can NEVER be deleted.
        """
        raise DomainSeparationError(
            error_code="DELETE_FORBIDDEN",
            message=(
                "DELETE operations are NOT ALLOWED on Service Book entries. "
                "Service Book entries are PERMANENT legal records. "
                "They cannot be deleted under any circumstances."
            ),
            domain="SERVICE_BOOK",
            details={
                "entry_status": entry_status,
                "legal_requirement": (
                    "Deleting Service Book entries would destroy the audit trail "
                    "and constitute destruction of government records. "
                    "Mark entries as corrected via SUPERSESSION instead."
                ),
            },
        )

    @staticmethod
    def validate_approved_immutability(entry_status: str) -> None:
        """
        Ensure APPROVED/finalized entries cannot be modified.
        """
        immutable_statuses = ["APPROVED", "ATTESTED", "LOCKED"]

        if entry_status in immutable_statuses:
            raise DomainSeparationError(
                error_code="ENTRY_IMMUTABLE",
                message=(
                    f"Entry with status '{entry_status}' is IMMUTABLE. "
                    "Once approved, Service Book entries become part of the legal record "
                    "and cannot be modified. Use SUPERSESSION to correct errors."
                ),
                domain="SERVICE_BOOK",
                details={
                    "entry_status": entry_status,
                    "immutable_statuses": immutable_statuses,
                },
            )

    @staticmethod
    def get_forbidden_fields() -> List[str]:
        """Get list of fields forbidden in Service Book payloads"""
        return list(FORBIDDEN_IN_SERVICE_BOOK)


# ==================== HELPER FUNCTIONS ====================


def enforce_profile_separation(payload: Dict[str, Any]) -> None:
    """
    Convenience function to enforce Profile domain separation.
    Raises HTTPException if violation detected.
    """
    try:
        ProfilePayloadValidator.validate_create(payload)
    except DomainSeparationError as e:
        raise e.to_http_exception()


def enforce_service_book_separation(payload: Dict[str, Any]) -> None:
    """
    Convenience function to enforce Service Book domain separation.
    Raises HTTPException if violation detected.
    """
    try:
        ServiceBookPayloadValidator.validate_create(payload)
    except DomainSeparationError as e:
        raise e.to_http_exception()


def block_service_book_update() -> None:
    """
    Block UPDATE operations on Service Book.
    Always raises HTTPException.
    """
    try:
        ServiceBookPayloadValidator.validate_update_blocked("ANY")
    except DomainSeparationError as e:
        raise e.to_http_exception(status_code=405)


def block_service_book_delete() -> None:
    """
    Block DELETE operations on Service Book.
    Always raises HTTPException.
    """
    try:
        ServiceBookPayloadValidator.validate_delete_blocked("ANY")
    except DomainSeparationError as e:
        raise e.to_http_exception(status_code=405)


def check_approved_immutability(entry_status: str) -> None:
    """
    Check if an entry is immutable due to approval status.
    Raises HTTPException if immutable.
    """
    try:
        ServiceBookPayloadValidator.validate_approved_immutability(entry_status)
    except DomainSeparationError as e:
        raise e.to_http_exception(status_code=403)
