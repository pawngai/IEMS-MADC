from __future__ import annotations

import importlib
import pkgutil
from datetime import datetime, timezone
from types import ModuleType
from typing import Any


MIGRATIONS_PACKAGE = "app_platform.db.migrations"
MIGRATIONS_COLLECTION = "schema_migrations"


def discover_migration_modules() -> list[ModuleType]:
    package = importlib.import_module(MIGRATIONS_PACKAGE)
    package_path = getattr(package, "__path__", None)
    if package_path is None:
        raise RuntimeError(f"Migration package {MIGRATIONS_PACKAGE!r} is not a package")

    modules: list[ModuleType] = []
    for module_info in pkgutil.iter_modules(package_path):
        name = module_info.name
        if not name[:3].isdigit() or name.startswith("__"):
            continue
        modules.append(importlib.import_module(f"{MIGRATIONS_PACKAGE}.{name}"))

    return sorted(modules, key=lambda module: module.__name__.rsplit(".", 1)[-1])


async def run_pending_migrations(db, *, modules: list[ModuleType] | None = None) -> list[str]:
    migrations = modules if modules is not None else discover_migration_modules()
    collection = db[MIGRATIONS_COLLECTION]
    await collection.create_index("migration_id", unique=True, background=True)

    applied_rows = collection.find({}, {"_id": 0, "migration_id": 1})
    applied_ids = {
        str(row.get("migration_id"))
        async for row in applied_rows
        if row.get("migration_id")
    }

    applied_now: list[str] = []
    for module in migrations:
        migration_id = module.__name__.rsplit(".", 1)[-1]
        if migration_id in applied_ids:
            continue

        run = getattr(module, "run", None)
        if run is None:
            raise RuntimeError(f"Migration {migration_id} does not define async run(db)")

        await run(db)
        await collection.insert_one(
            {
                "migration_id": migration_id,
                "applied_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        applied_now.append(migration_id)

    return applied_now
