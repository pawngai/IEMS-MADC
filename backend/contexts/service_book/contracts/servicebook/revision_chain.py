from __future__ import annotations

from typing import Any

from contexts.service_book.contracts.servicebook.revisions import compute_revision_hash


def verify_revision_chain(part_code: str, revisions: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    prev_hash = ""
    expected_sequence = 1

    for rev in revisions:
        seq = int(rev.get("sequence", 0) or 0)
        if seq != expected_sequence:
            errors.append(
                {
                    "type": "SEQUENCE_GAP",
                    "expected_sequence": expected_sequence,
                    "actual_sequence": seq,
                    "revision_id": rev.get("id"),
                }
            )
            expected_sequence = seq

        actual_prev_hash = rev.get("prev_hash", "") or ""
        if actual_prev_hash != prev_hash:
            errors.append(
                {
                    "type": "PREV_HASH_MISMATCH",
                    "sequence": seq,
                    "expected_prev_hash": prev_hash,
                    "actual_prev_hash": actual_prev_hash,
                    "revision_id": rev.get("id"),
                }
            )

        payload = rev.get("payload", {})
        expected_hash = compute_revision_hash(
            part_code, rev.get("employee_id", ""), seq, actual_prev_hash, payload
        )
        actual_hash = rev.get("hash", "")
        if expected_hash != actual_hash:
            errors.append(
                {
                    "type": "HASH_MISMATCH",
                    "sequence": seq,
                    "expected_hash": expected_hash,
                    "actual_hash": actual_hash,
                    "revision_id": rev.get("id"),
                }
            )

        prev_hash = actual_hash
        expected_sequence += 1

    return {
        "valid": len(errors) == 0,
        "count": len(revisions),
        "errors": errors,
        "latest_hash": prev_hash,
    }