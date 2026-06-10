__all__ = [
    "ServiceBookReadRepository",
]


def __getattr__(name: str):
    if name == "ServiceBookReadRepository":
        from contexts.service_book.repository.read_repository import (
            ServiceBookReadRepository,
        )

        return ServiceBookReadRepository
    raise AttributeError(name)
