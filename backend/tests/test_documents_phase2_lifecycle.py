"""Phase 2 tests: legal hold, retention, malware scanning, audit timeline."""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.documents.domain import retention, scanning, validation
from contexts.documents.infrastructure import (
    lock_ops,
    malware_scanner,
    paths as _doc_paths,
    retention_job,
    storage_ops,
)
from contexts.documents.infrastructure.malware_scanner import (
    EicarOnlyScanner,
    NoOpScanner,
    set_scanner_for_testing,
)
from contexts.documents.infrastructure.storage import StorageBucket
from contexts.documents.repository.metadata_repository import COLLECTION as METADATA_COLLECTION


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def isolated_document_store(tmp_path, monkeypatch):
    documents_dir = tmp_path / "documents"
    meta_dir = documents_dir / "_meta"
    archive_dir = tmp_path / "archive"
    documents_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(_doc_paths, "DOCUMENT_DIR", documents_dir)
    monkeypatch.setattr(_doc_paths, "DOCUMENT_META_DIR", meta_dir)
    monkeypatch.setattr(_doc_paths, "ARCHIVE_DIR", archive_dir)

    return {"documents": documents_dir, "meta": meta_dir, "archive": archive_dir}


@pytest.fixture(autouse=True)
def reset_scanner():
    set_scanner_for_testing(None)
    yield
    set_scanner_for_testing(None)


# ── 2.2 Legal hold ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_apply_legal_hold_sets_flag_and_emits_event(isolated_document_store, monkeypatch):
    filename = "legal-hold-file.pdf"
    (isolated_document_store["documents"] / filename).write_bytes(b"%PDF-1.4\nhold")

    from contexts.documents.infrastructure import metadata_ops
    await metadata_ops.write_document_metadata(filename, {"uploaded_employee_id": "EMP-1"})

    published: list[dict] = []

    async def fake_publish(**kwargs):
        published.append(kwargs)

    monkeypatch.setattr(
        "contexts.documents.infrastructure.lock_ops.publish_document_event",
        fake_publish,
    )

    result = await lock_ops.apply_legal_hold(
        filename,
        reason="Litigation #1234",
        applied_by_user_id="admin-1",
    )

    assert result["legal_hold"] is True
    assert result["legal_hold_reason"] == "Litigation #1234"

    meta = await metadata_ops.read_document_metadata(filename)
    assert meta["legal_hold"] is True
    assert meta["legal_hold_reason"] == "Litigation #1234"
    assert meta["legal_hold_applied_at"]

    assert len(published) == 1
    assert published[0]["name"] == "DocumentLegalHoldApplied"
    assert published[0]["payload"]["legal_hold_reason"] == "Litigation #1234"


@pytest.mark.asyncio
async def test_apply_legal_hold_rejects_empty_reason(isolated_document_store):
    filename = "no-reason.pdf"
    (isolated_document_store["documents"] / filename).write_bytes(b"%PDF-1.4")

    with pytest.raises(HTTPException) as exc:
        await lock_ops.apply_legal_hold(filename, reason="  ", applied_by_user_id="admin")
    assert exc.value.status_code == 422
    assert exc.value.detail["error_code"] == "LEGAL_HOLD_REASON_REQUIRED"


@pytest.mark.asyncio
async def test_legal_hold_blocks_delete(isolated_document_store):
    filename = "held.pdf"
    (isolated_document_store["documents"] / filename).write_bytes(b"%PDF-1.4")

    from contexts.documents.infrastructure import metadata_ops
    await metadata_ops.write_document_metadata(
        filename,
        {
            "uploaded_employee_id": "EMP-1",
            "legal_hold": True,
            "legal_hold_reason": "Litigation",
        },
    )

    with pytest.raises(HTTPException) as exc:
        await storage_ops.delete_document(
            filename,
            current_user={"sub": "admin", "authorities": ["SYSTEM_ADMIN"]},
        )
    assert exc.value.status_code == 400
    assert exc.value.detail["error_code"] == "DOCUMENT_LEGAL_HOLD"


@pytest.mark.asyncio
async def test_release_legal_hold_clears_flag(isolated_document_store, monkeypatch):
    filename = "release-me.pdf"
    (isolated_document_store["documents"] / filename).write_bytes(b"%PDF-1.4")

    from contexts.documents.infrastructure import metadata_ops
    await metadata_ops.write_document_metadata(
        filename,
        {"legal_hold": True, "legal_hold_reason": "Old reason"},
    )

    monkeypatch.setattr(
        "contexts.documents.infrastructure.lock_ops.publish_document_event",
        lambda **kw: _async_noop(),
    )

    result = await lock_ops.release_legal_hold(
        filename, released_by_user_id="admin-2", release_reason="Case closed"
    )
    assert result["legal_hold"] is False
    assert result["legal_hold_released_at"]


