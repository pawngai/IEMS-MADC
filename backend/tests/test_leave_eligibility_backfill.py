from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.leave.domain.eligibility_backfill import build_leave_eligibility_backfill_update


def test_legacy_leave_eligibility_backfill_marks_simple_leave_as_review_free() -> None:
    update = build_leave_eligibility_backfill_update({"leave_type_code": "EL"})

    assert update == {
        "$set": {
            "eligibility_context_version": 1,
            "eligibility_review_required": False,
            "eligibility_review_reasons": [],
        }
    }


def test_legacy_leave_eligibility_backfill_flags_special_leave_missing_context() -> None:
    update = build_leave_eligibility_backfill_update({"leave_type_code": "PL"})

    assert update == {
        "$set": {
            "eligibility_context_version": 1,
            "eligibility_review_required": True,
            "eligibility_review_reasons": ["missing_paternity_event_date"],
        }
    }


def test_legacy_leave_eligibility_backfill_accepts_existing_special_context() -> None:
    update = build_leave_eligibility_backfill_update(
        {
            "leave_type_code": "CCL",
            "child_date_of_birth": "2018-01-01",
        }
    )

    assert update["$set"]["eligibility_review_required"] is False
    assert update["$set"]["eligibility_review_reasons"] == []