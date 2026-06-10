# Domain Separation Validators
# =============================
#
# STRICT ENFORCEMENT of Profile/Service Book domain boundaries.
# These validators REJECT any payload that violates separation rules.

from typing import Dict, Any, List, Optional, Set
from fastapi import HTTPException
from datetime import datetime, timezone
import hashlib
import uuid

from .schema_definitions import (
    PROFILE_FIELDS,
    SERVICE_BOOK_FIELDS,
    FORBIDDEN_IN_PROFILE,
    FORBIDDEN_IN_SERVICE_BOOK,
    PROFILE_EMPLOYMENT_TYPE_RULES,
    SERVICE_BOOK_EVENT_TYPE_RULES,
)


class DomainSeparationError(Exception):
    """Raised when domain separation rules are violated"""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        violating_fields: List[str] = None,
        domain: str = None,
        details: Dict[str, Any] = None,
    ):
        self.error_code = error_code
        self.message = message
        self.violating_fields = violating_fields or []
        self.domain = domain
        self.details = details or {}
        super().__init__(self.message)
    
    def to_http_exception(self, status_code: int = 400) -> HTTPException:
        """Convert to FastAPI HTTPException"""
        return HTTPException(
            status_code=status_code,
            detail={
                "error_code": self.error_code,
                "message": self.message,
                "domain": self.domain,
                "violating_fields": self.violating_fields,
                "details": self.details,
                "legal_note": (
                    "Domain separation is enforced to maintain data integrity. "
                    "Profile data and Service Book entries MUST be kept in separate collections."
                ),
            }
        )


def validate_profile_payload(
    payload: Dict[str, Any],
    employment_type: Optional[str] = None,
    is_create: bool = True,
) -> Dict[str, Any]:
    """
    Validate that a Profile API payload contains ONLY profile fields.
    
    RULES:
    1. REJECT any field that belongs to Service Book domain
    2. REJECT any forbidden field for the employment type
    3. WARN if required fields for employment type are missing (on create)
    
    Returns:
        Cleaned payload with only allowed fields
        
    Raises:
        DomainSeparationError if validation fails
    """
    violations = []
    warnings = []
    
    # Check for Service Book fields in Profile payload
    for field in payload.keys():
        if field in FORBIDDEN_IN_PROFILE:
            violations.append({
                "field": field,
                "reason": "SERVICE_BOOK_FIELD",
                "message": f"Field '{field}' belongs to Service Book domain and CANNOT appear in Profile payload",
            })
    
    if violations:
        raise DomainSeparationError(
            error_code="DOMAIN_VIOLATION_PROFILE",
            message=(
                "Profile payload contains Service Book fields. "
                "These fields belong to immutable Service Book records and must be submitted separately."
            ),
            violating_fields=[v["field"] for v in violations],
            domain="PROFILE",
            details={
                "violations": violations,
                "rule": "Profile API accepts ONLY identity and contact data. Service chronology data (pay, leave, promotions) must use /api/service-book/records endpoints.",
            },
        )
    
    # Validate employment type rules if provided
    if employment_type and employment_type in PROFILE_EMPLOYMENT_TYPE_RULES:
        rules = PROFILE_EMPLOYMENT_TYPE_RULES[employment_type]
        
        # Check forbidden fields for this employment type
        for field in payload.keys():
            if field in rules.get("forbidden", []):
                violations.append({
                    "field": field,
                    "reason": "FORBIDDEN_FOR_TYPE",
                    "message": f"Field '{field}' is not allowed for {employment_type} employees",
                })
        
        if violations:
            raise DomainSeparationError(
                error_code="EMPLOYMENT_TYPE_VIOLATION",
                message=f"Payload contains fields forbidden for {employment_type} employment type",
                violating_fields=[v["field"] for v in violations],
                domain="PROFILE",
                details={
                    "employment_type": employment_type,
                    "violations": violations,
                    "allowed_fields": rules.get("required", []) + rules.get("optional", []),
                },
            )
        
        # Check required fields on create
        if is_create:
            missing_required = []
            for field in rules.get("required", []):
                if field not in payload or payload.get(field) is None:
                    missing_required.append(field)
            
            if missing_required:
                warnings.append({
                    "type": "MISSING_REQUIRED",
                    "fields": missing_required,
                    "message": f"Required fields for {employment_type}: {', '.join(missing_required)}",
                })
    
    # Return validation result
    return {
        "valid": True,
        "payload": payload,
        "warnings": warnings,
        "employment_type": employment_type,
    }


