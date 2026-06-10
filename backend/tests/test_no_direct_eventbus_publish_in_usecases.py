from __future__ import annotations

from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
APPLICATION_ROOT = BACKEND_ROOT / "contexts"


def test_no_direct_event_bus_publish_in_application_usecases() -> None:
    violations: list[str] = []
    for file_path in APPLICATION_ROOT.rglob("application/*.py"):
        rel = file_path.relative_to(BACKEND_ROOT).as_posix()
        if rel.endswith("subscribers.py"):
            continue

        source = file_path.read_text(encoding="utf-8")
        if "event_bus.publish(" in source:
            violations.append(rel)

    assert not violations, (
        "Use-cases must enqueue outbox events instead of directly publishing to event bus:\n"
        + "\n".join(sorted(violations))
    )
