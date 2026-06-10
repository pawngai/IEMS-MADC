# Authority-Based RBAC Model - Compliant
# This replaces simple role-based access with authority-based workflow

from pydantic import BaseModel, Field
from typing import Optional, List, Set, Dict
from datetime import datetime, timezone
from enum import Enum
import uuid

# ==================== AUTHORITIES ====================

class Authority(str, Enum):
    """
    Authorities in government HRMS hierarchy.
    Each authority has specific powers and workflow responsibilities.
    """
    # Core Authorities
    EMPLOYEE = "EMPLOYEE"                       # Basic employee access
    DEPT_DATA_ENTRY = "DEPT_DATA_ENTRY"         # Departmental data entry operator (department-scoped)
    GLOBAL_DATA_ENTRY = "GLOBAL_DATA_ENTRY"     # Global data entry operator (cross-department)
    DEALING_ASSISTANT = "DEALING_ASSISTANT"     # Dealing hand
    SECTION_OFFICER = "SECTION_OFFICER"         # Section officer
    VERIFIER = "VERIFIER"                       # Verification authority
    NODAL_OFFICER = "NODAL_OFFICER"             # Nodal officer (reserved)
    DDO = "DDO"                                 # Drawing & Disbursing Officer
    APPROVING_AUTHORITY = "APPROVING_AUTHORITY"  # Approving Authority
    HOD = "HOD"                                 # Head of Department
    APPOINTING_AUTHORITY = "APPOINTING_AUTHORITY"  # For appointments
    DISCIPLINARY_AUTHORITY = "DISCIPLINARY_AUTHORITY"  # For disciplinary matters
    AUDITOR = "AUDITOR"                         # Audit/compliance
    SYSTEM_ADMIN = "SYSTEM_ADMIN"               # System administration

# ==================== PERMISSIONS ====================

class Permission(str, Enum):
    """Granular permissions for each action"""
    
    # Employee Profile Permissions
    PROFILE_READ_OWN = "PROFILE_READ_OWN"
    PROFILE_READ_ALL = "PROFILE_READ_ALL"
    PROFILE_CREATE = "PROFILE_CREATE"
    PROFILE_UPDATE_OWN_LIMITED = "PROFILE_UPDATE_OWN_LIMITED"  # ESS editable fields
    PROFILE_UPDATE_ALL = "PROFILE_UPDATE_ALL"

    # Core Employee Identity Permissions
    IDENTITY_READ_OWN = PROFILE_READ_OWN
    IDENTITY_READ_ALL = PROFILE_READ_ALL
    IDENTITY_CREATE = PROFILE_CREATE
    IDENTITY_UPDATE_ALL = PROFILE_UPDATE_ALL
    
    # Service Book Permissions
    SERVICE_BOOK_READ_OWN = "SERVICE_BOOK_READ_OWN"
    SERVICE_BOOK_READ_ALL = "SERVICE_BOOK_READ_ALL"
    SERVICE_BOOK_ENTRY_CREATE = "SERVICE_BOOK_ENTRY_CREATE"
    SERVICE_BOOK_ENTRY_SUBMIT = "SERVICE_BOOK_ENTRY_SUBMIT"
    SERVICE_BOOK_ENTRY_VERIFY = "SERVICE_BOOK_ENTRY_VERIFY"
    SERVICE_BOOK_ENTRY_APPROVE = "SERVICE_BOOK_ENTRY_APPROVE"
    SERVICE_BOOK_ENTRY_ATTEST = "SERVICE_BOOK_ENTRY_ATTEST"
    SERVICE_BOOK_OPENING_CREATE = "SERVICE_BOOK_OPENING_CREATE"
    SERVICE_BOOK_OPENING_UPDATE = "SERVICE_BOOK_OPENING_UPDATE"
    SERVICE_BOOK_OPENING_SUBMIT = "SERVICE_BOOK_OPENING_SUBMIT"
    SERVICE_BOOK_OPENING_VERIFY = "SERVICE_BOOK_OPENING_VERIFY"
    SERVICE_BOOK_OPENING_APPROVE = "SERVICE_BOOK_OPENING_APPROVE"
    SERVICE_BOOK_SUPERSEDE = "SERVICE_BOOK_SUPERSEDE"  # Create correction entry
    SERVICE_BOOK_PRINT = "SERVICE_BOOK_PRINT"
    
    # Establishment Permissions
    ESTABLISHMENT_APPOINTMENT = "ESTABLISHMENT_APPOINTMENT"
    ESTABLISHMENT_PROMOTION = "ESTABLISHMENT_PROMOTION"
    ESTABLISHMENT_TRANSFER = "ESTABLISHMENT_TRANSFER"
    ESTABLISHMENT_PAY_FIXATION = "ESTABLISHMENT_PAY_FIXATION"
    ESTABLISHMENT_RETIREMENT = "ESTABLISHMENT_RETIREMENT"
    
    # Leave Permissions
    LEAVE_APPLY_OWN = "LEAVE_APPLY_OWN"
    LEAVE_READ_OWN = "LEAVE_READ_OWN"
    LEAVE_READ_ALL = "LEAVE_READ_ALL"
    LEAVE_RECOMMEND = "LEAVE_RECOMMEND"
    LEAVE_SANCTION = "LEAVE_SANCTION"

    # Document Permissions
    DOCUMENT_READ_OWN = "DOCUMENT_READ_OWN"
    
    # Disciplinary Permissions
    DISCIPLINARY_INITIATE = "DISCIPLINARY_INITIATE"
    DISCIPLINARY_INQUIRE = "DISCIPLINARY_INQUIRE"
    DISCIPLINARY_PENALIZE = "DISCIPLINARY_PENALIZE"
    
    # Audit Permissions
    AUDIT_READ_ALL = "AUDIT_READ_ALL"
    AUDIT_GENERATE_REPORTS = "AUDIT_GENERATE_REPORTS"
    
    # Master Data Permissions
    MASTER_READ = "MASTER_READ"
    MASTER_CREATE = "MASTER_CREATE"
    MASTER_UPDATE = "MASTER_UPDATE"
    
    # Identity Workflow Permissions
    IDENTITY_SUBMIT = "IDENTITY_SUBMIT"
    IDENTITY_VERIFY = "IDENTITY_VERIFY"
    IDENTITY_ACTIVATE = "IDENTITY_ACTIVATE"
    IDENTITY_REJECT = "IDENTITY_REJECT"

    # System Permissions
    SYSTEM_CONFIG = "SYSTEM_CONFIG"
    USER_MANAGEMENT = "USER_MANAGEMENT"

