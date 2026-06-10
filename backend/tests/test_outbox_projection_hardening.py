"""Tests for outbox-driven projection hardening.

Covers:
- Outbox-only publishing enforcement (no direct event_bus.publish in contexts)
- Idempotent projection on duplicate dispatch
- Replay mechanism
- Rebuild entrypoints
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from app_platform.event_bus.bus import EventBus
from app_platform.event_bus.types import BaseEvent, EventName
from app_platform.outbox.dispatcher import OutboxDispatcher
from contexts.service_book.read_side.application.subscribers import (
    register_service_book_subscribers,
)


BACKEND_ROOT = Path(__file__).resolve().parents[1]
CONTEXTS_ROOT = BACKEND_ROOT / "contexts"


# ---------------------------------------------------------------------------
# 1. Enforcement: contexts must not call event_bus.publish() directly
# ---------------------------------------------------------------------------


def test_contexts_never_call_event_bus_publish_directly() -> None:
    """No context module should import and call event_bus.publish().

    All event emission must go through OutboxRepository.add_event().
    Subscriber files (which *receive* events from the bus) are exempt.
    """
    violations: list[str] = []
    subscriber_pattern = re.compile(r"subscriber|_on_event|_dispatch|register_.*_subscribers")

    for py_file in CONTEXTS_ROOT.rglob("*.py"):
        if py_file.name.startswith("__"):
            continue
        source = py_file.read_text(encoding="utf-8", errors="replace")
        # Skip subscriber registration files — they subscribe, not publish
        if subscriber_pattern.search(source) and "event_bus.subscribe(" in source:
            continue
        if "event_bus.publish(" in source:
            rel = py_file.relative_to(BACKEND_ROOT).as_posix()
            violations.append(rel)

    assert not violations, (
        "Context modules must not call event_bus.publish() directly.\n"
        "Use OutboxRepository.add_event() instead:\n"
        + "\n".join(sorted(violations))
    )


# ---------------------------------------------------------------------------
# 2. Idempotent service_book projection on duplicate dispatch
# ---------------------------------------------------------------------------


class _FakeCollection:
    """Minimal Motor-like collection stub supporting insert_one, update_one, find."""

    def __init__(self) -> None:
        self.items: list[dict] = []

    async def insert_one(self, document: dict):
        self.items.append(dict(document))

    async def update_one(self, query: dict, update: dict, upsert: bool = False):
        existing = None
        for row in self.items:
            if all(row.get(k) == v for k, v in query.items()):
                existing = row
                break
        if existing is None and upsert:
            set_on_insert = (update or {}).get("$setOnInsert") or {}
            set_fields = (update or {}).get("$set") or {}
            row = {**query, **set_on_insert, **set_fields}
            self.items.append(row)
        elif existing is not None:
            existing.update((update or {}).get("$set") or {})

    async def delete_many(self, query: dict):
        self.items = [
            item for item in self.items
            if not all(item.get(k) == v for k, v in query.items())
        ]

    def find(self, query: dict, _projection: dict | None = None):
        rows = [
            dict(item)
            for item in self.items
            if all(item.get(key) == value for key, value in query.items())
        ]

        class _Cursor:
            def __init__(self, payload):
                self._payload = payload

            def sort(self, *_args, **_kwargs):
                return self

            async def to_list(self, length: int):
                return self._payload[:length]

        return _Cursor(rows)


class _FakeDb:
    def __init__(self) -> None:
        self.service_book_entries = _FakeCollection()
        self.service_book_part_projections = _FakeCollection()
        # leave_ledger_entries needed by part_vi projection helper
        self.leave_ledger_entries = _FakeCollection()


class _FakeOutboxRepo:
    def __init__(self, docs: list[dict]) -> None:
        self._docs = list(docs)
        self.sent_ids: list[str] = []
        self._sent_docs: list[dict] = list(docs)

    async def get_pending(self, batch_size: int = 100, **_kwargs) -> list[dict]:
        return self._docs[:batch_size]

    async def lock_for_processing(self, event_id: str, ttl_seconds: int = 30) -> bool:
        return True

    async def mark_sent(self, event_id: str) -> None:
        self.sent_ids.append(event_id)

    async def mark_failed(self, event_id: str, err: str, **_kwargs) -> None:
        raise AssertionError(f"Unexpected failure: {event_id} {err}")

    async def get_sent(self, *, event_names: list[str] | None = None, batch_size: int = 500) -> list[dict]:
        if event_names:
            return [d for d in self._sent_docs if d.get("name") in event_names][:batch_size]
        return self._sent_docs[:batch_size]


def _make_service_event_doc(event_id: str = "evt-idem-1") -> dict:
    return {
        "_id": event_id,
        "name": EventName.SERVICE_EVENT_APPROVED.value,
        "payload": {
            "event_version": 1,
            "service_event_id": "SE-100",
            "employee_id": "EMP-100",
            "event_type": "PROMOTION",
            "part_code": "IV",
            "status": "APPROVED",
            "effective_date": "2026-03-01",
            "payload": {"to_post": "Senior Clerk"},
        },
        "actor_id": "actor-1",
        "department_id": "EST",
        "occurred_at": "2026-03-04T10:00:00+00:00",
    }


@pytest.mark.asyncio
async def test_duplicate_dispatch_does_not_create_duplicate_entries() -> None:
    """Dispatching the same outbox event twice must not duplicate service_book_entries."""
    db = _FakeDb()
    bus = EventBus()
    register_service_book_subscribers(event_bus=bus, db_provider=lambda: db)

    doc = _make_service_event_doc("evt-dup-1")
    repo = _FakeOutboxRepo([doc])
    dispatcher = OutboxDispatcher(outbox_repo=repo, event_bus=bus)

    # Dispatch same event twice
    await dispatcher._drain_once()
    await dispatcher._drain_once()

    # Should have exactly 1 entry (idempotent via source_event_id)
    assert len(db.service_book_entries.items) == 1
    entry = db.service_book_entries.items[0]
    assert entry["employee_id"] == "EMP-100"
    assert entry["source_event_id"] == "evt-dup-1"


# ---------------------------------------------------------------------------
# 3. Replay mechanism
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_replay_sent_re_dispatches_events() -> None:
    """replay_sent() should re-publish already-sent outbox events."""
    db = _FakeDb()
    bus = EventBus()
    register_service_book_subscribers(event_bus=bus, db_provider=lambda: db)

    doc = _make_service_event_doc("evt-replay-1")
    repo = _FakeOutboxRepo([doc])
    dispatcher = OutboxDispatcher(outbox_repo=repo, event_bus=bus)

    # First normal dispatch
    await dispatcher._drain_once()
    assert len(db.service_book_entries.items) == 1

    # Replay — should not create duplicates
    replayed = await dispatcher.replay_sent()
    assert replayed == 1
    assert len(db.service_book_entries.items) == 1  # Idempotent


@pytest.mark.asyncio
async def test_replay_sent_filters_by_event_name() -> None:
    """replay_sent(event_names=[...]) should only replay matching events."""
    db = _FakeDb()
    bus = EventBus()
    register_service_book_subscribers(event_bus=bus, db_provider=lambda: db)

    doc = _make_service_event_doc("evt-filter-1")
    repo = _FakeOutboxRepo([doc])
    dispatcher = OutboxDispatcher(outbox_repo=repo, event_bus=bus)

    # Replay with non-matching filter
    replayed = await dispatcher.replay_sent(event_names=["NonExistentEvent"])
    assert replayed == 0
    assert len(db.service_book_entries.items) == 0


# ---------------------------------------------------------------------------
# 4. Rebuild entrypoint: employee_profile read model
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_employee_profile_rebuild_from_identity() -> None:
    """rebuild_projection_from_identity should project every canonical identity."""
    from contexts.employee_profile.read_model.application.service import (
        EmployeeProfileReadModelService,
    )
    from contexts.employee_profile.read_model.infrastructure.repository import (
        EmployeeProfileReadModelRepository,
    )

    class _FakeIdentityCursor:
        def __init__(self, docs):
            self._docs = docs
            self._idx = 0

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self._idx >= len(self._docs):
                raise StopAsyncIteration
            doc = self._docs[self._idx]
            self._idx += 1
            return doc

    class _FakeProfileCollection:
        def __init__(self):
            self.items: list[dict] = []

        async def update_one(self, query, update, upsert=False):
            existing = None
            for row in self.items:
                if row.get("employee_id") == query.get("employee_id"):
                    existing = row
                    break
            if existing is None and upsert:
                set_on_insert = (update or {}).get("$setOnInsert") or {}
                set_fields = (update or {}).get("$set") or {}
                row = {**query, **set_on_insert, **set_fields}
                self.items.append(row)
            elif existing is not None:
                existing.update((update or {}).get("$set") or {})

        async def find_one(self, query, projection=None):
            for row in self.items:
                if all(row.get(k) == v for k, v in query.items()):
                    return dict(row)
            return None

    class _FakeRebuildDb:
        def __init__(self):
            self.employee_profile_read_models = _FakeProfileCollection()
            self.employee_identities = None  # set below

    identities = [
        {
            "employee_id": "EMP-1",
            "full_name": "Alice",
            "employee_status": "ACTIVE",
            "workflow_status": "ACTIVE",
        },
        {"employee_id": "EMP-2", "full_name": "Bob", "employee_status": "ACTIVE"},
        {
            "employee_id": "EMP-IDENTITY-DRAFT",
            "full_name": "Draft Identity",
            "employee_status": "ACTIVE",
            "workflow_status": "DRAFT",
        },
        {
            "employee_id": "EMP-IDENTITY-SUBMITTED",
            "full_name": "Submitted Identity",
            "employee_status": "ACTIVE",
            "workflow_status": "SUBMITTED",
        },
    ]

    db = _FakeRebuildDb()
    db.employee_identities = type("_FakeIdentities", (), {
        "find": lambda self, query, projection=None: _FakeIdentityCursor(identities),
    })()

    repo = EmployeeProfileReadModelRepository(db=db)
    service = EmployeeProfileReadModelService(repo=repo)

    rebuilt = await service.rebuild_projection_from_identity(db=db)

    assert rebuilt == 4
    assert len(db.employee_profile_read_models.items) == 4
    ids = {item["employee_id"] for item in db.employee_profile_read_models.items}
    assert ids == {"EMP-1", "EMP-2", "EMP-IDENTITY-DRAFT", "EMP-IDENTITY-SUBMITTED"}
    assert {item["workflow_status"] for item in db.employee_profile_read_models.items} == {"DRAFT"}
    identity_workflow_by_id = {
        item["employee_id"]: item.get("identity_workflow_status")
        for item in db.employee_profile_read_models.items
    }
    assert identity_workflow_by_id["EMP-1"] == "ACTIVE"
    assert identity_workflow_by_id["EMP-IDENTITY-DRAFT"] == "DRAFT"
    assert identity_workflow_by_id["EMP-IDENTITY-SUBMITTED"] == "SUBMITTED"


# ---------------------------------------------------------------------------
# 5. Rebuild entrypoint: service_book projection must not expose hard deletes
# ---------------------------------------------------------------------------


def test_service_book_repository_has_no_employee_projection_drop_api() -> None:
    from contexts.service_book.repository.read_repository import ServiceBookReadRepository

    assert not hasattr(ServiceBookReadRepository, "drop_employee_projection")


# ---------------------------------------------------------------------------
# 6. AST enforcement: projectors accept source_event_id
# ---------------------------------------------------------------------------


def test_projectors_accept_source_event_id_parameter() -> None:
    """All service_book projectors must accept source_event_id for idempotency."""
    projectors_dir = (
        BACKEND_ROOT / "contexts" / "service_book" / "read_side" / "application" / "projectors"
    )
    violations: list[str] = []
    for py_file in projectors_dir.glob("project_*.py"):
        source = py_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name.startswith("project_"):
                arg_names = [arg.arg for arg in node.args.args + node.args.kwonlyargs]
                if "source_event_id" not in arg_names:
                    rel = py_file.relative_to(BACKEND_ROOT).as_posix()
                    violations.append(f"{rel}:{node.name}")

    assert not violations, (
        "Projectors must accept source_event_id for idempotent replay:\n"
        + "\n".join(sorted(violations))
    )


# ---------------------------------------------------------------------------
# 7. append_entry idempotency AST check
# ---------------------------------------------------------------------------


def test_append_entry_uses_idempotent_upsert() -> None:
    """append_entry must use $setOnInsert upsert (not plain insert_one) when source_event_id is present."""
    read_repo_path = (
        BACKEND_ROOT / "contexts" / "service_book" / "repository" / "read_repository.py"
    )
    entry_repo_path = (
        BACKEND_ROOT / "contexts" / "service_book" / "repository" / "mongo_entry_repository.py"
    )
    read_repo_source = read_repo_path.read_text(encoding="utf-8")
    entry_repo_source = entry_repo_path.read_text(encoding="utf-8")
    assert "source_event_id" in read_repo_source, "append_entry must accept source_event_id parameter"
    assert "source_event_id=source_event_id" in read_repo_source, "append_entry must pass source_event_id through"
    assert "$setOnInsert" in entry_repo_source, "append_entry must use $setOnInsert for idempotent upsert"


# ---------------------------------------------------------------------------
# 8. OutboxDispatcher has replay_sent method
# ---------------------------------------------------------------------------


def test_outbox_dispatcher_has_replay_sent() -> None:
    """OutboxDispatcher must expose replay_sent for controlled replay."""
    assert hasattr(OutboxDispatcher, "replay_sent"), "OutboxDispatcher must have replay_sent method"
    import inspect
    sig = inspect.signature(OutboxDispatcher.replay_sent)
    assert "event_names" in sig.parameters, "replay_sent must accept event_names filter"


# ---------------------------------------------------------------------------
# 9. OutboxRepository has get_sent method
# ---------------------------------------------------------------------------


def test_outbox_repo_has_get_sent() -> None:
    """OutboxRepository must expose get_sent for replay support."""
    from app_platform.outbox.repo import OutboxRepository
    assert hasattr(OutboxRepository, "get_sent"), "OutboxRepository must have get_sent method"
    import inspect
    sig = inspect.signature(OutboxRepository.get_sent)
    assert "event_names" in sig.parameters, "get_sent must accept event_names filter"


def test_service_event_approval_emits_single_lifecycle_event() -> None:
    """Approval should not emit overlapping custom and lifecycle approved events."""
    handler_path = (
        BACKEND_ROOT
        / "contexts"
        / "service_book"
        / "records"
        / "application"
        / "handlers"
        / "approve_event_handler.py"
    )
    source = handler_path.read_text(encoding="utf-8")
    assert 'name="ServiceEventApproved"' not in source
    assert "EventName.SERVICE_EVENT_APPROVED.value" in source
