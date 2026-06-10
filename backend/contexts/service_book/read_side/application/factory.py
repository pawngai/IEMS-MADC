from __future__ import annotations

from contexts.service_book.read_side.application.service import ServiceBookReadService
from contexts.service_book.repository.read_repository import (
    ServiceBookReadRepository,
)


def build_service_book_repository(*, db) -> ServiceBookReadRepository:
    return ServiceBookReadRepository(db=db)


def build_service_book_service(*, db) -> ServiceBookReadService:
    return ServiceBookReadService(repo=build_service_book_repository(db=db), db=db)