# ==================== RBAC MATRIX ====================

AUTHORITY_PERMISSIONS: Dict[Authority, Set[Permission]] = {
    Authority.EMPLOYEE: {
        Permission.IDENTITY_READ_OWN,
        Permission.PROFILE_UPDATE_OWN_LIMITED,
        Permission.SERVICE_BOOK_READ_OWN,
        Permission.LEAVE_APPLY_OWN,
        Permission.LEAVE_READ_OWN,
        Permission.DOCUMENT_READ_OWN,
        Permission.MASTER_READ,
    },

    Authority.DEPT_DATA_ENTRY: {
        Permission.IDENTITY_READ_ALL,
        Permission.IDENTITY_CREATE,
        Permission.IDENTITY_UPDATE_ALL,
        Permission.IDENTITY_SUBMIT,
        Permission.SERVICE_BOOK_READ_ALL,
        Permission.SERVICE_BOOK_ENTRY_CREATE,
        Permission.SERVICE_BOOK_ENTRY_SUBMIT,
        Permission.LEAVE_READ_ALL,
        Permission.MASTER_READ,
        Permission.IDENTITY_READ_OWN,
        Permission.PROFILE_UPDATE_OWN_LIMITED,
        Permission.SERVICE_BOOK_READ_OWN,
        Permission.LEAVE_APPLY_OWN,
        Permission.LEAVE_READ_OWN,
    },

    Authority.GLOBAL_DATA_ENTRY: {
        Permission.IDENTITY_READ_ALL,
        Permission.IDENTITY_CREATE,
        Permission.IDENTITY_UPDATE_ALL,
        Permission.IDENTITY_SUBMIT,
        Permission.SERVICE_BOOK_READ_ALL,
        Permission.SERVICE_BOOK_ENTRY_CREATE,
        Permission.SERVICE_BOOK_ENTRY_SUBMIT,
        Permission.SERVICE_BOOK_OPENING_CREATE,
        Permission.SERVICE_BOOK_OPENING_UPDATE,
        Permission.SERVICE_BOOK_OPENING_SUBMIT,
        Permission.LEAVE_READ_ALL,
        Permission.MASTER_READ,
        Permission.IDENTITY_READ_OWN,
        Permission.PROFILE_UPDATE_OWN_LIMITED,
        Permission.SERVICE_BOOK_READ_OWN,
        Permission.LEAVE_APPLY_OWN,
        Permission.LEAVE_READ_OWN,
    },

    Authority.DEALING_ASSISTANT: {
        Permission.IDENTITY_READ_ALL,
        Permission.IDENTITY_CREATE,
        Permission.IDENTITY_UPDATE_ALL,
        Permission.IDENTITY_SUBMIT,
        Permission.SERVICE_BOOK_READ_ALL,
        Permission.SERVICE_BOOK_ENTRY_CREATE,
        Permission.SERVICE_BOOK_ENTRY_SUBMIT,
        Permission.SERVICE_BOOK_OPENING_CREATE,
        Permission.SERVICE_BOOK_OPENING_UPDATE,
        Permission.SERVICE_BOOK_OPENING_SUBMIT,
        Permission.LEAVE_READ_ALL,
        Permission.MASTER_READ,
        Permission.IDENTITY_READ_OWN,
        Permission.PROFILE_UPDATE_OWN_LIMITED,
        Permission.SERVICE_BOOK_READ_OWN,
        Permission.LEAVE_APPLY_OWN,
        Permission.LEAVE_READ_OWN,
    },

    Authority.SECTION_OFFICER: {
        Permission.IDENTITY_READ_ALL,
        Permission.SERVICE_BOOK_READ_ALL,
        Permission.SERVICE_BOOK_ENTRY_CREATE,
        Permission.SERVICE_BOOK_ENTRY_SUBMIT,
        Permission.LEAVE_READ_ALL,
        Permission.MASTER_READ,
        Permission.IDENTITY_READ_OWN,
        Permission.PROFILE_UPDATE_OWN_LIMITED,
        Permission.SERVICE_BOOK_READ_OWN,
        Permission.LEAVE_APPLY_OWN,
        Permission.LEAVE_READ_OWN,
    },

    Authority.VERIFIER: {
        Permission.IDENTITY_READ_ALL,
        Permission.IDENTITY_VERIFY,
        Permission.IDENTITY_REJECT,
        Permission.SERVICE_BOOK_READ_ALL,
        Permission.SERVICE_BOOK_OPENING_VERIFY,
        Permission.SERVICE_BOOK_ENTRY_VERIFY,
        Permission.LEAVE_READ_ALL,
        Permission.MASTER_READ,
        Permission.IDENTITY_READ_OWN,
        Permission.PROFILE_UPDATE_OWN_LIMITED,
        Permission.SERVICE_BOOK_READ_OWN,
        Permission.LEAVE_APPLY_OWN,
        Permission.LEAVE_READ_OWN,
    },

    Authority.NODAL_OFFICER: {
        Permission.IDENTITY_READ_ALL,
        Permission.MASTER_READ,
        Permission.IDENTITY_READ_OWN,
        Permission.PROFILE_UPDATE_OWN_LIMITED,
        Permission.SERVICE_BOOK_READ_OWN,
        Permission.LEAVE_APPLY_OWN,
        Permission.LEAVE_READ_OWN,
    },



    Authority.DDO: {
        Permission.IDENTITY_READ_ALL,
        Permission.SERVICE_BOOK_READ_ALL,
        Permission.SERVICE_BOOK_OPENING_APPROVE,
        Permission.SERVICE_BOOK_ENTRY_APPROVE,
        Permission.SERVICE_BOOK_PRINT,
        Permission.ESTABLISHMENT_PAY_FIXATION,
        Permission.LEAVE_READ_ALL,
        Permission.LEAVE_SANCTION,
        Permission.MASTER_READ,
        Permission.IDENTITY_READ_OWN,
        Permission.PROFILE_UPDATE_OWN_LIMITED,
        Permission.SERVICE_BOOK_READ_OWN,
        Permission.LEAVE_APPLY_OWN,
        Permission.LEAVE_READ_OWN,
    },

    Authority.APPROVING_AUTHORITY: {
        Permission.IDENTITY_READ_ALL,
        Permission.IDENTITY_UPDATE_ALL,
        Permission.IDENTITY_ACTIVATE,
        Permission.IDENTITY_REJECT,
        Permission.SERVICE_BOOK_READ_ALL,
        Permission.SERVICE_BOOK_OPENING_APPROVE,
        Permission.SERVICE_BOOK_ENTRY_CREATE,
        Permission.SERVICE_BOOK_ENTRY_SUBMIT,
        Permission.SERVICE_BOOK_ENTRY_VERIFY,
        Permission.SERVICE_BOOK_ENTRY_APPROVE,
        Permission.SERVICE_BOOK_ENTRY_ATTEST,
        Permission.SERVICE_BOOK_SUPERSEDE,
        Permission.SERVICE_BOOK_PRINT,
        Permission.ESTABLISHMENT_APPOINTMENT,
        Permission.ESTABLISHMENT_PROMOTION,
        Permission.ESTABLISHMENT_TRANSFER,
        Permission.ESTABLISHMENT_PAY_FIXATION,
        Permission.ESTABLISHMENT_RETIREMENT,
        Permission.LEAVE_READ_ALL,
        Permission.LEAVE_SANCTION,
        Permission.DISCIPLINARY_INITIATE,
        Permission.MASTER_READ,
        Permission.IDENTITY_READ_OWN,
        Permission.PROFILE_UPDATE_OWN_LIMITED,
        Permission.SERVICE_BOOK_READ_OWN,
        Permission.LEAVE_APPLY_OWN,
        Permission.LEAVE_READ_OWN,
    },

    # HOD is the Recommending Authority for leave (department-scoped).
    Authority.HOD: {
        Permission.IDENTITY_READ_ALL,
        Permission.IDENTITY_UPDATE_ALL,
        Permission.SERVICE_BOOK_READ_ALL,
        Permission.SERVICE_BOOK_ENTRY_CREATE,
        Permission.SERVICE_BOOK_ENTRY_SUBMIT,
        Permission.SERVICE_BOOK_ENTRY_VERIFY,
        Permission.SERVICE_BOOK_ENTRY_APPROVE,
        Permission.SERVICE_BOOK_ENTRY_ATTEST,
        Permission.SERVICE_BOOK_SUPERSEDE,
        Permission.SERVICE_BOOK_PRINT,
        Permission.ESTABLISHMENT_APPOINTMENT,
        Permission.ESTABLISHMENT_PROMOTION,
        Permission.ESTABLISHMENT_TRANSFER,
        Permission.ESTABLISHMENT_PAY_FIXATION,
        Permission.ESTABLISHMENT_RETIREMENT,
        Permission.LEAVE_READ_ALL,
        Permission.LEAVE_RECOMMEND,
        Permission.MASTER_READ,
        Permission.IDENTITY_READ_OWN,
        Permission.PROFILE_UPDATE_OWN_LIMITED,
        Permission.SERVICE_BOOK_READ_OWN,
        Permission.LEAVE_APPLY_OWN,
        Permission.LEAVE_READ_OWN,
    },

    Authority.APPOINTING_AUTHORITY: {
        Permission.IDENTITY_READ_ALL,
        Permission.SERVICE_BOOK_READ_ALL,
        Permission.SERVICE_BOOK_ENTRY_ATTEST,
        Permission.SERVICE_BOOK_PRINT,
        Permission.ESTABLISHMENT_APPOINTMENT,
        Permission.MASTER_READ,
        Permission.IDENTITY_READ_OWN,
        Permission.PROFILE_UPDATE_OWN_LIMITED,
        Permission.SERVICE_BOOK_READ_OWN,
        Permission.LEAVE_APPLY_OWN,
        Permission.LEAVE_READ_OWN,
    },

    Authority.DISCIPLINARY_AUTHORITY: {
        Permission.IDENTITY_READ_ALL,
        Permission.SERVICE_BOOK_READ_ALL,
        Permission.SERVICE_BOOK_ENTRY_CREATE,
        Permission.SERVICE_BOOK_ENTRY_ATTEST,
        Permission.DISCIPLINARY_INITIATE,
        Permission.DISCIPLINARY_INQUIRE,
        Permission.DISCIPLINARY_PENALIZE,
        Permission.MASTER_READ,
        Permission.IDENTITY_READ_OWN,
        Permission.PROFILE_UPDATE_OWN_LIMITED,
        Permission.SERVICE_BOOK_READ_OWN,
        Permission.LEAVE_APPLY_OWN,
        Permission.LEAVE_READ_OWN,
    },

    Authority.AUDITOR: {
        Permission.IDENTITY_READ_ALL,
        Permission.SERVICE_BOOK_READ_ALL,
        Permission.SERVICE_BOOK_PRINT,
        Permission.LEAVE_READ_ALL,
        Permission.AUDIT_READ_ALL,
        Permission.AUDIT_GENERATE_REPORTS,
        Permission.MASTER_READ,
        Permission.IDENTITY_READ_OWN,
        Permission.PROFILE_UPDATE_OWN_LIMITED,
        Permission.SERVICE_BOOK_READ_OWN,
        Permission.LEAVE_READ_OWN,
    },

    Authority.SYSTEM_ADMIN: {
        # Governance-only access: READ all, WRITE only policy/config/users
        # INVARIANT: SYSTEM_ADMIN NEVER writes to transactional records
        #   (profiles, service book entries, leave sanctions, leave applications)
        # The forbid_system_admin_write() guard in access_control.py
        # acts as defense-in-depth; the primary defense is this permission set.
        Permission.IDENTITY_READ_ALL,
        Permission.SERVICE_BOOK_READ_ALL,
        Permission.SERVICE_BOOK_PRINT,
        Permission.LEAVE_READ_ALL,
        Permission.AUDIT_READ_ALL,
        Permission.AUDIT_GENERATE_REPORTS,
        Permission.MASTER_READ,
        Permission.MASTER_CREATE,
        Permission.MASTER_UPDATE,
        Permission.SYSTEM_CONFIG,
        Permission.USER_MANAGEMENT,
        Permission.IDENTITY_READ_OWN,
        Permission.PROFILE_UPDATE_OWN_LIMITED,
        Permission.SERVICE_BOOK_READ_OWN,
        Permission.LEAVE_READ_OWN,
    },
}

