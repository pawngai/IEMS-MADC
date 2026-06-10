from __future__ import annotations

from enum import Enum


class ServiceEventCategory(str, Enum):
    APPOINTMENT = "APPOINTMENT"
    CONFIRMATION = "CONFIRMATION"
    PROMOTION = "PROMOTION"
    TRANSFER = "TRANSFER"
    PAY = "PAY"
    INCREMENT = "INCREMENT"
    DEPUTATION = "DEPUTATION"
    SUSPENSION = "SUSPENSION"
    REINSTATEMENT = "REINSTATEMENT"
    RETIREMENT = "RETIREMENT"
    DISCIPLINARY = "DISCIPLINARY"
    CUSTOM = "CUSTOM"
    GENERIC = "GENERIC"
    FINANCIAL_UPGRADATION = "FINANCIAL_UPGRADATION"
    CPC_PAY_FIXATION = "CPC_PAY_FIXATION"


class PayCommission(str, Enum):
    CPC_4 = "4TH_CPC"
    CPC_5 = "5TH_CPC"
    CPC_6 = "6TH_CPC"
    CPC_7 = "7TH_CPC"


CPC_OPTIONS: tuple[dict[str, str], ...] = (
    {"value": "4TH_CPC", "label": "4th CPC (1986)"},
    {"value": "5TH_CPC", "label": "5th CPC (1997)"},
    {"value": "6TH_CPC", "label": "6th CPC (2006)"},
    {"value": "7TH_CPC", "label": "7th CPC (2016)"},
)
