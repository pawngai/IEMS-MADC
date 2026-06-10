from __future__ import annotations

from contexts.service_book.contracts.servicebook.revision_chain import verify_revision_chain
from contexts.service_book.contracts.servicebook.revisions import compute_revision_hash


def _revision(part: str, employee_id: str, sequence: int, prev_hash: str, payload: dict):
    return {
        "id": f"rev-{sequence}",
        "employee_id": employee_id,
        "part": part,
        "sequence": sequence,
        "prev_hash": prev_hash,
        "payload": payload,
        "hash": compute_revision_hash(part, employee_id, sequence, prev_hash, payload),
    }


def test_verify_revision_chain_valid_sequence_is_accepted():
    rev1 = _revision("I", "EMP-1", 1, "", {"value": "one"})
    rev2 = _revision("I", "EMP-1", 2, rev1["hash"], {"value": "two"})

    result = verify_revision_chain("I", [rev1, rev2])

    assert result["valid"] is True
    assert result["count"] == 2
    assert result["errors"] == []


def test_verify_revision_chain_detects_hash_tampering():
    rev1 = _revision("I", "EMP-1", 1, "", {"value": "one"})
    rev2 = _revision("I", "EMP-1", 2, rev1["hash"], {"value": "two"})
    rev2["payload"] = {"value": "tampered"}

    result = verify_revision_chain("I", [rev1, rev2])

    assert result["valid"] is False
    assert any(err["type"] == "HASH_MISMATCH" for err in result["errors"])


def test_verify_revision_chain_detects_prev_hash_mismatch():
    rev1 = _revision("I", "EMP-1", 1, "", {"value": "one"})
    rev2 = _revision("I", "EMP-1", 2, "WRONG_PREV_HASH", {"value": "two"})

    result = verify_revision_chain("I", [rev1, rev2])

    assert result["valid"] is False
    assert any(err["type"] == "PREV_HASH_MISMATCH" for err in result["errors"])


