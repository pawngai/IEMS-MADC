# Compliant Master Data Models
# These are controlled vocabularies - no free-text substitutes allowed

from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import List, Optional

from pydantic import BaseModel, Field

from app_platform.reference_data.contracts.employment_type_master import (
    list_employment_type_master,
)


class EmploymentTypeCode(str, Enum):
    REGULAR = "REG"
    CONTRACTUAL = "CON"
    ADHOC = "ADH"
    CASUAL = "CAS"
    OUTSOURCED = "OUT"
    DEPUTATION = "DEP"
    REEMPLOYMENT = "REE"


class EmploymentTypeRules(BaseModel):
    has_service_book: bool = True
    has_pension: bool = True
    has_gpf: bool = True
    has_leave_account: bool = True
    has_increment: bool = True
    can_be_promoted: bool = True
    can_be_transferred: bool = True
    service_book_parts: List[str] = ["I", "II-A", "II-B", "III", "IV", "V", "VI", "VII", "VIII"]


EMPLOYMENT_TYPE_RULES = {
    EmploymentTypeCode.REGULAR: EmploymentTypeRules(
        has_service_book=True,
        has_pension=True,
        has_gpf=True,
        has_leave_account=True,
        has_increment=True,
        can_be_promoted=True,
        can_be_transferred=True,
        service_book_parts=["I", "II-A", "II-B", "III", "IV", "V", "VI", "VII", "VIII"],
    ),
    EmploymentTypeCode.CONTRACTUAL: EmploymentTypeRules(
        has_service_book=False,
        has_pension=False,
        has_gpf=False,
        has_leave_account=True,
        has_increment=False,
        can_be_promoted=False,
        can_be_transferred=False,
        service_book_parts=[],
    ),
    EmploymentTypeCode.ADHOC: EmploymentTypeRules(
        has_service_book=False,
        has_pension=False,
        has_gpf=False,
        has_leave_account=True,
        has_increment=False,
        can_be_promoted=False,
        can_be_transferred=True,
        service_book_parts=[],
    ),
    EmploymentTypeCode.CASUAL: EmploymentTypeRules(
        has_service_book=False,
        has_pension=False,
        has_gpf=False,
        has_leave_account=False,
        has_increment=False,
        can_be_promoted=False,
        can_be_transferred=False,
        service_book_parts=[],
    ),
    EmploymentTypeCode.OUTSOURCED: EmploymentTypeRules(
        has_service_book=False,
        has_pension=False,
        has_gpf=False,
        has_leave_account=False,
        has_increment=False,
        can_be_promoted=False,
        can_be_transferred=False,
        service_book_parts=[],
    ),
    EmploymentTypeCode.DEPUTATION: EmploymentTypeRules(
        has_service_book=False,
        has_pension=True,
        has_gpf=True,
        has_leave_account=True,
        has_increment=True,
        can_be_promoted=False,
        can_be_transferred=False,
        service_book_parts=[],
    ),
    EmploymentTypeCode.REEMPLOYMENT: EmploymentTypeRules(
        has_service_book=False,
        has_pension=False,
        has_gpf=False,
        has_leave_account=True,
        has_increment=False,
        can_be_promoted=False,
        can_be_transferred=True,
        service_book_parts=[],
    ),
}


class MasterBase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    description: str
    is_active: bool = True
    effective_from: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    effective_to: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DepartmentMaster(MasterBase):
    parent_department_code: Optional[str] = None


class DesignationMaster(MasterBase):
    pay_level_code: str
    service_group_code: str
    is_gazetted: bool = False
    is_supervisory: bool = False


class PayLevelMaster(MasterBase):
    pay_band: str
    grade_pay: Optional[int] = None
    basic_min: int
    basic_max: int
    annual_increment_rate: float = 3.0


class ServiceGroupMaster(MasterBase):
    group_code: str
    is_gazetted: bool = False


class CasteCategoryMaster(MasterBase):
    category_code: str
    reservation_percentage: float = 0.0


class EmploymentTypeMaster(MasterBase):
    type_code: str
    rules: dict = {}


class StateMaster(MasterBase):
    state_code: str
    is_ut: bool = False


class DistrictMaster(MasterBase):
    state_code: str
    district_code: str


class QualificationMaster(MasterBase):
    level: str
    discipline: Optional[str] = None


class LeaveTypeMaster(MasterBase):
    leave_code: str
    max_days_per_year: Optional[int] = None
    is_encashable: bool = False
    is_accumulative: bool = False
    applicable_employment_types: List[str] = []


class ServiceEventTypeMaster(MasterBase):
    event_code: str
    service_book_part: str
    requires_order_number: bool = True
    affects_pay: bool = False
    affects_posting: bool = False


