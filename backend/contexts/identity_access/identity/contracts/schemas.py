from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field
from typing import Any, List, Optional

# Re-export existing RBAC primitives for compatibility across the codebase.
from contexts.identity_access.contracts.models import Authority, Permission  # noqa: F401


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ModuleAccessResponse(BaseModel):
    mode: str
    allowed_modules: Optional[List[str]] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    authorities: List[str]
    employee_id: Optional[str] = None
    office_code: Optional[str] = None
    department_code: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    authorities: Optional[List[str]] = None
    employee_id: Optional[str] = None
    office_code: Optional[str] = None
    department_code: Optional[str] = None
    is_active: Optional[bool] = None


class AuthorityPatch(BaseModel):
    add: Optional[List[str]] = None
    remove: Optional[List[str]] = None
    department_code: Optional[str] = None


class UserPasswordUpdate(BaseModel):
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    authorities: List[str]
    employee_id: Optional[str] = None
    office_code: Optional[str] = None
    department_code: Optional[str] = None
    must_change_password: bool = False
    is_active: bool = True
    created_at: Optional[str] = None


class EmployeeAccountProvisionRequest(BaseModel):
    employee_id: str
    email: EmailStr


class EmployeeAccountProvisionResponse(BaseModel):
    user_id: str
    email: str
    employee_id: str
    must_change_password: bool = True
    temp_password: Optional[str] = None
    already_exists: bool = False
    linked_existing_user: bool = False
    message: str


class ActivityLogResponse(BaseModel):
    id: str
    action: str
    target_user_id: Optional[str] = None
    target_user_email: Optional[str] = None
    target_user_name: Optional[str] = None
    performed_by_id: str
    performed_by_name: str
    performed_by_email: str
    details: Optional[dict[str, Any]] = None
    timestamp: str


class SystemAdminRequired(BaseModel):
    reason: str = Field(..., min_length=10)

