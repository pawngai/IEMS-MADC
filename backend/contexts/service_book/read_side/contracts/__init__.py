__all__ = [
    "ServiceBookFilter",
    "ServiceBookProjectionEvent",
    "ServiceBookServiceEventProjection",
    "build_part_print_view",
    "build_full_print_view",
]


def __getattr__(name: str):
    if name == "ServiceBookFilter":
        from contexts.service_book.read_side.contracts.dto import ServiceBookFilter

        return ServiceBookFilter
    if name in {"ServiceBookProjectionEvent", "ServiceBookServiceEventProjection"}:
        from contexts.service_book.read_side.contracts.events import (
            ServiceBookProjectionEvent,
            ServiceBookServiceEventProjection,
        )

        return {
            "ServiceBookProjectionEvent": ServiceBookProjectionEvent,
            "ServiceBookServiceEventProjection": ServiceBookServiceEventProjection,
        }[name]
    if name in {"build_part_print_view", "build_full_print_view"}:
        from contexts.service_book.read_side.contracts.print_view import (
            build_full_print_view,
            build_part_print_view,
        )

        return {
            "build_part_print_view": build_part_print_view,
            "build_full_print_view": build_full_print_view,
        }[name]
    raise AttributeError(name)


