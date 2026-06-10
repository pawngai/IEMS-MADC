from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.identity_access.identity.infrastructure import activity_service
from contexts.identity_access.identity.infrastructure import service


@pytest.mark.asyncio
async def test_get_role_change_stats_computes_weekly_slice_separately(monkeypatch) -> None:
    fixed_now = datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc)

    class _FixedDateTime:
        @staticmethod
        def now(tz=None):
            if tz is None:
                return fixed_now.replace(tzinfo=None)
            return fixed_now.astimezone(tz)

        @staticmethod
        def fromtimestamp(ts, tz=None):
            return datetime.fromtimestamp(ts, tz=tz)

    seen_match_windows: list[str] = []

    async def _fake_aggregate_role_change_stats(_db, pipeline):
        since_iso = pipeline[0]["$match"]["timestamp"]["$gte"]
        seen_match_windows.append(since_iso)
        if since_iso == "2026-03-08T12:00:00+00:00":
            return [{"_id": "grant", "count": 3}, {"_id": "revoke", "count": 1}]
        if since_iso == "2026-02-13T12:00:00+00:00":
            return [{"_id": "grant", "count": 8}, {"_id": "revoke", "count": 4}]
        raise AssertionError(f"Unexpected stats window: {since_iso}")

    monkeypatch.setattr(activity_service, "datetime", _FixedDateTime)
    monkeypatch.setattr(
        activity_service.repo,
        "aggregate_role_change_stats",
        _fake_aggregate_role_change_stats,
    )

    result = await service.get_role_change_stats(
        object(),
        days=30,
        current_user={"authorities": ["SYSTEM_ADMIN"]},
    )

    assert result == {
        "days": 30,
        "stats": [{"_id": "grant", "count": 8}, {"_id": "revoke", "count": 4}],
        "total_changes": 12,
        "changes_last_7_days": 4,
    }
    assert seen_match_windows == [
        "2026-02-13T12:00:00+00:00",
        "2026-03-08T12:00:00+00:00",
    ]