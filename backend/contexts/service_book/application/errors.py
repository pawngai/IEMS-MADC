from __future__ import annotations

from typing import Any


class ServiceBookApplicationError(Exception):
    def __init__(self, *, status_code: int, detail: Any) -> None:
        super().__init__(str(detail))
        self.status_code = status_code
        self.detail = detail


def not_found(detail: Any) -> ServiceBookApplicationError:
    return ServiceBookApplicationError(status_code=404, detail=detail)


def conflict(detail: Any) -> ServiceBookApplicationError:
    return ServiceBookApplicationError(status_code=409, detail=detail)


def validation_error(detail: Any) -> ServiceBookApplicationError:
    return ServiceBookApplicationError(status_code=422, detail=detail)


def forbidden(detail: Any) -> ServiceBookApplicationError:
    return ServiceBookApplicationError(status_code=403, detail=detail)
