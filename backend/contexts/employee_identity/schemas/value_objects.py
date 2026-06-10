"""Embedded value objects used by employee records."""

from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, field_validator


class ContactDetails(BaseModel):
    """Contact information - ESS editable"""
    mobile_primary: Optional[str] = None
    mobile_alternate: Optional[str] = None
    email_personal: Optional[str] = None
    email_official: Optional[str] = None

    # Current Address (ESS editable)
    address: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None

    # Present Address (can differ from permanent)
    present_address: Optional[str] = None
    present_city: Optional[str] = None
    present_district: Optional[str] = None
    present_state: Optional[str] = None
    present_pincode: Optional[str] = None

    # Emergency Contact
    emergency_name: Optional[str] = None
    emergency_phone: Optional[str] = None
    emergency_relation: Optional[str] = None

    @field_validator('mobile_primary', 'mobile_alternate')
    @classmethod
    def validate_mobile(cls, v):
        if v and not re.match(r'^[6-9]\d{9}$', v):
            raise ValueError('Invalid Indian mobile number')
        return v

    @field_validator('pincode')
    @classmethod
    def validate_pincode(cls, v):
        if v and not re.match(r'^\d{6}$', v):
            raise ValueError('Invalid pincode')
        return v
