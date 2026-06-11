# Field-Level Immutability Validator
# ==================================
#
# Certain employee data fields become immutable after verification.
# This module enforces immutability rules at the service layer.
#
# IMMUTABLE FIELDS (after VERIFIED stage):
# - date_of_birth
# - full_name (and name components)
# - father_husband_name (parent_name)
# - category (caste)
# - initial_appointment_date
#
# RULES:
# 1. Immutable fields are editable ONLY in DRAFT/REJECTED stage
# 2. After VERIFIED/APPROVED, these fields cannot be modified
# 3. LOCKED (ATTESTED) records reject ALL write operations
# 4. All failed modification attempts are logged for audit

from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone
import hashlib


class ImmutabilityStage(str, Enum):
    """Workflow stages that affect immutability"""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    VERIFIED = "VERIFIED"
    APPROVED = "APPROVED"
    ATTESTED = "ATTESTED"  # Final - service book entries
    LOCKED = "LOCKED"      # Final - profiles
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"  # Replaced by correction entry


# ==================== IMMUTABLE FIELD DEFINITIONS ====================

# Fields that become immutable after VERIFIED stage
IMMUTABLE_AFTER_VERIFICATION: Set[str] = {
    # Identity fields - cannot change after verification
    "date_of_birth",
    "full_name",
    "father_husband_name",  # parent_name
    "mother_name",
    "category",  # caste/reservation category
    "gender",
    "nationality",
    
    # Initial appointment - historical fact, cannot change
    "initial_appointment_date",
    "appointment_order_no",
    "appointment_order_date",
    "recruitment_mode",
}

# Fields that become immutable after SUBMITTED stage (more restrictive)
IMMUTABLE_AFTER_SUBMISSION: Set[str] = {
    "employment_type",  # Employment type cannot change after submission
}

# Stages where fields can still be edited
EDITABLE_STAGES: Set[str] = {
    ImmutabilityStage.DRAFT.value,
    ImmutabilityStage.REJECTED.value,
}

# Stages where immutable fields are locked
LOCKED_STAGES: Set[str] = {
    ImmutabilityStage.VERIFIED.value,
    ImmutabilityStage.APPROVED.value,
    ImmutabilityStage.ATTESTED.value,
}

# Stage where ALL fields are locked (full immutability)
FULLY_LOCKED_STAGE: str = ImmutabilityStage.ATTESTED.value


# ==================== VALIDATION RESULT ====================

@dataclass
class ImmutabilityValidationResult:
    """Result of immutability validation"""
    valid: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    blocked_fields: List[str] = None
    current_stage: Optional[str] = None
    
    def __post_init__(self):
        if self.blocked_fields is None:
            self.blocked_fields = []


@dataclass 
class ImmutabilityViolation:
    """Details of a single immutability violation"""
    field_id: str
    field_label: str
    old_value: Any
    attempted_new_value: Any
    locked_since_stage: str
    violation_type: str  # 'FIELD_IMMUTABLE' or 'RECORD_LOCKED'
    

# ==================== IMMUTABILITY VALIDATOR ====================