def validate_service_book_payload(
    payload: Dict[str, Any],
    event_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validate that a Service Book API payload contains ONLY service book fields.
    
    RULES:
    1. REJECT any field that belongs to Profile domain
    2. VALIDATE required fields for event type
    
    Returns:
        Cleaned payload with only allowed fields
        
    Raises:
        DomainSeparationError if validation fails
    """
    violations = []
    
    # Check for Profile fields in Service Book payload
    for field in payload.keys():
        if field in FORBIDDEN_IN_SERVICE_BOOK:
            violations.append({
                "field": field,
                "reason": "PROFILE_FIELD",
                "message": f"Field '{field}' belongs to Profile domain and CANNOT appear in Service Book payload",
            })
    
    if violations:
        raise DomainSeparationError(
            error_code="DOMAIN_VIOLATION_SERVICE_BOOK",
            message=(
                "Service Book payload contains Profile fields. "
                "Identity and contact data is stored separately in the Profile collection."
            ),
            violating_fields=[v["field"] for v in violations],
            domain="SERVICE_BOOK",
            details={
                "violations": violations,
                "rule": (
                    "Service Book API accepts ONLY event data. "
                    "Employee identity data must use /api/employee-identities/ and "
                    "employee profile data must use /api/employee-profiles/."
                ),
            },
        )
    
    # Validate event type rules if provided
    if event_type and event_type in SERVICE_BOOK_EVENT_TYPE_RULES:
        rules = SERVICE_BOOK_EVENT_TYPE_RULES[event_type]
        
        # Check required fields
        missing_required = []
        for field in rules.get("required", []):
            if field not in payload or payload.get(field) is None:
                missing_required.append(field)
        
        if missing_required:
            raise DomainSeparationError(
                error_code="MISSING_REQUIRED_FIELDS",
                message=f"Missing required fields for {event_type} event",
                violating_fields=missing_required,
                domain="SERVICE_BOOK",
                details={
                    "event_type": event_type,
                    "required_fields": rules.get("required", []),
                    "missing_fields": missing_required,
                },
            )
    
    return {
        "valid": True,
        "payload": payload,
        "event_type": event_type,
    }


def reject_mixed_payload(payload: Dict[str, Any]) -> None:
    """
    REJECT any payload that contains BOTH Profile and Service Book fields.
    This is a strict enforcement to prevent cross-contamination.
    
    Raises:
        DomainSeparationError if payload contains mixed fields
    """
    profile_fields_found = []
    service_book_fields_found = []
    
    for field in payload.keys():
        if field in PROFILE_FIELDS and field not in {"employee_id"}:  # employee_id is shared
            profile_fields_found.append(field)
        if field in SERVICE_BOOK_FIELDS and field not in {"employee_id", "payload", "remarks"}:
            service_book_fields_found.append(field)
    
    if profile_fields_found and service_book_fields_found:
        raise DomainSeparationError(
            error_code="MIXED_PAYLOAD_REJECTED",
            message=(
                "Payload contains BOTH Profile and Service Book fields. "
                "These domains MUST be kept separate. "
                "Submit employee identity data to /api/employee-identities/, "
                "employee profile data to /api/employee-profiles/{employee_id}, "
                "and service chronology data to /api/service-book/records."
            ),
            violating_fields=profile_fields_found + service_book_fields_found,
            domain="MIXED",
            details={
                "profile_fields": profile_fields_found,
                "service_book_fields": service_book_fields_found,
                "rule": (
                    "Domain separation is a LEGAL REQUIREMENT. "
                    "Employee identity data (Profile) and employment history (Service Book) "
                    "must be maintained in separate, auditable collections."
                ),
            },
        )


async def log_domain_violation(
    db,
    violation_type: str,
    user_id: str,
    user_role: str,
    endpoint: str,
    payload: Dict[str, Any],
    violating_fields: List[str],
    ip_address: str = None,
) -> str:
    """
    Log domain separation violations for audit purposes.
    
    Returns:
        Log entry ID
    """
    log_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "violation_type": violation_type,
        "user_id": user_id,
        "user_role": user_role,
        "endpoint": endpoint,
        "payload_snapshot": {k: "***" if "password" in k.lower() else v for k, v in payload.items()},
        "violating_fields": violating_fields,
        "ip_address": ip_address,
        "integrity_hash": hashlib.sha256(
            f"{user_id}:{endpoint}:{violation_type}:{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest(),
    }
    
    try:
        if db is not None:
            await db.domain_violation_logs.insert_one(log_entry)
    except Exception:
        pass  # Best-effort logging — don't fail the request
    return log_entry["id"]
