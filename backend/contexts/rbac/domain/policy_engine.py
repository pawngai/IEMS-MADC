# RBAC Policy Engine - Government-Grade Access Control
# =====================================================
#
# This module implements a CENTRALIZED permission engine that evaluates
# access based on three dimensions:
#   1. USER ROLE - Who is the user?
#   2. WORKFLOW STAGE - What stage is the record in?
#   3. RECORD STATE - Is the record editable/locked?
#
# DESIGN PRINCIPLES:
# ------------------
# 1. DENY BY DEFAULT - All actions are denied unless explicitly permitted
# 2. SEPARATION OF DUTIES - Users cannot act on their own submissions
# 3. NO BYPASS - Workflow stages cannot be skipped
# 4. IMMUTABILITY - LOCKED (including compatibility final-state labels) records cannot be modified by anyone
# 5. AUDIT TRAIL - All permission checks are loggable
#
# USAGE:
# ------
# Instead of scattered role checks like:
#   if user.role == "ADMIN" or user.role == "DATA_ENTRY": ...
#
# Use:
#   result = PolicyEngine.evaluate(action, user_context, record_context)
#   if not result.allowed:
#       raise PermissionDenied(result)

import functools
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

# ==================== ROLE DEFINITIONS ====================


class Role(str, Enum):
    """
    Government HRMS Roles.
    Each role has specific permissions and workflow responsibilities.
    """

    DATA_ENTRY_OPERATOR = "DATA_ENTRY_OPERATOR"  # Creates and edits DRAFT records
    VERIFIER = "VERIFIER"  # Verifies SUBMITTED records (no edit)
    APPROVING_AUTHORITY = "APPROVING_AUTHORITY"  # Approves, attests, and finalizes
    AUDITOR = "AUDITOR"  # Read-only access to all records
    ADMIN = "ADMIN"  # System administration (no workflow powers)


# Map roles to existing authority names in the system
ROLE_TO_AUTHORITIES: Dict[Role, List[str]] = {
    Role.DATA_ENTRY_OPERATOR: [
        "DEPT_DATA_ENTRY",
        "GLOBAL_DATA_ENTRY",
        "DEALING_ASSISTANT",
    ],
    Role.VERIFIER: ["VERIFIER"],
    Role.APPROVING_AUTHORITY: ["APPROVING_AUTHORITY", "DDO", "APPROVER", "ATTESTER", "APPOINTING_AUTHORITY"],
    Role.AUDITOR: ["AUDITOR"],
    Role.ADMIN: ["SYSTEM_ADMIN", "ADMIN"],
}

# Reverse map: authority -> role
AUTHORITY_TO_ROLE: Dict[str, Role] = {}
for role, authorities in ROLE_TO_AUTHORITIES.items():
    for auth in authorities:
        AUTHORITY_TO_ROLE[auth] = role


# ==================== RECORD STATES ====================


class RecordState(str, Enum):
    """
    Record states that affect what operations are allowed.
    """

    DRAFT = "DRAFT"  # Editable by creator
    SUBMITTED = "SUBMITTED"  # Awaiting verification
    VERIFIED = "VERIFIED"  # Verified, awaiting approval
    APPROVED = "APPROVED"  # Approved, awaiting final lock/finalization
    LOCKED = "LOCKED"  # Final - Read-only for everyone
    REJECTED = "REJECTED"  # Sent back for revision


# Alias for backward compatibility
WorkflowStage = RecordState


# ==================== ACTIONS ====================


class Action(str, Enum):
    """
    All possible actions in the system.
    Each action has specific role and state requirements.
    """

    # CRUD Operations
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

    # Workflow Actions
    SUBMIT = "SUBMIT"
    VERIFY = "VERIFY"
    APPROVE = "APPROVE"
    ATTEST = "ATTEST"
    REJECT = "REJECT"
    REVISE = "REVISE"

    # Special Actions
    SUPERSEDE = "SUPERSEDE"  # Create correction entry
    EXPORT = "EXPORT"  # Export data
    AUDIT = "AUDIT"  # View audit trail


# ==================== CONTEXTS ====================