DEFAULT_SERVICE_EVENT_TYPES = [
    {"code": "APPT", "description": "Initial Appointment", "event_code": "APPOINTMENT", "service_book_part": "II-A", "requires_order_number": True, "affects_pay": True, "affects_posting": True},
    {"code": "CONF", "description": "Confirmation in Service", "event_code": "CONFIRMATION", "service_book_part": "II-A", "requires_order_number": True, "affects_pay": False, "affects_posting": False},
    {"code": "PROM", "description": "Promotion", "event_code": "PROMOTION", "service_book_part": "II-A", "requires_order_number": True, "affects_pay": True, "affects_posting": True},
    {"code": "TRAN", "description": "Transfer", "event_code": "TRANSFER", "service_book_part": "II-A", "requires_order_number": True, "affects_pay": False, "affects_posting": True},
    {"code": "PAYF", "description": "Pay Fixation", "event_code": "PAY_FIXATION", "service_book_part": "II-B", "requires_order_number": True, "affects_pay": True, "affects_posting": False},
    {"code": "INCR", "description": "Annual Increment", "event_code": "INCREMENT", "service_book_part": "II-B", "requires_order_number": False, "affects_pay": True, "affects_posting": False},
    {"code": "LVGR", "description": "Leave Grant", "event_code": "LEAVE_GRANT", "service_book_part": "III", "requires_order_number": True, "affects_pay": False, "affects_posting": False},
    {"code": "SUSP", "description": "Suspension", "event_code": "SUSPENSION", "service_book_part": "IV", "requires_order_number": True, "affects_pay": True, "affects_posting": False},
    {"code": "REIN", "description": "Reinstatement", "event_code": "REINSTATEMENT", "service_book_part": "IV", "requires_order_number": True, "affects_pay": True, "affects_posting": False},
    {"code": "PNLT", "description": "Penalty", "event_code": "PENALTY", "service_book_part": "IV", "requires_order_number": True, "affects_pay": True, "affects_posting": False},
    {"code": "RETI", "description": "Retirement", "event_code": "RETIREMENT", "service_book_part": "V", "requires_order_number": True, "affects_pay": True, "affects_posting": True},
    {"code": "RESG", "description": "Resignation", "event_code": "RESIGNATION", "service_book_part": "V", "requires_order_number": True, "affects_pay": True, "affects_posting": True},
    {"code": "TERM", "description": "Termination", "event_code": "TERMINATION", "service_book_part": "V", "requires_order_number": True, "affects_pay": True, "affects_posting": True},
    {"code": "DEPT", "description": "Deputation", "event_code": "DEPUTATION", "service_book_part": "II-A", "requires_order_number": True, "affects_pay": True, "affects_posting": True},
    {"code": "REVR", "description": "Reversion", "event_code": "REVERSION", "service_book_part": "II-A", "requires_order_number": True, "affects_pay": True, "affects_posting": True},
    {"code": "FINU", "description": "Financial Upgradation", "event_code": "FINANCIAL_UPGRADATION", "service_book_part": "II-B", "requires_order_number": True, "affects_pay": True, "affects_posting": False},
    {"code": "CPFX", "description": "CPC Pay Fixation", "event_code": "CPC_PAY_FIXATION", "service_book_part": "II-B", "requires_order_number": True, "affects_pay": True, "affects_posting": False},
]

DEFAULT_LEAVE_TYPES = [
    {"code": "CL", "description": "Casual Leave", "leave_code": "CL", "max_days_per_year": 8, "max_days_per_spell": 5, "is_encashable": False, "is_accumulative": False, "applicable_employment_types": ["REG", "CON", "ADH", "DEP", "REE"]},
    {"code": "EL", "description": "Earned Leave", "leave_code": "EL", "max_days_per_year": 30, "is_encashable": True, "is_accumulative": True, "applicable_employment_types": ["REG", "DEP"]},
    {"code": "HPL", "description": "Half Pay Leave", "leave_code": "HPL", "max_days_per_year": 20, "is_encashable": False, "is_accumulative": True, "applicable_employment_types": ["REG", "DEP"]},
    {"code": "CML", "description": "Commuted Leave", "leave_code": "CML", "max_days_per_year": None, "is_encashable": False, "is_accumulative": False, "applicable_employment_types": ["REG", "DEP"]},
    {"code": "LND", "description": "Leave Not Due", "leave_code": "LND", "max_days_per_year": None, "is_encashable": False, "is_accumulative": False, "applicable_employment_types": ["REG", "DEP"]},
    {"code": "CCL", "description": "Child Care Leave", "leave_code": "CCL", "max_days_per_year": 730, "min_days_per_spell": 5, "max_days_lifetime": 730, "is_encashable": False, "is_accumulative": False, "applicable_employment_types": ["REG", "DEP"]},
    {"code": "ML", "description": "Maternity Leave", "leave_code": "ML", "max_days_per_year": 180, "max_days_per_spell": 180, "is_encashable": False, "is_accumulative": False, "applicable_employment_types": ["REG", "CON", "DEP"]},
    {"code": "PL", "description": "Paternity Leave", "leave_code": "PL", "max_days_per_year": 15, "max_days_per_spell": 15, "is_encashable": False, "is_accumulative": False, "applicable_employment_types": ["REG", "DEP"]},
    {"code": "SCL", "description": "Special Casual Leave", "leave_code": "SCL", "max_days_per_year": 14, "is_encashable": False, "is_accumulative": False, "applicable_employment_types": ["REG", "CON", "ADH", "DEP"]},
]

