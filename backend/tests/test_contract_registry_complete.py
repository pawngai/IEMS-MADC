from __future__ import annotations

import app_platform.contracts.events  # noqa: F401
from app_platform.contracts.registry import canonical_contract_name, get_registered_events
from app_platform.event_bus.types import EventName


def test_all_event_names_have_registered_v1_contract() -> None:
    registered = get_registered_events()
    missing: list[str] = []
    for event_name in EventName:
        key = canonical_contract_name(event_name.value, "v1")
        if key not in registered:
            missing.append(key)

    assert not missing, "Missing event contracts:\n" + "\n".join(sorted(missing))


def test_legacy_compat_event_names_are_not_registered() -> None:
    """Legacy custom event names were retired in favour of the canonical
    ``EventName.SERVICE_EVENT_*`` lifecycle names. The registrations must
    not return — they masked the canonical-name migration by validating an
    out-of-band payload schema."""
    registered = get_registered_events()
    forbidden = {
        canonical_contract_name("ServiceEventCreated", "v1"),
        canonical_contract_name("ServiceEventProposed", "v1"),
        canonical_contract_name("ServiceEventApproved", "v1"),
    }
    resurrected = sorted(forbidden & set(registered.keys()))
    assert not resurrected, (
        "Retired legacy event names are registered again. Emit canonical "
        "EventName.SERVICE_EVENT_* names instead:\n" + "\n".join(resurrected)
    )
