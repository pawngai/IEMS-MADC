from contexts.service_book.records.schemas.service_event_schemas import normalize_service_event_input


def test_normalize_service_event_input_prefers_category_part_mapping_over_stale_input() -> None:
    canonical = normalize_service_event_input(
        {
            "employee_id": "EMP-100",
            "event_type": "PROMOTION",
            "part_code": "IV",
            "payload": {
                "promotion_date": "2026-03-14",
                "to_post": "Senior Clerk",
                "promotion_type": "regular",
                "order_no": "MADC/HR/PROM/2026/004",
                "order_date": "2026-03-14",
            },
        }
    )

    assert canonical.part_code == "IV"
