from __future__ import annotations

import pytest

from contexts.identity.contracts import system_config


class _FakeSystemConfigCollection:
    def __init__(self) -> None:
        self.doc = {"_id": "main", "financial_year": "2025-26"}

    async def find_one(self, query, projection=None):
        if query != {"_id": "main"}:
            return None
        if not self.doc:
            return None
        if projection and projection.get("_id") == 0:
            return {k: v for k, v in self.doc.items() if k != "_id"}
        return dict(self.doc)

    async def update_one(self, query, update, upsert=False):
        assert query == {"_id": "main"}
        assert "$set" in update
        if not self.doc and upsert:
            self.doc = {"_id": "main"}
        set_map = update["$set"]
        for key, value in set_map.items():
            if "." in key:
                top, child = key.split(".", 1)
                self.doc.setdefault(top, {})
                self.doc[top][child] = value
            else:
                self.doc[key] = value


class _FakeDb:
    def __init__(self) -> None:
        self.system_config = _FakeSystemConfigCollection()


@pytest.mark.asyncio
async def test_get_system_config_returns_existing_doc() -> None:
    db = _FakeDb()

    result = await system_config.get_system_config(db)

    assert result["financial_year"] == "2025-26"


@pytest.mark.asyncio
async def test_set_system_config_key_updates_doc_and_meta() -> None:
    db = _FakeDb()

    result = await system_config.set_system_config_key(
        db,
        key="module_permissions",
        value={"matrix": {"SYSTEM_ADMIN": {"admin_console": True}}},
        updated_by="admin-1",
        reason="Enable admin console visibility",
    )

    assert result["module_permissions"]["matrix"]["SYSTEM_ADMIN"]["admin_console"] is True
    assert result["_meta"]["updated_by"] == "admin-1"
    assert result["_meta"]["update_reason"] == "Enable admin console visibility"
