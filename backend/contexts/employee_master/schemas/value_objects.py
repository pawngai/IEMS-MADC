"""Employee Master embedded value objects.

Unifies the two divergent ContactDetails definitions (employee_identity
value_objects.py and employee_profile profile_model.py) and the write-path field
surface (update_profile_extension.CONTACT_FIELDS). To guarantee zero field loss
(risk R-2), ContactDetails declares BOTH the single-line form (`address`,
`present_address`) used by the stored model AND the line1/line2 form
(`address_line1/2`, `present_address_line1/2`) used by the write API.
"""

from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, field_validator


class ContactDetails(BaseModel):
    """Contact information — ESS editable. Superset of both legacy definitions."""

    mobile_primary: Optional[str] = None
    mobile_alternate: Optional[str] = None
    email_personal: Optional[str] = None
    email_official: Optional[str] = None

    # Permanent / current address — single-line (legacy stored model) ...
    address: Optional[str] = None
    # ... and line1/line2 (legacy write-path). Both preserved; see R-2.
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None

    # Present address — single-line and line1/line2 forms both preserved.
    present_address: Optional[str] = None
    present_address_line1: Optional[str] = None
    present_address_line2: Optional[str] = None
    present_city: Optional[str] = None
    present_district: Optional[str] = None
    present_state: Optional[str] = None
    present_pincode: Optional[str] = None

    # Emergency contact
    emergency_name: Optional[str] = None
    emergency_phone: Optional[str] = None
    emergency_relation: Optional[str] = None

    @field_validator("mobile_primary", "mobile_alternate")
    @classmethod
    def validate_mobile(cls, v):
        if v and not re.match(r"^[6-9]\d{9}$", v):
            raise ValueError("Invalid Indian mobile number")
        return v

    @field_validator("pincode", "present_pincode")
    @classmethod
    def validate_pincode(cls, v):
        if v and not re.match(r"^\d{6}$", v):
            raise ValueError("Invalid pincode")
        return v


class IdentityDocuments(BaseModel):
    """Government identifier documents (embedded)."""

    aadhaar_number: Optional[str] = None
    pan_number: Optional[str] = None

    @field_validator("aadhaar_number")
    @classmethod
    def validate_aadhaar(cls, value):
        if value and not re.match(r"^\d{12}$", value):
            raise ValueError("Aadhaar must be 12 digits")
        return value

    @field_validator("pan_number")
    @classmethod
    def validate_pan(cls, value):
        if value and not re.match(r"^[A-Z]{5}\d{4}[A-Z]$", value.upper()):
            raise ValueError("Invalid PAN format")
        return value.upper() if value else value
