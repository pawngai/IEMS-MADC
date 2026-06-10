from __future__ import annotations

import pytest
from fastapi import HTTPException

from contexts.service_book.records.application.use_cases import (
    classifyServiceEvent,
    routeServiceEventToServiceBook,
    validateServiceEventPayload,
)


def test_classify_service_event_maps_operational_types() -> None:
    assert classifyServiceEvent("appointment")["event_type"].value == "APPOINTMENT"
    assert classifyServiceEvent("promotion")["event_type"].value == "PROMOTION"
    assert classifyServiceEvent("increment")["event_type"].value == "INCREMENT"
    assert classifyServiceEvent("suspension")["event_type"].value == "SUSPENSION"
    assert classifyServiceEvent("transfer")["event_type"].value == "TRANSFER"
    assert classifyServiceEvent("custom")["event_type"].value == "GENERIC"
    assert classifyServiceEvent("cpc_change_fixation")["event_type"].value == "CPC_PAY_FIXATION"


def test_validate_service_event_payload_rejects_empty_payload() -> None:
    with pytest.raises(HTTPException):
        validateServiceEventPayload(
            {
                "employee_id": "EMP-100",
                "event_type": "PROMOTION",
                "payload": {},
            }
        )


def test_route_service_event_to_service_book_only_when_approved() -> None:
    approved_route = routeServiceEventToServiceBook(
        approved_event={"service_event_id": "SE-1", "status": "APPROVED"}
    )
    assert approved_route["routed"] is True
    assert approved_route["service_book_remains_authoritative"] is True

    draft_route = routeServiceEventToServiceBook(
        approved_event={"service_event_id": "SE-2", "status": "DRAFT"}
    )
    assert draft_route["routed"] is False


def test_validate_service_event_payload_enforces_category_required_keys() -> None:
    with pytest.raises(HTTPException):
        validateServiceEventPayload(
            {
                "employee_id": "EMP-100",
                "event_type": "PROMOTION",
                "payload": {
                    "to_post": "Senior Clerk",
                },
            }
        )

    normalized = validateServiceEventPayload(
        {
            "employee_id": "EMP-100",
            "event_type": "PROMOTION",
            "payload": {
                "promotion_date": "2026-03-14",
                "to_post": "Senior Clerk",
                "promotion_type": "regular",
                "order_no": "MADC/HR/PROM/2026/001",
                "order_date": "2026-03-14",
            },
        }
    )
    assert "event_subtype" not in normalized["payload"]


def test_validate_service_event_payload_preserves_custom_category_over_generic_storage() -> None:
    normalized = validateServiceEventPayload(
        {
            "employee_id": "EMP-100",
            "event_type": "CUSTOM",
            "payload": {
                "order_no": "MADC/HR/CUSTOM/2026/001",
                "order_date": "2026-04-09",
                "remarks": "Custom event entry",
            },
        }
    )

    assert normalized["category"] == "CUSTOM"
    assert normalized["event_type"].value == "GENERIC"


def test_validate_service_event_payload_enforces_pay_change_when_affects_pay_true() -> None:
    with pytest.raises(HTTPException):
        validateServiceEventPayload(
            {
                "employee_id": "EMP-100",
                "event_type": "PROMOTION",
                "payload": {
                    "promotion_date": "2026-03-14",
                    "to_post": "Senior Clerk",
                    "promotion_type": "regular",
                    "order_no": "MADC/HR/PROM/2026/002",
                    "order_date": "2026-03-14",
                    "pay_change": {
                        "affects_pay": True,
                        "old_basic": 35400,
                    },
                },
            }
        )


def test_validate_service_event_payload_infers_authoritative_part_code_from_category() -> None:
    normalized = validateServiceEventPayload(
        {
            "employee_id": "EMP-100",
            "event_type": "PROMOTION",
            "part_code": "IV",
            "payload": {
                "promotion_date": "2026-03-14",
                "to_post": "Senior Clerk",
                "promotion_type": "regular",
                "order_no": "MADC/HR/PROM/2026/003",
                "order_date": "2026-03-14",
            },
        }
    )

    assert normalized["part_code"] == "IV"


def test_validate_service_event_payload_preserves_increment_event_type() -> None:
    normalized = validateServiceEventPayload(
        {
            "employee_id": "EMP-100",
            "event_type": "INCREMENT",
            "payload": {
                "increment_date": "2026-03-14",
                "increment_type": "annual",
                "order_no": "MADC/FIN/INCR/2026/001",
                "order_date": "2026-03-14",
                "cpc": "7TH_CPC",
                "pay_level": "Level 4",
                "pay_cell_index": 5,
                "from_basic_pay": 25500,
                "to_basic_pay": 26300,
            },
        }
    )

    assert normalized["event_type"].value == "INCREMENT"


def test_validate_service_event_payload_normalizes_cpc_change_fixation_contract() -> None:
    normalized = validateServiceEventPayload(
        {
            "employee_id": "EMP-100",
            "event_type": "CPC_CHANGE_FIXATION",
            "effective_date": "2026-04-01",
            "order_no": "MADC/FIN/CPC/2026/001",
            "order_date": "2026-04-02",
            "from_cpc": "6TH_CPC",
            "to_cpc": "7TH_CPC",
            "pre_revised_pay": {
                "basic_pay": "15600",
            },
            "fitment": {
                "pay_level": "Level 6",
                "pay_cell_index": 1,
            },
            "post_revised_pay": {
                "pay_level": "Level 6",
                "pay_cell_index": 1,
                "basic_pay": "35400",
            },
            "option": {},
            "remarks": "Migration test",
        }
    )

    assert normalized["event_type"].value == "CPC_PAY_FIXATION"
    assert normalized["category"] == "CPC_PAY_FIXATION"
    assert normalized["payload"]["from_cpc"] == "6TH_CPC"
    assert normalized["payload"]["to_cpc"] == "7TH_CPC"
    assert normalized["payload"]["post_revised_pay"]["basic_pay"] == "35400"
    assert normalized["effective_from"] == "2026-04-01"