class ImmutabilityValidator:
    """
    Validates field-level immutability rules.
    
    Usage:
    ------
    validator = ImmutabilityValidator(current_stage, old_data, updates)
    result = validator.validate()
    
    if not result.valid:
        # Log the violation and reject the update
        raise HTTPException(403, detail=result.to_dict())
    """
    
    # Field labels for human-readable error messages
    FIELD_LABELS = {
        "date_of_birth": "Date of Birth",
        "full_name": "Full Name",
        "father_husband_name": "Father's/Husband's Name",
        "mother_name": "Mother's Name",
        "category": "Category (Caste)",
        "gender": "Gender",
        "nationality": "Nationality",
        "initial_appointment_date": "Initial Appointment Date",
        "appointment_order_no": "Appointment Order Number",
        "appointment_order_date": "Appointment Order Date",
        "recruitment_mode": "Recruitment Mode",
        "employment_type": "Employment Type",
    }
    
    def __init__(
        self,
        current_stage: str,
        old_data: Dict[str, Any],
        updates: Dict[str, Any],
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
    ):
        self.current_stage = current_stage
        self.old_data = old_data
        self.updates = updates
        self.user_id = user_id
        self.user_name = user_name
        self.violations: List[ImmutabilityViolation] = []
    
    def validate(self) -> ImmutabilityValidationResult:
        """
        Validate all updates against immutability rules.
        
        Returns ImmutabilityValidationResult with:
        - valid: True if all updates are allowed
        - blocked_fields: List of fields that cannot be modified
        - error_code: Type of violation
        - error_message: Human-readable explanation
        """
        # Rule 1: LOCKED (ATTESTED) records reject ALL writes
        if self.current_stage == FULLY_LOCKED_STAGE:
            return ImmutabilityValidationResult(
                valid=False,
                error_code="RECORD_LOCKED",
                error_message=(
                    "This record is ATTESTED and fully locked. "
                    "No modifications are allowed. "
                    "To correct errors, use the supersession process."
                ),
                blocked_fields=list(self.updates.keys()),
                current_stage=self.current_stage,
            )
        
        # Rule 2: Check if in editable stage (DRAFT/REJECTED)
        if self.current_stage in EDITABLE_STAGES:
            # All fields are editable in DRAFT/REJECTED
            return ImmutabilityValidationResult(
                valid=True,
                current_stage=self.current_stage,
            )
        
        # Rule 3: Check immutable fields in SUBMITTED stage
        if self.current_stage == ImmutabilityStage.SUBMITTED.value:
            self._check_immutable_fields(
                IMMUTABLE_AFTER_SUBMISSION,
                "SUBMITTED"
            )
        
        # Rule 4: Check immutable fields in VERIFIED/APPROVED stages
        if self.current_stage in LOCKED_STAGES:
            self._check_immutable_fields(
                IMMUTABLE_AFTER_VERIFICATION,
                self.current_stage
            )
            # Also check submission-locked fields
            self._check_immutable_fields(
                IMMUTABLE_AFTER_SUBMISSION,
                "SUBMITTED"
            )
        
        # Return result
        if self.violations:
            blocked_fields = [v.field_id for v in self.violations]
            blocked_labels = [v.field_label for v in self.violations]
            
            return ImmutabilityValidationResult(
                valid=False,
                error_code="FIELD_IMMUTABLE",
                error_message=(
                    f"The following fields cannot be modified after {self.current_stage} stage: "
                    f"{', '.join(blocked_labels)}. "
                    f"To correct these fields, the record must be rejected back to DRAFT."
                ),
                blocked_fields=blocked_fields,
                current_stage=self.current_stage,
            )
        
        return ImmutabilityValidationResult(
            valid=True,
            current_stage=self.current_stage,
        )
    
    def _check_immutable_fields(self, immutable_set: Set[str], locked_since: str):
        """Check if any updates attempt to modify immutable fields"""
        for field_id in self.updates:
            if field_id in immutable_set:
                old_value = self.old_data.get(field_id)
                new_value = self.updates[field_id]
                
                # Skip if values are the same (no actual change)
                if self._values_equal(old_value, new_value):
                    continue
                
                # Skip if old value is None/empty and we're setting initial value
                # This allows setting values that were never set before
                if old_value in [None, "", []]:
                    continue
                
                # Record violation
                self.violations.append(ImmutabilityViolation(
                    field_id=field_id,
                    field_label=self.FIELD_LABELS.get(field_id, field_id),
                    old_value=old_value,
                    attempted_new_value=new_value,
                    locked_since_stage=locked_since,
                    violation_type="FIELD_IMMUTABLE",
                ))
    
    def _values_equal(self, old_value: Any, new_value: Any) -> bool:
        """Compare values, handling type differences"""
        if old_value == new_value:
            return True
        
        # Handle string/None comparisons
        if old_value is None and new_value == "":
            return True
        if old_value == "" and new_value is None:
            return True
        
        # Handle date string comparisons
        if isinstance(old_value, str) and isinstance(new_value, str):
            # Normalize date formats
            try:
                from dateutil.parser import parse
                old_date = parse(old_value).date()
                new_date = parse(new_value).date()
                return old_date == new_date
            except (ValueError, TypeError):
                pass
        
        return False
    
    def get_violations(self) -> List[Dict]:
        """Get list of violations as dictionaries for API response"""
        return [
            {
                "field_id": v.field_id,
                "field_label": v.field_label,
                "old_value": v.old_value,
                "attempted_new_value": v.attempted_new_value,
                "locked_since_stage": v.locked_since_stage,
                "violation_type": v.violation_type,
            }
            for v in self.violations
        ]


