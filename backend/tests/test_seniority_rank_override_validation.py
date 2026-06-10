from __future__ import annotations

import os
import sys

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.seniority.api.router import _apply_rank_overrides
from contexts.seniority.domain.models import RankOverride


def test_apply_rank_overrides_rejects_duplicate_ranks():
    employees = [
        {"employee_id": "emp-1", "rank": 1},
        {"employee_id": "emp-2", "rank": 2},
        {"employee_id": "emp-3", "rank": 3},
    ]

    with pytest.raises(HTTPException) as exc_info:
        _apply_rank_overrides(
            employees=employees,
            overrides=[RankOverride(employee_id="emp-3", new_rank=1)],
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Ranks must be unique whole numbers from 1 to 3"


def test_apply_rank_overrides_accepts_complete_unique_reorder():
    employees = [
        {"employee_id": "emp-1", "rank": 1},
        {"employee_id": "emp-2", "rank": 2},
        {"employee_id": "emp-3", "rank": 3},
    ]

    updated = _apply_rank_overrides(
        employees=employees,
        overrides=[
            RankOverride(employee_id="emp-1", new_rank=3),
            RankOverride(employee_id="emp-3", new_rank=1),
        ],
    )

    assert [row["employee_id"] for row in updated] == ["emp-3", "emp-2", "emp-1"]
    assert [row["rank"] for row in updated] == [1, 2, 3]