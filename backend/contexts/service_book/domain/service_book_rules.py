"""Service Book domain invariants.

The domain layer is intentionally free of cross-context imports — eligibility
resolution belongs to the application layer, which queries the
``employee_identity`` Published Language. The domain only enforces the
invariant on a resolved boolean.
"""

from __future__ import annotations


SERVICE_BOOK_NOT_APPLICABLE_DETAIL = {
    "error": "Service Book not applicable",
    "message": "Service Book is only maintained for REGULAR employees.",
    "required_employment_type": "REGULAR",
}


class ServiceBookNotApplicableError(ValueError):
    pass


def service_book_not_applicable_error() -> ServiceBookNotApplicableError:
    return ServiceBookNotApplicableError(str(SERVICE_BOOK_NOT_APPLICABLE_DETAIL))


def require_regular_employee_service_book(*, is_eligible: bool) -> bool:
    if not is_eligible:
        raise service_book_not_applicable_error()
    return True