# ==================== AUDIT LOG FOR VIOLATIONS ====================

@dataclass
class ImmutabilityAuditLog:
    """Audit log entry for immutability violation attempts"""
    id: str
    timestamp: str
    user_id: str
    user_name: str
    entity_type: str  # e.g., "EmployeeProfile"
    entity_id: str
    action: str  # "IMMUTABILITY_VIOLATION"
    current_stage: str
    attempted_updates: Dict[str, Any]
    blocked_fields: List[str]
    violations: List[Dict]
    error_code: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    integrity_hash: Optional[str] = None
    
    def __post_init__(self):
        import uuid
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        
        # Generate integrity hash
        hash_data = f"{self.id}:{self.timestamp}:{self.user_id}:{self.entity_id}:{self.action}"
        self.integrity_hash = hashlib.sha256(hash_data.encode()).hexdigest()


async def log_immutability_violation(
    db,
    user_id: str,
    user_name: str,
    entity_type: str,
    entity_id: str,
    current_stage: str,
    attempted_updates: Dict,
    validation_result: ImmutabilityValidationResult,
    violations: List[Dict],
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> str:
    """
    Create an immutable audit log entry for a failed modification attempt.
    
    Returns the audit log ID.
    """
    try:
        log_entry = ImmutabilityAuditLog(
            id="",  # Will be auto-generated
            timestamp="",  # Will be auto-generated
            user_id=user_id,
            user_name=user_name,
            entity_type=entity_type,
            entity_id=entity_id,
            action="IMMUTABILITY_VIOLATION",
            current_stage=current_stage,
            attempted_updates=attempted_updates,
            blocked_fields=validation_result.blocked_fields or [],
            violations=violations,
            error_code=validation_result.error_code,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        await db.immutability_audit_logs.insert_one(log_entry.__dict__)
        return log_entry.id
    except Exception as e:
        # Log to stderr but don't fail the main operation
        import sys
        print(f"Failed to log immutability violation: {e}", file=sys.stderr)
        return ""


# ==================== CONVENIENCE FUNCTIONS ====================

def validate_immutability(
    current_stage: str,
    old_data: Dict,
    updates: Dict,
) -> ImmutabilityValidationResult:
    """
    Convenience function to validate immutability rules.
    
    Usage:
    ------
    result = validate_immutability("VERIFIED", old_profile, updates)
    if not result.valid:
        raise HTTPException(403, detail={
            "error_code": result.error_code,
            "message": result.error_message,
            "blocked_fields": result.blocked_fields
        })
    """
    validator = ImmutabilityValidator(current_stage, old_data, updates)
    return validator.validate()


def get_immutable_fields_for_stage(stage: str) -> Set[str]:
    """
    Get the set of immutable fields for a given workflow stage.
    
    Returns empty set if stage allows all edits (DRAFT/REJECTED).
    """
    if stage in EDITABLE_STAGES:
        return set()
    
    if stage == FULLY_LOCKED_STAGE:
        return {"*"}  # All fields locked
    
    immutable = set()
    
    if stage == ImmutabilityStage.SUBMITTED.value:
        immutable.update(IMMUTABLE_AFTER_SUBMISSION)
    
    if stage in LOCKED_STAGES:
        immutable.update(IMMUTABLE_AFTER_VERIFICATION)
        immutable.update(IMMUTABLE_AFTER_SUBMISSION)
    
    return immutable


def is_field_immutable(field_id: str, stage: str) -> Tuple[bool, Optional[str]]:
    """
    Check if a specific field is immutable at a given stage.
    
    Returns:
        (is_immutable, reason)
    """
    if stage in EDITABLE_STAGES:
        return False, None
    
    if stage == FULLY_LOCKED_STAGE:
        return True, "Record is ATTESTED (fully locked)"
    
    if field_id in IMMUTABLE_AFTER_SUBMISSION and stage != ImmutabilityStage.DRAFT.value:
        return True, f"Field locked after SUBMITTED stage"
    
    if field_id in IMMUTABLE_AFTER_VERIFICATION and stage in LOCKED_STAGES:
        return True, f"Field locked after VERIFIED stage"
    
    return False, None
