from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Optional

from app_platform.config.settings import settings
from app_platform.db.migration_runner import run_pending_migrations
from fastapi import FastAPI, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)


class MongoState:
    def __init__(self) -> None:
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Any = None
        self.bootstrap_task: Optional[asyncio.Task[Any]] = None


mongo_state = MongoState()


def _normalize_index_key(key: Any) -> tuple[tuple[str, int], ...]:
    return tuple((str(name), int(direction)) for name, direction in (key or []))


async def _drop_employee_identity_aadhaar_indexes(collection) -> None:
    expected_key = (("aadhaar_number", 1),)
    index_info = await collection.index_information()
    for index_name, metadata in index_info.items():
        if _normalize_index_key(metadata.get("key")) == expected_key:
            await collection.drop_index(index_name)


async def _drop_employee_identity_assignment_indexes(collection) -> None:
    expected_keys = {
        (("current_department_id", 1),),
        (("employment_type", 1),),
    }
    index_info = await collection.index_information()
    for index_name, metadata in index_info.items():
        if _normalize_index_key(metadata.get("key")) in expected_keys:
            await collection.drop_index(index_name)


async def _find_duplicate_employee_codes(collection, *, limit: int = 5) -> list[dict[str, Any]]:
    cursor = collection.aggregate(
        [
            {"$match": {"employee_code": {"$type": "string", "$ne": ""}}},
            {
                "$group": {
                    "_id": "$employee_code",
                    "count": {"$sum": 1},
                    "employee_ids": {"$push": "$employee_id"},
                }
            },
            {"$match": {"count": {"$gt": 1}}},
            {"$sort": {"count": -1, "_id": 1}},
            {"$limit": limit},
        ]
    )
    return [row async for row in cursor]


async def _ensure_employee_code_unique_index(db, *, ascending: int) -> None:
    collection = db.employee_identities
    duplicate_rows = await _find_duplicate_employee_codes(collection)
    if duplicate_rows:
        duplicate_codes = ", ".join(str(row.get("_id")) for row in duplicate_rows)
        raise RuntimeError(
            "Cannot promote employee_code to a unique index because duplicates exist: "
            f"{duplicate_codes}"
        )

    expected_key = (("employee_code", ascending),)
    index_info = await collection.index_information()
    stale_index_names: list[str] = []
    has_unique_index = False

    for index_name, metadata in index_info.items():
        if _normalize_index_key(metadata.get("key")) != expected_key:
            continue
        if metadata.get("unique", False):
            has_unique_index = True
        else:
            stale_index_names.append(index_name)

    for index_name in stale_index_names:
        await collection.drop_index(index_name)

    if has_unique_index and not stale_index_names:
        return

    await collection.create_index(
        [("employee_code", ascending)],
        unique=True,
        background=True,
    )


async def _drop_index_if_exists(collection, index_name: str) -> None:
    index_info = await collection.index_information()
    if index_name in index_info:
        await collection.drop_index(index_name)


async def _drop_index_if_non_partial(collection, *, field: str, collection_name: str) -> None:
    """Drop a unique index on ``field`` if it exists without partialFilterExpression.

    A non-partial unique index on an optional field treats missing values as the
    implicit ``null`` and rejects more than one such document. When the document
    schema has moved on (e.g. ``token`` → ``token_hash``), the old index must be
    rebuilt as a partial index before new writes can succeed.
    """

    index_info = await collection.index_information()
    for name, definition in index_info.items():
        keys = definition.get("key") or []
        if len(keys) != 1:
            continue
        if keys[0][0] != field:
            continue
        if not definition.get("unique"):
            continue
        if "partialFilterExpression" in definition:
            continue
        logger.info(
            "Dropping non-partial unique index on %s.%s (index=%s) so it can be rebuilt as a partial index.",
            collection_name,
            field,
            name,
        )
        await collection.drop_index(name)


