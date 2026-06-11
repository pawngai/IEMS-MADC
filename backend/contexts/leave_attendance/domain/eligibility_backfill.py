from __future__ import annotations

from typing import Any


SPECIAL_ELIGIBILITY_CODES = {"CML", "ML", "PL", "CCL"}


def build_leave_eligibility_backfill_update(record: dict[str, Any]) -> dict[str, Any]:
    leave_type_code = str(record.get("leave_type_code") or "").strip().upper()
    set_fields: dict[str, Any] = {"eligibility_context_version": 1}

    review_reasons: list[str] = []
    if leave_type_code == "CML":
      if record.get("medical_certificate_provided") is None and not record.get("commuted_leave_basis"):
        review_reasons.append("missing_commuted_leave_support")
    elif leave_type_code == "ML":
      if not record.get("expected_delivery_date") and not record.get("childbirth_date"):
        review_reasons.append("missing_maternity_event_date")
    elif leave_type_code == "PL":
      if not record.get("childbirth_date") and not record.get("adoption_date"):
        review_reasons.append("missing_paternity_event_date")
    elif leave_type_code == "CCL":
      if not record.get("child_date_of_birth"):
        review_reasons.append("missing_child_birth_date")

    set_fields["eligibility_review_required"] = bool(review_reasons)
    if review_reasons:
        set_fields["eligibility_review_reasons"] = review_reasons
    else:
        set_fields["eligibility_review_reasons"] = []

    return {"$set": set_fields}