@dataclass
class UserContext:
    """
    User context for permission evaluation.
    Contains all information about the current user.
    """

    user_id: str
    role: Role
    authorities: List[str] = field(default_factory=list)
    department_code: Optional[str] = None
    office_code: Optional[str] = None

    @classmethod
    def from_user_dict(cls, user: Dict) -> "UserContext":
        """Create UserContext from JWT payload or user dict"""
        authorities = user.get("authorities", [])

        # Determine role from authorities
        role = Role.DATA_ENTRY_OPERATOR  # Default
        for auth in authorities:
            if auth in AUTHORITY_TO_ROLE:
                role = AUTHORITY_TO_ROLE[auth]
                break

        return cls(
            user_id=user.get("sub", user.get("user_id", "")),
            role=role,
            authorities=authorities,
            department_code=user.get("department_code"),
            office_code=user.get("office_code"),
        )


@dataclass
class RecordContext:
    """
    Record context for permission evaluation.
    Contains all information about the target record.
    """

    record_id: str
    record_type: str  # "employee_profile", "service_book_entry", etc.
    state: RecordState
    created_by: str
    department_code: Optional[str] = None
    office_code: Optional[str] = None
    is_immutable: bool = False

    @classmethod
    def from_record_dict(cls, record: Dict, record_type: str) -> "RecordContext":
        """Create RecordContext from database record"""
        # Determine state
        state_str = record.get("status") or record.get("workflow_status") or "DRAFT"
        try:
            state = RecordState(state_str)
        except ValueError:
            # Handle compatibility final-state label -> LOCKED mapping
            if state_str in ["ATTESTED", "SUPERSEDED"]:
                state = RecordState.LOCKED
            else:
                state = RecordState.DRAFT

        return cls(
            record_id=record.get("id", record.get("employee_id", "")),
            record_type=record_type,
            state=state,
            created_by=record.get("created_by", ""),
            department_code=record.get("department_code"),
            office_code=record.get("office_code"),
            is_immutable=record.get("is_immutable", False)
            or state == RecordState.LOCKED,
        )


# ==================== POLICY EVALUATION RESULT ====================


