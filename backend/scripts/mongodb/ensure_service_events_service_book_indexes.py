from __future__ import annotations

import asyncio
import os
import sys

from motor.motor_asyncio import AsyncIOMotorClient

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


async def ensure_indexes() -> None:
    from app_platform.config.settings import settings  # noqa: WPS433

    if not settings.mongo_url:
        raise RuntimeError("MONGO_URL is required")

    client = AsyncIOMotorClient(settings.mongo_url)
    db = client[settings.db_name]

    await db.service_events.create_index(
        [("employee_id", 1)],
        name="idx_service_events_employee_id",
        background=True,
    )
    await db.service_events.create_index(
        [("events.service_event_id", 1)],
        name="idx_service_events_event_id",
        background=True,
        sparse=True,
    )
    await db.service_book_entries.create_index(
        [("employee_id", 1), ("created_at", -1)],
        name="idx_service_book_entries_employee_id_created_at",
        background=True,
    )
    await db.service_book_part_projections.create_index(
        [("employee_id", 1), ("part_code", 1)],
        name="idx_service_book_part_projections_employee_part",
        background=True,
    )

    print("MongoDB indexes ensured for service_events/service_book")
    client.close()


if __name__ == "__main__":
    asyncio.run(ensure_indexes())
