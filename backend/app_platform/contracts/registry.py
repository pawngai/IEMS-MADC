from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError


class ContractValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ContractDefinition:
    kind: str
    name: str
    version: str
    schema: type[BaseModel]

    @property
    def key(self) -> str:
        return canonical_contract_name(self.name, self.version)


_EVENT_REGISTRY: dict[str, ContractDefinition] = {}
_COMMAND_REGISTRY: dict[str, ContractDefinition] = {}
_QUERY_REGISTRY: dict[str, ContractDefinition] = {}


def normalize_version(version: str) -> str:
    normalized = str(version or "").strip().lower()
    if not normalized:
        raise ValueError("Contract version is required")
    if not normalized.startswith("v"):
        normalized = f"v{normalized}"
    return normalized


def canonical_contract_name(name: str, version: str) -> str:
    normalized_name = str(name or "").strip()
    if not normalized_name:
        raise ValueError("Contract name is required")
    return f"{normalized_name}.{normalize_version(version)}"


def _register(
    *,
    registry: dict[str, ContractDefinition],
    kind: str,
    name: str,
    version: str,
    schema: type[BaseModel],
) -> ContractDefinition:
    key = canonical_contract_name(name, version)
    definition = ContractDefinition(
        kind=kind,
        name=name,
        version=normalize_version(version),
        schema=schema,
    )
    existing = registry.get(key)
    if existing and existing.schema is not schema:
        raise ValueError(f"{kind} contract already registered for {key}")
    registry[key] = definition
    return definition


def register_event(*, name: str, version: str, schema: type[BaseModel]) -> ContractDefinition:
    return _register(
        registry=_EVENT_REGISTRY,
        kind="event",
        name=name,
        version=version,
        schema=schema,
    )


def register_command(*, name: str, version: str, schema: type[BaseModel]) -> ContractDefinition:
    return _register(
        registry=_COMMAND_REGISTRY,
        kind="command",
        name=name,
        version=version,
        schema=schema,
    )


def register_query(*, name: str, version: str, schema: type[BaseModel]) -> ContractDefinition:
    return _register(
        registry=_QUERY_REGISTRY,
        kind="query",
        name=name,
        version=version,
        schema=schema,
    )


def get_registered_events() -> dict[str, ContractDefinition]:
    return dict(_EVENT_REGISTRY)


def get_registered_commands() -> dict[str, ContractDefinition]:
    return dict(_COMMAND_REGISTRY)


def get_registered_queries() -> dict[str, ContractDefinition]:
    return dict(_QUERY_REGISTRY)


def _resolve(registry: dict[str, ContractDefinition], *, name: str, version: str) -> ContractDefinition:
    key = canonical_contract_name(name, version)
    definition = registry.get(key)
    if definition is None:
        raise ContractValidationError(f"Unregistered contract: {key}")
    return definition


def _validate_payload(definition: ContractDefinition, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        model = definition.schema.model_validate(payload or {})
    except ValidationError as exc:
        raise ContractValidationError(
            f"Invalid {definition.kind} payload for {definition.key}: {exc}"
        ) from exc
    return model.model_dump(mode="json")


def validate_event_payload(*, name: str, version: str, payload: dict[str, Any]) -> dict[str, Any]:
    definition = _resolve(_EVENT_REGISTRY, name=name, version=version)
    return _validate_payload(definition, payload)


def validate_command_payload(*, name: str, version: str, payload: dict[str, Any]) -> dict[str, Any]:
    definition = _resolve(_COMMAND_REGISTRY, name=name, version=version)
    return _validate_payload(definition, payload)


def validate_query_payload(*, name: str, version: str, payload: dict[str, Any]) -> dict[str, Any]:
    definition = _resolve(_QUERY_REGISTRY, name=name, version=version)
    return _validate_payload(definition, payload)


def is_event_registered(*, name: str, version: str = "v1") -> bool:
    return canonical_contract_name(name, version) in _EVENT_REGISTRY