async def _find_duplicate_compound_keys(
    collection,
    *,
    fields: list[str],
    partial_field: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    group_id = {field: f"${field}" for field in fields}
    cursor = collection.aggregate(
        [
            {"$match": {partial_field: {"$type": "string"}}},
            {"$group": {"_id": group_id, "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit},
        ]
    )
    return [row async for row in cursor]


async def _quarantine_duplicate_compound_keys(
    collection,
    *,
    db,
    collection_name: str,
    fields: list[str],
    partial_field: str,
) -> None:
    duplicate_rows = await _find_duplicate_compound_keys(
        collection,
        fields=fields,
        partial_field=partial_field,
    )
    if not duplicate_rows:
        return
    quarantine = db.event_duplicate_quarantine
    quarantined_at = datetime.now(timezone.utc).isoformat()
    for row in duplicate_rows:
        key = row.get("_id") or {}
        docs = await collection.find({field: key.get(field) for field in fields}).sort("_id", 1).to_list(length=None)
        duplicate_docs = docs[1:]
        if not duplicate_docs:
            continue
        await quarantine.insert_many(
            [
                {
                    "quarantined_at": quarantined_at,
                    "source_collection": collection_name,
                    "unique_fields": fields,
                    "duplicate_key": key,
                    "document": doc,
                }
                for doc in duplicate_docs
            ]
        )
        await collection.delete_many({"_id": {"$in": [doc["_id"] for doc in duplicate_docs if "_id" in doc]}})
    logger.warning(
        "Quarantined duplicate rows before creating unique index on %s for fields %s.",
        collection_name,
        fields,
    )


async def _ensure_indexes(db) -> None:
    """Create indexes if they don't already exist (idempotent)."""
    from pymongo import ASCENDING, DESCENDING

    # Employee identity/profile
    await db.employee_identities.create_index(
        [("employee_id", ASCENDING)],
        unique=True,
        background=True,
    )
    await _ensure_employee_code_unique_index(db, ascending=ASCENDING)
    await db.employee_identities.create_index(
        [("employee_status", ASCENDING)],
        background=True,
    )
    await _drop_employee_identity_aadhaar_indexes(db.employee_identities)
    await _drop_employee_identity_assignment_indexes(db.employee_identities)
    await db.employee_profile_extensions.create_index(
        [("employee_id", ASCENDING)],
        unique=True,
        background=True,
    )
    await db.employee_profile_extensions.create_index(
        [("workflow_status", ASCENDING)],
        background=True,
    )
    await db.employee_profile_read_models.create_index(
        [("employee_id", ASCENDING)],
        unique=True,
        background=True,
    )
    await db.employee_profile_read_models.create_index(
        [("workflow_status", ASCENDING)],
        background=True,
    )
    await db.employee_profile_read_models.create_index(
        [("current_department_id", ASCENDING)],
        background=True,
    )
    await db.employee_profile_read_models.create_index(
        [("employment_type", ASCENDING)],
        background=True,
    )

    # Users / auth
    await db.users.create_index(
        [("id", ASCENDING)],
        unique=True,
        background=True,
    )
    await db.users.create_index(
        [("employee_id", ASCENDING)],
        background=True,
    )

    # Leave applications
    await db.leave_applications.create_index(
        [("employee_id", ASCENDING), ("status", ASCENDING)],
        background=True,
    )

    # Outbox — dispatch lookup plus idempotency-key dedupe.
    await db.outbox_events.create_index(
        [("status", ASCENDING), ("next_attempt_at", ASCENDING), ("locked_until", ASCENDING)],
        background=True,
    )
    await _quarantine_duplicate_compound_keys(
        db.outbox_events,
        db=db,
        collection_name="outbox_events",
        fields=["name", "event_version", "idempotency_key"],
        partial_field="idempotency_key",
    )
    await db.outbox_events.create_index(
        [("name", ASCENDING), ("event_version", ASCENDING), ("idempotency_key", ASCENDING)],
        unique=True,
        partialFilterExpression={"idempotency_key": {"$type": "string"}},
        background=True,
        name="outbox_idempotency_unique",
    )
    await db.event_duplicate_quarantine.create_index(
        [("source_collection", ASCENDING), ("quarantined_at", DESCENDING)],
        background=True,
    )

    # Audit logs
    await db.audit_logs.create_index(
        [("timestamp", DESCENDING)],
        background=True,
    )
    await db.audit_logs.create_index(
        [("user_id", ASCENDING)],
        background=True,
    )
    await _quarantine_duplicate_compound_keys(
        db.audit_logs,
        db=db,
        collection_name="audit_logs",
        fields=["source_event_id", "action", "resource_type"],
        partial_field="source_event_id",
    )
    await db.audit_logs.create_index(
        [("source_event_id", ASCENDING), ("action", ASCENDING), ("resource_type", ASCENDING)],
        unique=True,
        partialFilterExpression={"source_event_id": {"$type": "string"}},
        background=True,
        name="audit_source_event_unique",
    )

    # Service book parts — employee_id index on each
    from contexts.service_book.contracts.servicebook.part_constants import SB_COLLECTION_LIST

    for coll_name in SB_COLLECTION_LIST:
        await db[coll_name].create_index(
            [("employee_id", ASCENDING)],
            background=True,
        )

    # Service book revisions — append-only history index set
    await db.service_book_part_revisions.create_index(
        [("employee_id", ASCENDING), ("part", ASCENDING), ("sequence", ASCENDING)],
        unique=True,
        background=True,
    )
    await db.service_book_part_revisions.create_index(
        [
            ("employee_id", ASCENDING),
            ("part", ASCENDING),
            ("created_at", DESCENDING),
        ],
        background=True,
    )
    await db.service_book_part_revisions.create_index(
        [("hash", ASCENDING)],
        unique=True,
        background=True,
    )

    # Service Book dynamic engine
    await db.servicebook_schema_definitions.create_index(
        [("schema_key", ASCENDING)],
        unique=True,
        background=True,
    )
    await db.servicebook_schema_versions.create_index(
        [("schema_key", ASCENDING), ("version", ASCENDING)],
        unique=True,
        background=True,
    )
    await db.servicebook_schema_versions.create_index(
        [
            ("schema_key", ASCENDING),
            ("is_published", ASCENDING),
            ("version", DESCENDING),
        ],
        background=True,
    )
    await db.servicebook_entries.create_index(
        [
            ("employee_id", ASCENDING),
            ("schema_key", ASCENDING),
            ("is_active", ASCENDING),
            ("created_at", DESCENDING),
        ],
        background=True,
    )
    await db.servicebook_entries.create_index(
        [
            ("employee_id", ASCENDING),
            ("part_key", ASCENDING),
            ("status", ASCENDING),
            ("is_active", ASCENDING),
        ],
        background=True,
    )
    await db.servicebook_entries.create_index(
        [("workflow_state", ASCENDING), ("department_id", ASCENDING)],
        background=True,
    )
    await db.servicebook_entries.create_index(
        [("id", ASCENDING)],
        unique=True,
        background=True,
    )
    await db.service_book_workflow_entries.create_index(
        [("id", ASCENDING)],
        unique=True,
        background=True,
    )
    await db.service_book_workflow_entries.create_index(
        [
            ("employee_id", ASCENDING),
            ("schema_key", ASCENDING),
            ("is_active", ASCENDING),
            ("created_at", DESCENDING),
        ],
        background=True,
    )
    await db.service_book_workflow_entries.create_index(
        [("workflow_state", ASCENDING), ("updated_at", DESCENDING)],
        background=True,
    )
    await _quarantine_duplicate_compound_keys(
        db.service_book_entries,
        db=db,
        collection_name="service_book_entries",
        fields=["source_event_id", "event_name"],
        partial_field="source_event_id",
    )
    await db.service_book_entries.create_index(
        [("source_event_id", ASCENDING), ("event_name", ASCENDING)],
        unique=True,
        partialFilterExpression={"source_event_id": {"$type": "string"}},
        background=True,
        name="service_book_source_event_unique",
    )
    await db.service_book_projection_status.create_index(
        [("projection_name", ASCENDING)],
        unique=True,
        background=True,
    )
    await db.servicebook_part_views.create_index(
        [("employee_id", ASCENDING), ("part_key", ASCENDING)],
        unique=True,
        background=True,
    )

    # Change requests
    await db.change_requests.create_index(
        [("employee_id", ASCENDING), ("status", ASCENDING)],
        background=True,
    )

    # Service events — normalized event records plus legacy stream projection
    # Service Book records - official append-only entries plus stream metadata.
    await db.service_book_record_streams.create_index(
        [("employee_id", ASCENDING)],
        unique=True,
        background=True,
    )
    await db.service_book_records.create_index(
        [("service_event_id", ASCENDING)],
        unique=True,
        background=True,
    )
    await db.service_book_records.create_index(
        [("employee_id", ASCENDING), ("sequence", ASCENDING)],
        background=True,
    )
    await db.service_book_records.create_index(
        [("employee_id", ASCENDING), ("status", ASCENDING)],
        background=True,
    )
    await db.service_book_records.create_index(
        [("event_type", ASCENDING), ("effective_from", DESCENDING)],
        background=True,
    )
    await db.service_book_records.create_index(
        [("employee_id", ASCENDING), ("event_type", ASCENDING), ("effective_from", DESCENDING)],
        background=True,
    )
    await db.service_book_records.create_index(
        [("recorded_at", DESCENDING)],
        background=True,
    )
    await db.service_book_records.create_index(
        [("correlation_id", ASCENDING)],
        background=True,
        sparse=True,
    )

    # TODO(migration): legacy service_event_* collections remain indexed during
    # the service_book_records cutover so existing data can be copied safely.
    await db.service_event_streams.create_index(
        [("employee_id", ASCENDING)],
        unique=True,
        background=True,
    )
    await db.service_event_records.create_index(
        [("service_event_id", ASCENDING)],
        unique=True,
        background=True,
    )
    await db.service_event_records.create_index(
        [("employee_id", ASCENDING), ("sequence", ASCENDING)],
        background=True,
    )
    await db.service_event_records.create_index(
        [("employee_id", ASCENDING), ("status", ASCENDING)],
        background=True,
    )
    await db.service_event_records.create_index(
        [("event_type", ASCENDING), ("effective_from", DESCENDING)],
        background=True,
    )
    await db.service_event_records.create_index(
        [("employee_id", ASCENDING), ("event_type", ASCENDING), ("effective_from", DESCENDING)],
        background=True,
    )
    await db.service_event_records.create_index(
        [("recorded_at", DESCENDING)],
        background=True,
    )
    await db.service_event_records.create_index(
        [("correlation_id", ASCENDING)],
        background=True,
        sparse=True,
    )

    # Legacy projection retained for reporting compatibility during cutover.
    await db.service_events.create_index(
        [("employee_id", ASCENDING)],
        unique=True,
        background=True,
    )

    # Workflow tasks — unique task_id for fast lookup
    await db.workflow_tasks.create_index(
        [("task_id", ASCENDING)],
        unique=True,
        background=True,
    )
    await db.workflow_tasks.create_index(
        [("subject_type", ASCENDING), ("subject_id", ASCENDING)],
        background=True,
    )

    # Seniority lists — unique list_id
    await db.seniority_lists.create_index(
        [("list_id", ASCENDING)],
        unique=True,
        background=True,
    )

    # Users — unique email index for fast lookups and duplicate prevention
    await db.users.create_index(
        [("email", ASCENDING)],
        unique=True,
        background=True,
    )
    await db.refresh_tokens.create_index(
        [("token_hash", ASCENDING)],
        unique=True,
        background=True,
        partialFilterExpression={"token_hash": {"$type": "string"}},
    )
    await db.refresh_tokens.create_index(
        [("user_id", ASCENDING)],
        background=True,
    )

    # Notifications — employee_id + read for ESS notification queries
    await db.notifications.create_index(
        [("employee_id", ASCENDING), ("read", ASCENDING)],
        background=True,
    )
    await db.notifications.create_index(
        [("timestamp", DESCENDING)],
        background=True,
    )
    await _quarantine_duplicate_compound_keys(
        db.notifications,
        db=db,
        collection_name="notifications",
        fields=["source_event_id", "type", "employee_id"],
        partial_field="source_event_id",
    )
    await db.notifications.create_index(
        [("source_event_id", ASCENDING), ("type", ASCENDING), ("employee_id", ASCENDING)],
        unique=True,
        partialFilterExpression={"source_event_id": {"$type": "string"}},
        background=True,
        name="notification_source_event_unique",
    )

    # Refresh tokens — lookup by token value (legacy documents only) and cleanup by user_id.
    # New refresh tokens persist only `token_hash`. The `token` index must be PARTIAL,
    # otherwise multiple new documents (each with `token` missing) collide on the
    # implicit null value and cause E11000 duplicate-key errors on every login.
    await _drop_index_if_non_partial(
        db.refresh_tokens,
        field="token",
        collection_name="refresh_tokens",
    )
    await db.refresh_tokens.create_index(
        [("token", ASCENDING)],
        unique=True,
        background=True,
        partialFilterExpression={"token": {"$type": "string"}},
        name="refresh_tokens_token_partial_unique",
    )
    await db.refresh_tokens.create_index(
        [("user_id", ASCENDING)],
        background=True,
    )
    # TTL index: auto-expire refresh tokens after 7 days
    await db.refresh_tokens.create_index(
        [("expires_at", ASCENDING)],
        expireAfterSeconds=0,
        background=True,
    )

    # Master data — unique (code, version) index for versioned records
    master_collections = [
        "employment_types",
        "service_event_types",
        "leave_types",
        "pay_levels",
        "service_groups",
        "services",
        "caste_categories",
        "departments",
        "designations",
        "offices",
    ]
    for coll_name in master_collections:
        # Drop legacy unique code-only index if it exists.
        await _drop_index_if_exists(db[coll_name], "code_1")
        await db[coll_name].create_index(
            [("code", ASCENDING), ("version", ASCENDING)],
            unique=True,
            name="code_version_unique",
            background=True,
        )

    logger.info("MongoDB indexes ensured.")


async def _run_post_connect_bootstrap(db) -> None:
    """Run required DB migrations and index setup before API readiness."""
    applied_migrations = await run_pending_migrations(db)
    if applied_migrations:
        logger.info("Applied MongoDB migrations: %s", ", ".join(applied_migrations))
    await _ensure_indexes(db)


async def _require_database_exists(client: AsyncIOMotorClient, db_name: str) -> None:
    database_names = await client.list_database_names()
    if db_name not in database_names:
        raise RuntimeError(f"MongoDB database {db_name!r} does not exist")


async def _log_transaction_support(db) -> None:
    """Report whether the deployment supports multi-document transactions.

    run_atomic silently degrades to sequential non-transactional writes on a
    standalone mongod, so a misconfigured production deployment loses atomicity
    without any other signal.
    """
    try:
        hello = await db.command("hello")
    except Exception as exc:
        logger.warning("Could not determine MongoDB topology: %s", exc)
        return
    set_name = hello.get("setName")
    if set_name:
        logger.info(
            "MongoDB replica set %r detected; multi-document transactions are enabled.",
            set_name,
        )
    elif settings.is_production:
        logger.error(
            "MongoDB is running standalone; multi-document transactions are unavailable "
            "and atomic writes fall back to sequential non-transactional updates. "
            "Run mongod with --replSet and initiate the replica set "
            "(see deploy/gcp/docker-compose.vm.yml)."
        )
    else:
        logger.info(
            "MongoDB is running standalone; transactions disabled (run_atomic falls back)."
        )


async def _connect() -> None:
    if not settings.mongo_url:
        if settings.is_production:
            raise RuntimeError("MONGO_URL is required in production")
        logger.warning("MONGO_URL not set; running with no database connection.")
        mongo_state.client = None
        mongo_state.db = None
        return

    last_error: Exception | None = None
    for attempt in range(1, 6):
        client = AsyncIOMotorClient(settings.mongo_url, serverSelectionTimeoutMS=5000)
        try:
            db = client[settings.db_name]
            # Force initial server selection; retry transient startup races before offline mode.
            await db.command("ping")
            if settings.is_production:
                await _require_database_exists(client, settings.db_name)
            await _log_transaction_support(db)
            await _run_post_connect_bootstrap(db)
            mongo_state.client = client
            mongo_state.db = db
            return
        except Exception as exc:
            client.close()
            if settings.is_production and isinstance(exc, RuntimeError):
                raise
            last_error = exc
            if attempt < 5:
                logger.warning(
                    "MongoDB connection attempt %s/5 failed: %s. Retrying.",
                    attempt,
                    exc,
                )
                await asyncio.sleep(2)

    if settings.is_production:
        raise RuntimeError("MongoDB connection is required in production") from last_error

    logger.warning(f"MongoDB connection warning: {last_error}. Running in offline mode.")
    mongo_state.client = None
    mongo_state.db = None


async def _close() -> None:
    if mongo_state.bootstrap_task is not None and not mongo_state.bootstrap_task.done():
        mongo_state.bootstrap_task.cancel()
        try:
            await mongo_state.bootstrap_task
        except asyncio.CancelledError:
            pass
    mongo_state.bootstrap_task = None

    if mongo_state.client is not None:
        mongo_state.client.close()
    mongo_state.client = None
    mongo_state.db = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await _connect()
    app.state.mongo_client = mongo_state.client
    app.state.db = mongo_state.db
    try:
        yield
    finally:
        await _close()


def get_db(request: Request):
    """
    FastAPI dependency that returns a MongoDB database handle.

    Raises 503 if the app is running in offline mode.
    """

    db = getattr(request.app.state, "db", None)
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    return db


def get_db_optional(request: Request):
    """Like get_db(), but returns None in offline mode (for read-only endpoints)."""

    return getattr(request.app.state, "db", None)