async def _async_noop():
    return None


def test_legal_hold_predicate():
    assert validation.is_legal_hold_active({"legal_hold": True}) is True
    assert validation.is_legal_hold_active({}) is False
    assert validation.is_document_protected_from_mutation({"legal_hold": True}) is True
    assert validation.is_document_protected_from_mutation({"is_locked": True}) is True
    assert validation.is_document_protected_from_mutation({}) is False


# ── 2.1 Retention ───────────────────────────────────────────────────


def test_retention_policy_specificity_matches_more_specific_first():
    catch_all = retention.RetentionPolicy(key="default", archive_after_days=365)
    specific = retention.RetentionPolicy(
        key="leave-orders",
        document_type="ORDER",
        source_context="leave.attachment",
        archive_after_days=30,
    )
    selected = retention.select_policy(
        {"document_type": "ORDER", "source_context": "leave.attachment"},
        [catch_all, specific],
    )
    assert selected.key == "leave-orders"


def test_eligible_for_archive_respects_legal_hold():
    policy = retention.RetentionPolicy(key="default", archive_after_days=1)
    long_ago = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()

    assert retention.is_eligible_for_archive(
        {"uploaded_at": long_ago, "legal_hold": False},
        policy,
    )
    assert not retention.is_eligible_for_archive(
        {"uploaded_at": long_ago, "legal_hold": True},
        policy,
    )


def test_eligible_for_delete_only_after_archive_window():
    policy = retention.RetentionPolicy(
        key="default", archive_after_days=30, delete_after_archive_days=90
    )
    archived_yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    archived_long_ago = (datetime.now(timezone.utc) - timedelta(days=400)).isoformat()

    assert not retention.is_eligible_for_delete(
        {"archived_at": archived_yesterday}, policy
    )
    assert retention.is_eligible_for_delete(
        {"archived_at": archived_long_ago}, policy
    )


# ── 2.4 Malware scanning ────────────────────────────────────────────


class _ScanUpload:
    def __init__(self, contents: bytes, content_type: str = "application/pdf", filename: str = "x.pdf"):
        self._contents = contents
        self.content_type = content_type
        self.filename = filename

    async def read(self) -> bytes:
        return self._contents


@pytest.mark.asyncio
async def test_upload_rejects_infected_file(isolated_document_store):
    set_scanner_for_testing(EicarOnlyScanner())
    eicar_payload = (
        b"%PDF-1.4\n"
        b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    )
    with pytest.raises(HTTPException) as exc:
        await storage_ops.upload_document(
            _ScanUpload(eicar_payload),
            current_user={"sub": "u1", "employee_id": "EMP-1"},
            db=None,
        )
    assert exc.value.status_code == 400
    assert exc.value.detail["error_code"] == "DOCUMENT_INFECTED"
    assert exc.value.detail["threat_name"] == "EICAR-Test-File"


@pytest.mark.asyncio
async def test_upload_marks_clean_files(isolated_document_store):
    set_scanner_for_testing(NoOpScanner())
    payload = b"%PDF-1.4\nclean content"
    result = await storage_ops.upload_document(
        _ScanUpload(payload),
        current_user={"sub": "u1", "employee_id": "EMP-1"},
        db=None,
    )
    from contexts.documents.infrastructure import metadata_ops
    meta = await metadata_ops.read_document_metadata(result["filename"])
    assert meta["scan_status"] == "CLEAN"


@pytest.mark.asyncio
async def test_scan_gate_blocks_infected_download(isolated_document_store):
    filename = "infected.pdf"
    (isolated_document_store["documents"] / filename).write_bytes(b"%PDF-1.4")

    from contexts.documents.infrastructure import metadata_ops
    await metadata_ops.write_document_metadata(
        filename,
        {
            "uploaded_employee_id": "EMP-1",
            "scan_status": "INFECTED",
            "scan_threat_name": "EICAR-Test-File",
        },
    )

    with pytest.raises(HTTPException) as exc:
        await storage_ops.download_document(
            filename,
            current_user={"sub": "admin", "authorities": ["SYSTEM_ADMIN"]},
        )
    assert exc.value.status_code == 403
    assert exc.value.detail["error_code"] == "DOCUMENT_INFECTED"


def test_scan_status_validation():
    with pytest.raises(ValueError):
        scanning.ScanResult(status="MAYBE", backend="x")