DEFAULT_PAY_LEVELS = [
    {"code": "L1", "description": "Level 1", "pay_band": "PB-1", "basic_min": 17400, "basic_max": 55100},
    {"code": "L1A", "description": "Level 1A", "pay_band": "PB-1", "basic_min": 18000, "basic_max": 56900},
    {"code": "L2", "description": "Level 2", "pay_band": "PB-1", "basic_min": 19900, "basic_max": 63200},
    {"code": "L3", "description": "Level 3", "pay_band": "PB-1", "basic_min": 21700, "basic_max": 69100},
    {"code": "L4", "description": "Level 4", "pay_band": "PB-1", "basic_min": 25500, "basic_max": 81100},
    {"code": "L5", "description": "Level 5", "pay_band": "PB-1", "basic_min": 29200, "basic_max": 92300},
    {"code": "L6", "description": "Level 6", "pay_band": "PB-2", "basic_min": 35400, "basic_max": 112400},
    {"code": "L7", "description": "Level 7", "pay_band": "PB-2", "basic_min": 39100, "basic_max": 123700},
    {"code": "L8", "description": "Level 8", "pay_band": "PB-2", "basic_min": 44900, "basic_max": 142400},
    {"code": "L9", "description": "Level 9", "pay_band": "PB-2", "basic_min": 47600, "basic_max": 151100},
    {"code": "L10", "description": "Level 10", "pay_band": "PB-3", "basic_min": 56100, "basic_max": 177500},
    {"code": "L10A", "description": "Level 10A", "pay_band": "PB-3", "basic_min": 64700, "basic_max": 204900},
    {"code": "L11", "description": "Level 11", "pay_band": "PB-3", "basic_min": 67700, "basic_max": 215000},
    {"code": "L11A", "description": "Level 11A", "pay_band": "PB-3", "basic_min": 75100, "basic_max": 237700},
    {"code": "L12", "description": "Level 12", "pay_band": "PB-3", "basic_min": 78800, "basic_max": 250000},
    {"code": "L13", "description": "Level 13", "pay_band": "PB-4", "basic_min": 123100, "basic_max": 390100},
    {"code": "L13A", "description": "Level 13A", "pay_band": "PB-4", "basic_min": 131100, "basic_max": 414900},
    {"code": "L14", "description": "Level 14", "pay_band": "PB-4", "basic_min": 140200, "basic_max": 444400},
]

DEFAULT_SERVICE_GROUPS = [
    {"code": "GRP-A", "description": "Group A - Gazetted", "group_code": "A", "is_gazetted": True},
    {"code": "GRP-B-G", "description": "Group B - Gazetted", "group_code": "B", "is_gazetted": True},
    {"code": "GRP-B-NG", "description": "Group B - Non-Gazetted", "group_code": "B", "is_gazetted": False},
    {"code": "GRP-C", "description": "Group C", "group_code": "C", "is_gazetted": False},
    {"code": "GRP-D", "description": "Group D", "group_code": "D", "is_gazetted": False},
]

DEFAULT_SERVICES = [
    {"code": "MINISTERIAL", "description": "Ministerial Service"},
    {"code": "ENGINEERING", "description": "Engineering Service"},
    {"code": "GENERAL", "description": "General Service"},
]

DEFAULT_CASTE_CATEGORIES = [
    {"code": "GEN", "description": "General", "category_code": "GEN", "reservation_percentage": 0},
    {"code": "SC", "description": "Scheduled Caste", "category_code": "SC", "reservation_percentage": 15},
    {"code": "ST", "description": "Scheduled Tribe", "category_code": "ST", "reservation_percentage": 7.5},
    {"code": "OBC", "description": "Other Backward Class", "category_code": "OBC", "reservation_percentage": 27},
    {"code": "EWS", "description": "Economically Weaker Section", "category_code": "EWS", "reservation_percentage": 10},
]

DEFAULT_EMPLOYMENT_TYPES = [
    {
        "code": record["employment_type_code"],
        "description": record["name"],
        "type_code": record["employment_type_code"],
        "rules": {
            "has_service_book": record["eligible_for_service_book"],
            "has_pension": record["eligible_for_pension"],
            "has_gpf": record["eligible_for_gpf"],
            "has_leave_account": record["eligible_for_leave_account"],
            "has_increment": record["eligible_for_macp"],
            "can_be_promoted": record["eligible_for_seniority"],
            "can_be_transferred": record["employment_class"] == "REGULAR",
            "service_book_parts": ["I", "II-A", "II-B", "III", "IV", "V", "VI", "VII", "VIII"]
            if record["eligible_for_service_book"]
            else [],
        },
        **record,
    }
    for record in list_employment_type_master()
]