# ==================== WORKFLOW STAGES ====================

class WorkflowStage(str, Enum):
    """Workflow stages for Service Book entries"""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    VERIFIED = "VERIFIED"
    APPROVED = "APPROVED"
    ATTESTED = "ATTESTED"  # Final - service book entries
    LOCKED = "LOCKED"      # Final - profiles
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"  # Replaced by correction entry

# Workflow transition rules
WORKFLOW_TRANSITIONS = {
    WorkflowStage.DRAFT: {
        "next_stages": [WorkflowStage.SUBMITTED],
        "required_authority": [Authority.DEPT_DATA_ENTRY, Authority.GLOBAL_DATA_ENTRY, Authority.DEALING_ASSISTANT],
        "can_edit": True,
    },
    WorkflowStage.SUBMITTED: {
        "next_stages": [WorkflowStage.VERIFIED, WorkflowStage.REJECTED],
        "required_authority": Authority.VERIFIER,
        "can_edit": False,
    },
    WorkflowStage.VERIFIED: {
        "next_stages": [WorkflowStage.APPROVED, WorkflowStage.REJECTED],
        "required_authority": Authority.APPROVING_AUTHORITY,
        "can_edit": False,
    },
    WorkflowStage.APPROVED: {
        "next_stages": [WorkflowStage.ATTESTED, WorkflowStage.REJECTED],
        "required_authority": Authority.APPROVING_AUTHORITY,
        "can_edit": False,
    },
    WorkflowStage.ATTESTED: {
        "next_stages": [],  # Final stage - immutable
        "required_authority": None,
        "can_edit": False,
    },
    WorkflowStage.REJECTED: {
        "next_stages": [WorkflowStage.DRAFT],  # Can be revised
        "required_authority": [Authority.DEPT_DATA_ENTRY, Authority.GLOBAL_DATA_ENTRY, Authority.DEALING_ASSISTANT],
        "can_edit": True,
    },
}

