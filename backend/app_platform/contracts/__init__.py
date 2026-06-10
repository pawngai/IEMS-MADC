"""Platform contracts package.

Business event schemas now live in their owning bounded contexts. The platform
exposes only the registration mechanism and the domain-neutral
``LenientEventPayload`` primitive.
"""

from app_platform.contracts.events.core_events import LenientEventPayload
from app_platform.contracts.registry import (
    canonical_contract_name,
    get_registered_commands,
    get_registered_events,
    get_registered_queries,
    is_event_registered,
    register_command,
    register_event,
    register_query,
    validate_command_payload,
    validate_event_payload,
    validate_query_payload,
)

# Ensure command/query packages are importable for registration by contexts.
from app_platform.contracts.commands import GenericCommandPayload
from app_platform.contracts.queries import GenericQueryPayload

__all__ = [
    "LenientEventPayload",
    "register_event",
    "register_command",
    "register_query",
    "validate_event_payload",
    "validate_command_payload",
    "validate_query_payload",
    "get_registered_events",
    "get_registered_commands",
    "get_registered_queries",
    "is_event_registered",
    "canonical_contract_name",
    "GenericCommandPayload",
    "GenericQueryPayload",
]
