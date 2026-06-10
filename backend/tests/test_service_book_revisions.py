from __future__ import annotations

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from contexts.service_book.contracts.servicebook.revisions import (
    REVISION_COLLECTION,
    append_revision,
    compute_revision_hash,
)


class _FakeCollection:
    def __init__(self):
        self.docs = []

    async def find_one(self, query, projection=None, sort=None):
        matches = [
            d for d in self.docs
            if d.get("employee_id") == query.get("employee_id") and d.get("part") == query.get("part")
        ]
        if not matches:
            return None

        if sort:
            field, direction = sort[0]
            matches.sort(key=lambda item: item.get(field, 0), reverse=(direction == -1))

        return dict(matches[0])

    async def insert_one(self, doc):
        self.docs.append(dict(doc))


class _FakeDB:
    def __init__(self):
        self.collections = {}

    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = _FakeCollection()
        return self.collections[name]


def test_compute_revision_hash_is_deterministic_for_payload_order():
    payload_a = {"x": 1, "y": {"b": 2, "a": 1}}
    payload_b = {"y": {"a": 1, "b": 2}, "x": 1}

    hash_a = compute_revision_hash("I", "EMP-1", 1, "", payload_a)
    hash_b = compute_revision_hash("I", "EMP-1", 1, "", payload_b)

    assert hash_a == hash_b


@pytest.mark.asyncio
async def test_append_revision_increments_sequence_and_chains_prev_hash():
    db = _FakeDB()

    rev1 = await append_revision(
        db,
        part_code="I",
        employee_id="EMP-1",
        payload={"value": "first"},
        actor_user_id="user-1",
    )
    rev2 = await append_revision(
        db,
        part_code="I",
        employee_id="EMP-1",
        payload={"value": "second"},
        actor_user_id="user-2",
    )

    assert rev1["sequence"] == 1
    assert rev1["prev_hash"] == ""
    assert rev2["sequence"] == 2
    assert rev2["prev_hash"] == rev1["hash"]
    assert rev1["created_by"] == "user-1"
    assert rev2["created_by"] == "user-2"

    expected_hash_2 = compute_revision_hash("I", "EMP-1", 2, rev1["hash"], {"value": "second"})
    assert rev2["hash"] == expected_hash_2


@pytest.mark.asyncio
async def test_append_revision_is_part_scoped_for_sequences():
    db = _FakeDB()

    rev_i = await append_revision(
        db,
        part_code="I",
        employee_id="EMP-1",
        payload={"value": "i"},
        actor_user_id="user-1",
    )
    rev_vi = await append_revision(
        db,
        part_code="VI",
        employee_id="EMP-1",
        payload={"value": "vi"},
        actor_user_id="user-1",
    )

    assert rev_i["sequence"] == 1
    assert rev_vi["sequence"] == 1

    stored = db[REVISION_COLLECTION].docs
    assert len(stored) == 2