# ==================== USER MODEL ====================

class User(BaseModel):
    """User with authority-based access"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Authentication
    email: str
    password_hash: str
    
    # Profile
    name: str
    employee_id: Optional[str] = None  # Link to employee profile
    
    # Authority
    authorities: List[str] = [Authority.EMPLOYEE.value]
    
    # Office/Department context
    office_code: Optional[str] = None
    department_code: Optional[str] = None
    
    # Status
    is_active: bool = True
    is_locked: bool = False
    must_change_password: bool = False
    last_login: Optional[str] = None
    failed_login_attempts: int = 0
    
    # Audit
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    authorities: List[str] = [Authority.EMPLOYEE.value]
    employee_id: Optional[str] = None
    office_code: Optional[str] = None
    department_code: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    authorities: List[str]
    permissions: List[str]
    employee_id: Optional[str] = None
    office_code: Optional[str] = None
    department_code: Optional[str] = None
    must_change_password: bool = False

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: UserResponse
    expires_in: int = 1800  # 30 minutes (access token)

# ==================== AUDIT LOG ====================

class AuditLog(BaseModel):
    """Comprehensive audit log for all actions"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # Who
    user_id: str
    user_name: str
    authority: str
    
    # What
    action: str
    resource_type: str
    resource_id: str
    
    # Details
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    details: dict = {}
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Workflow (if applicable)
    workflow_stage: Optional[str] = None
    workflow_action: Optional[str] = None