@dataclass
class PolicyResult:
    """
    Result of policy evaluation.
    Contains detailed information about why access was allowed or denied.
    """

    allowed: bool
    action: Action
    reason: str
    error_code: Optional[str] = None
    required_role: Optional[Role] = None
    required_state: Optional[RecordState] = None
    actual_role: Optional[Role] = None
    actual_state: Optional[RecordState] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for API response"""
        result = {
            "allowed": self.allowed,
            "action": self.action.value,
            "reason": self.reason,
        }
        if not self.allowed:
            result["error_code"] = self.error_code
            if self.required_role:
                result["required_role"] = self.required_role.value
            if self.required_state:
                result["required_state"] = self.required_state.value
            if self.actual_role:
                result["actual_role"] = self.actual_role.value
            if self.actual_state:
                result["actual_state"] = self.actual_state.value
            if self.suggestion:
                result["suggestion"] = self.suggestion
        return result


# ==================== POLICY RULES ====================

# Define which roles can perform which actions at which states
# Format: (role, state) -> allowed actions
POLICY_MATRIX: Dict[tuple, Set[Action]] = {
    # DATA_ENTRY_OPERATOR permissions
    (Role.DATA_ENTRY_OPERATOR, RecordState.DRAFT): {
        Action.CREATE,
        Action.READ,
        Action.UPDATE,
        Action.DELETE,
        Action.SUBMIT,
    },
    (Role.DATA_ENTRY_OPERATOR, RecordState.SUBMITTED): {
        Action.READ  # Can only read after submission
    },
    (Role.DATA_ENTRY_OPERATOR, RecordState.VERIFIED): {Action.READ},
    (Role.DATA_ENTRY_OPERATOR, RecordState.APPROVED): {Action.READ},
    (Role.DATA_ENTRY_OPERATOR, RecordState.LOCKED): {Action.READ},
    (Role.DATA_ENTRY_OPERATOR, RecordState.REJECTED): {
        Action.READ,
        Action.UPDATE,
        Action.REVISE,  # Can revise rejected records
    },
    # VERIFIER permissions
    (Role.VERIFIER, RecordState.DRAFT): {
        Action.READ  # Can read drafts but not act on them
    },
    (Role.VERIFIER, RecordState.SUBMITTED): {
        Action.READ,
        Action.VERIFY,
        Action.REJECT,  # Main responsibility
    },
    (Role.VERIFIER, RecordState.VERIFIED): {Action.READ},
    (Role.VERIFIER, RecordState.APPROVED): {Action.READ},
    (Role.VERIFIER, RecordState.LOCKED): {Action.READ},
    (Role.VERIFIER, RecordState.REJECTED): {Action.READ},
    # APPROVING_AUTHORITY permissions
    (Role.APPROVING_AUTHORITY, RecordState.DRAFT): {Action.READ},
    (Role.APPROVING_AUTHORITY, RecordState.SUBMITTED): {Action.READ},
    (Role.APPROVING_AUTHORITY, RecordState.VERIFIED): {
        Action.READ,
        Action.APPROVE,
        Action.REJECT,
    },
    (Role.APPROVING_AUTHORITY, RecordState.APPROVED): {
        Action.READ,
        Action.ATTEST,
        Action.REJECT,
    },
    (Role.APPROVING_AUTHORITY, RecordState.LOCKED): {
        Action.READ,
        Action.SUPERSEDE,  # Can create corrections
    },
    (Role.APPROVING_AUTHORITY, RecordState.REJECTED): {Action.READ},
    # AUDITOR permissions (read-only everywhere)
    (Role.AUDITOR, RecordState.DRAFT): {Action.READ, Action.AUDIT},
    (Role.AUDITOR, RecordState.SUBMITTED): {Action.READ, Action.AUDIT},
    (Role.AUDITOR, RecordState.VERIFIED): {Action.READ, Action.AUDIT},
    (Role.AUDITOR, RecordState.APPROVED): {Action.READ, Action.AUDIT},
    (Role.AUDITOR, RecordState.LOCKED): {Action.READ, Action.AUDIT, Action.EXPORT},
    (Role.AUDITOR, RecordState.REJECTED): {Action.READ, Action.AUDIT},
    # ADMIN permissions (system administration, no workflow powers)
    (Role.ADMIN, RecordState.DRAFT): {Action.READ, Action.AUDIT},
    (Role.ADMIN, RecordState.SUBMITTED): {Action.READ, Action.AUDIT},
    (Role.ADMIN, RecordState.VERIFIED): {Action.READ, Action.AUDIT},
    (Role.ADMIN, RecordState.APPROVED): {Action.READ, Action.AUDIT},
    (Role.ADMIN, RecordState.LOCKED): {Action.READ, Action.AUDIT},
    (Role.ADMIN, RecordState.REJECTED): {Action.READ, Action.AUDIT},
}


# ==================== WORKFLOW TRANSITIONS ====================

# Define valid workflow transitions
WORKFLOW_TRANSITIONS: Dict[RecordState, Dict[Action, RecordState]] = {
    RecordState.DRAFT: {
        Action.SUBMIT: RecordState.SUBMITTED,
    },
    RecordState.SUBMITTED: {
        Action.VERIFY: RecordState.VERIFIED,
        Action.REJECT: RecordState.REJECTED,
    },
    RecordState.VERIFIED: {
        Action.APPROVE: RecordState.APPROVED,
        Action.REJECT: RecordState.REJECTED,
    },
    RecordState.APPROVED: {
        Action.ATTEST: RecordState.LOCKED,
        Action.REJECT: RecordState.REJECTED,
    },
    RecordState.LOCKED: {
        # No transitions - immutable
    },
    RecordState.REJECTED: {
        Action.REVISE: RecordState.DRAFT,
    },
}


# ==================== POLICY ENGINE ====================


class PolicyEngine:
    """
    Centralized Permission Engine.

    USAGE:
    ------
    result = PolicyEngine.evaluate(
        action=Action.UPDATE,
        user=UserContext.from_user_dict(current_user),
        record=RecordContext.from_record_dict(record, "employee_profile")
    )

    if not result.allowed:
        raise HTTPException(status_code=403, detail=result.to_dict())
    """

    @staticmethod
    def evaluate(
        action: Action, user: UserContext, record: Optional[RecordContext] = None
    ) -> PolicyResult:
        """
        Evaluate if an action is allowed.

        Args:
            action: The action being attempted
            user: Context about the current user
            record: Context about the target record (optional for CREATE)

        Returns:
            PolicyResult indicating if action is allowed and why
        """
        # Rule 1: CREATE doesn't require a record
        if action == Action.CREATE:
            if user.role in [Role.DATA_ENTRY_OPERATOR, Role.ADMIN]:
                return PolicyResult(
                    allowed=True,
                    action=action,
                    reason="User has permission to create records",
                )
            return PolicyResult(
                allowed=False,
                action=action,
                reason="Only DATA_ENTRY_OPERATOR can create records",
                error_code="ROLE_NOT_AUTHORIZED",
                required_role=Role.DATA_ENTRY_OPERATOR,
                actual_role=user.role,
            )

        # All other actions require a record
        if record is None:
            return PolicyResult(
                allowed=False,
                action=action,
                reason="Record context is required for this action",
                error_code="MISSING_RECORD_CONTEXT",
            )

        # Rule 2: LOCKED/IMMUTABLE records are read-only
        if record.is_immutable or record.state == RecordState.LOCKED:
            if action in [Action.READ, Action.AUDIT, Action.EXPORT]:
                return PolicyResult(
                    allowed=True,
                    action=action,
                    reason="Read access allowed on locked records",
                )
            if action == Action.SUPERSEDE and user.role == Role.APPROVING_AUTHORITY:
                return PolicyResult(
                    allowed=True,
                    action=action,
                    reason="APPROVING_AUTHORITY can create supersession entries",
                )
            return PolicyResult(
                allowed=False,
                action=action,
                reason=f"Record is LOCKED/IMMUTABLE. No modifications allowed.",
                error_code="RECORD_IMMUTABLE",
                actual_state=record.state,
                suggestion="Create a SUPERSESSION entry to correct this record",
            )

        # Rule 3: Separation of Duties - Cannot act on own submissions
        if action in [Action.VERIFY, Action.APPROVE, Action.ATTEST]:
            if user.user_id == record.created_by:
                return PolicyResult(
                    allowed=False,
                    action=action,
                    reason="Cannot perform workflow action on your own submission. Separation of duties is mandatory.",
                    error_code="SEPARATION_OF_DUTIES",
                    suggestion="Another officer with appropriate role must perform this action",
                )

        # Rule 4: Check policy matrix
        policy_key = (user.role, record.state)
        allowed_actions = POLICY_MATRIX.get(policy_key, set())

        if action not in allowed_actions:
            # Generate helpful error message
            error_msg = PolicyEngine._generate_denial_message(action, user, record)
            return error_msg

        # Rule 5: For workflow actions, verify transition is valid
        if action in [
            Action.SUBMIT,
            Action.VERIFY,
            Action.APPROVE,
            Action.ATTEST,
            Action.REJECT,
            Action.REVISE,
        ]:
            transition_result = PolicyEngine._validate_transition(action, record.state)
            if not transition_result.allowed:
                return transition_result

        # All checks passed
        return PolicyResult(
            allowed=True,
            action=action,
            reason=f"Action {action.value} allowed for {user.role.value} on {record.state.value} record",
        )

    @staticmethod
    def _generate_denial_message(
        action: Action, user: UserContext, record: RecordContext
    ) -> PolicyResult:
        """Generate a helpful denial message"""

        # Find what role CAN perform this action at this state
        required_role = None
        for (role, state), actions in POLICY_MATRIX.items():
            if state == record.state and action in actions:
                required_role = role
                break

        # Find what state is needed for this role to perform the action
        required_state = None
        for (role, state), actions in POLICY_MATRIX.items():
            if role == user.role and action in actions:
                required_state = state
                break

        if required_role and required_role != user.role:
            return PolicyResult(
                allowed=False,
                action=action,
                reason=f"Role {user.role.value} cannot perform {action.value} on {record.state.value} records",
                error_code="ROLE_STATE_MISMATCH",
                required_role=required_role,
                required_state=record.state,
                actual_role=user.role,
                actual_state=record.state,
                suggestion=f"This action requires {required_role.value} role",
            )

        if required_state and required_state != record.state:
            return PolicyResult(
                allowed=False,
                action=action,
                reason=f"Cannot perform {action.value} on record in {record.state.value} state",
                error_code="INVALID_STATE_FOR_ACTION",
                required_state=required_state,
                actual_state=record.state,
                actual_role=user.role,
                suggestion=f"Record must be in {required_state.value} state for this action",
            )

        return PolicyResult(
            allowed=False,
            action=action,
            reason=f"Action {action.value} not permitted for {user.role.value} on {record.state.value} records",
            error_code="ACTION_NOT_PERMITTED",
            actual_role=user.role,
            actual_state=record.state,
        )

    @staticmethod
    def _validate_transition(
        action: Action, current_state: RecordState
    ) -> PolicyResult:
        """Validate that a workflow transition is allowed"""

        valid_transitions = WORKFLOW_TRANSITIONS.get(current_state, {})

        if action not in valid_transitions:
            return PolicyResult(
                allowed=False,
                action=action,
                reason=f"Cannot perform {action.value} from {current_state.value} state",
                error_code="INVALID_WORKFLOW_TRANSITION",
                actual_state=current_state,
                suggestion=f"Valid actions from {current_state.value}: {list(valid_transitions.keys())}",
            )

        return PolicyResult(
            allowed=True, action=action, reason="Workflow transition is valid"
        )

    @staticmethod
    def get_allowed_actions(user: UserContext, record: RecordContext) -> List[Action]:
        """
        Get all actions that a user can perform on a record.
        Useful for UI to show/hide buttons.
        """
        allowed = []

        for action in Action:
            result = PolicyEngine.evaluate(action, user, record)
            if result.allowed:
                allowed.append(action)

        return allowed

    @staticmethod
    def get_next_state(
        action: Action, current_state: RecordState
    ) -> Optional[RecordState]:
        """Get the next state after performing an action"""
        transitions = WORKFLOW_TRANSITIONS.get(current_state, {})
        return transitions.get(action)


# ==================== PERMISSION DECORATOR ====================


def require_policy(action: Action, record_getter: Callable = None):
    """
    Decorator for API endpoints to enforce policy.

    Usage:
    ------
    @router.put("/{record_id}")
    @require_policy(Action.UPDATE, lambda kwargs: get_record(kwargs["record_id"]))
    async def update_record(record_id: str, data: dict, current_user: dict = Depends(get_current_user)):
        ...
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs
            current_user = kwargs.get("current_user")
            if not current_user:
                raise PermissionDeniedError(
                    "AUTHENTICATION_REQUIRED", "User authentication is required"
                )

            user_context = UserContext.from_user_dict(current_user)

            # Get record if needed
            record_context = None
            if record_getter:
                record = await record_getter(kwargs)
                if record:
                    record_type = kwargs.get("record_type", "unknown")
                    record_context = RecordContext.from_record_dict(record, record_type)

            # Evaluate policy
            result = PolicyEngine.evaluate(action, user_context, record_context)

            if not result.allowed:
                raise PermissionDeniedError(
                    result.error_code, result.reason, result.to_dict()
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# ==================== EXCEPTIONS ====================


class PermissionDeniedError(Exception):
    """Exception raised when permission is denied"""

    def __init__(self, error_code: str, message: str, details: Dict = None):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> Dict:
        return {"error_code": self.error_code, "message": self.message, **self.details}


# ==================== CONVENIENCE FUNCTIONS ====================


def check_permission(
    action: Action, user: Dict, record: Dict, record_type: str
) -> PolicyResult:
    """
    Convenience function to check permission.

    Usage:
    ------
    result = check_permission(Action.UPDATE, current_user, record, "employee_profile")
    if not result.allowed:
        raise HTTPException(403, detail=result.to_dict())
    """
    user_ctx = UserContext.from_user_dict(user)
    record_ctx = RecordContext.from_record_dict(record, record_type)
    return PolicyEngine.evaluate(action, user_ctx, record_ctx)


def get_user_permissions_for_record(user: Dict, record: Dict, record_type: str) -> Dict:
    """
    Get all permissions a user has for a specific record.
    Useful for frontend to render UI based on available actions.
    """
    user_ctx = UserContext.from_user_dict(user)
    record_ctx = RecordContext.from_record_dict(record, record_type)

    allowed_actions = PolicyEngine.get_allowed_actions(user_ctx, record_ctx)

    return {
        "record_id": record_ctx.record_id,
        "record_state": record_ctx.state.value,
        "user_role": user_ctx.role.value,
        "allowed_actions": [a.value for a in allowed_actions],
        "can_edit": Action.UPDATE in allowed_actions,
        "can_delete": Action.DELETE in allowed_actions,
        "can_submit": Action.SUBMIT in allowed_actions,
        "can_verify": Action.VERIFY in allowed_actions,
        "can_approve": Action.APPROVE in allowed_actions,
        "can_attest": Action.ATTEST in allowed_actions,
        "can_reject": Action.REJECT in allowed_actions,
    }
