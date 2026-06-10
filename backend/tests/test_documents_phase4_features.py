"""Phase 4 tests: share links, bulk ops, expiry, templates, signature requests."""
from __future__ import annotations

import io
import os
import sys
import zipfile
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.documents.application import (
    share_service,
    signature_service,
    template_service,
)
from contexts.documents.domain import share_token, signature_request, template
from contexts.documents.infrastructure import (
    bulk_ops,
    expiry_job,
    metadata_ops,
    paths as _doc_paths,
)
from contexts.documents.infrastructure.malware_scanner import (
    NoOpScanner,
    set_scanner_for_testing,
)
from contexts.documents.repository.template_repository import DocumentTemplateRepository
from contexts.documents.repository.signature_request_repository import SignatureRequestRepository


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def isolated_document_store(tmp_path, monkeypatch):
    docs = tmp_path / "documents"
    meta = docs / "_meta"
    archive = tmp_path / "archive"
    previews = tmp_path / "previews"
    for d in (docs, meta, archive, previews):
        d.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(_doc_paths, "DOCUMENT_DIR", docs)
    monkeypatch.setattr(_doc_paths, "DOCUMENT_META_DIR", meta)
    monkeypatch.setattr(_doc_paths, "ARCHIVE_DIR", archive)
    monkeypatch.setattr(_doc_paths, "PREVIEW_DIR", previews)
    return {"docs": docs, "meta": meta}


@pytest.fixture(autouse=True)
def reset_scanner():
    set_scanner_for_testing(NoOpScanner())
    yield
    set_scanner_for_testing(None)


# ── 4.5 Share tokens ────────────────────────────────────────────────


def test_share_token_round_trip():
    expires = datetime.now(timezone.utc) + timedelta(hours=1)
    token, nonce = share_token.issue_token(
        secret="s" * 32,
        document_id="doc-1",
        filename="abc.pdf",
        expires_at=expires,
    )
    payload = share_token.parse_token(secret="s" * 32, token=token)
    assert payload["d"] == "doc-1"
    assert payload["f"] == "abc.pdf"
    assert payload["n"] == nonce
    assert not share_token.is_expired(payload)


def test_share_token_rejects_tampered_signature():
    expires = datetime.now(timezone.utc) + timedelta(hours=1)
    token, _ = share_token.issue_token(
        secret="s" * 32, document_id="doc-1", filename="abc.pdf", expires_at=expires
    )
    bad = token[:-2] + "AA"
    with pytest.raises(ValueError):
        share_token.parse_token(secret="s" * 32, token=bad)


def test_share_token_expired_marker():
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    token, _ = share_token.issue_token(
        secret="s" * 32, document_id="doc-1", filename="abc.pdf", expires_at=past
    )
    payload = share_token.parse_token(secret="s" * 32, token=token)
    assert share_token.is_expired(payload) is True


def test_share_token_ttl_clamped():
    assert share_token.clamp_ttl_seconds(60) == 60
    assert share_token.clamp_ttl_seconds(10**9) == 7 * 24 * 3600


@pytest.mark.asyncio
async def test_create_and_resolve_share_link(isolated_document_store, monkeypatch):
    filename = "share.pdf"
    (isolated_document_store["docs"] / filename).write_bytes(b"%PDF-1.4\nshare")

    await metadata_ops.write_document_metadata(filename, {
        "document_id": "doc-share-1",
        "filename": filename,
        "uploaded_employee_id": "EMP-1",
    })

    result = await share_service.create_document_share_link(
        filename=filename,
        ttl_seconds=600,
        current_user={"sub": "u1", "employee_id": "EMP-1"},
        db=None,
    )
    assert result["token"]
    assert result["nonce"]

    # Anonymous resolve should succeed
    response = await share_service.resolve_share_token(token=result["token"], db=None)
    assert response is not None

    # After revoke, resolve should 410
    await share_service.revoke_document_share_link(
        filename=filename,
        nonce=result["nonce"],
        current_user={"sub": "u1", "employee_id": "EMP-1"},
        db=None,
    )
    with pytest.raises(HTTPException) as exc:
        await share_service.resolve_share_token(token=result["token"], db=None)
    assert exc.value.status_code == 410


@pytest.mark.asyncio
async def test_share_link_blocked_for_legal_hold(isolated_document_store):
    filename = "held.pdf"
    (isolated_document_store["docs"] / filename).write_bytes(b"%PDF-1.4")
    await metadata_ops.write_document_metadata(filename, {
        "document_id": "d1", "filename": filename,
        "uploaded_employee_id": "EMP-1",
        "legal_hold": True, "legal_hold_reason": "Litigation",
    })
    with pytest.raises(HTTPException) as exc:
        await share_service.create_document_share_link(
            filename=filename, ttl_seconds=600,
            current_user={"sub": "u1", "employee_id": "EMP-1"}, db=None,
        )
    assert exc.value.status_code == 409


# ── 4.4 Bulk ops ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_bulk_download_zip_skips_unauthorized(isolated_document_store):
    files = {
        "mine.pdf": b"%PDF-1.4\nmine",
        "yours.pdf": b"%PDF-1.4\nyours",
    }
    for name, body in files.items():
        (isolated_document_store["docs"] / name).write_bytes(body)
    await metadata_ops.write_document_metadata("mine.pdf", {
        "document_id": "d-mine", "filename": "mine.pdf",
        "uploaded_employee_id": "EMP-1", "original_name": "Mine.pdf",
    })
    await metadata_ops.write_document_metadata("yours.pdf", {
        "document_id": "d-yours", "filename": "yours.pdf",
        "uploaded_employee_id": "EMP-2", "original_name": "Yours.pdf",
    })

    chunks = []
    async for chunk in bulk_ops.stream_bulk_download_zip(
        filenames=["mine.pdf", "yours.pdf"],
        current_user={"sub": "u1", "employee_id": "EMP-1", "authorities": ["EMPLOYEE"]},
        db=None,
    ):
        chunks.append(chunk)

    zip_bytes = b"".join(chunks)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = sorted(zf.namelist())
    assert names == ["Mine.pdf"]  # yours.pdf was silently dropped


@pytest.mark.asyncio
async def test_bulk_apply_tags_adds_and_dedupes(isolated_document_store):
    filename = "a.pdf"
    (isolated_document_store["docs"] / filename).write_bytes(b"%PDF-1.4")
    await metadata_ops.write_document_metadata(filename, {
        "document_id": "d1", "filename": filename,
        "uploaded_employee_id": "EMP-1",
        "tags": ["invoice"],
    })

    result = await bulk_ops.bulk_apply_tags(
        filenames=[filename], tags=["Litigation", "invoice"],
        current_user={"sub": "u1", "employee_id": "EMP-1", "authorities": ["EMPLOYEE"]},
        db=None,
    )
    assert filename in result["updated"]
    meta = await metadata_ops.read_document_metadata(filename)
    assert meta["tags"] == ["invoice", "litigation"]


# ── 4.3 Expiry job (in-memory path returns 0 — use unit on the parser) ────


def test_expiry_parser_handles_iso_and_invalid():
    from contexts.documents.infrastructure.expiry_job import _parse_iso
    assert _parse_iso(None) is None
    assert _parse_iso("not-a-date") is None
    dt = _parse_iso("2026-01-01T00:00:00Z")
    assert dt is not None and dt.year == 2026


# ── 4.1 Templates ────────────────────────────────────────────────────


def test_validate_render_values_enforces_required_and_unknown():
    tmpl = template.DocumentTemplate(
        template_id="t1", name="t1", document_type="ORDER",
        base_filename="x.txt", content_type="text/plain",
        fields=[
            template.TemplateField(name="employee_name", required=True),
            template.TemplateField(name="effective_date", required=False, default="N/A"),
        ],
    )
    with pytest.raises(ValueError):
        template.validate_render_values(tmpl, {})
    out = template.validate_render_values(tmpl, {"employee_name": "Alice"})
    assert out == {"employee_name": "Alice", "effective_date": "N/A"}
    with pytest.raises(ValueError):
        template.validate_render_values(tmpl, {"employee_name": "Alice", "unknown_field": "x"})


def test_render_text_substitutes_placeholders():
    body = b"Hello ${employee_name}, effective ${effective_date}."
    out = template.render_text(body, {"employee_name": "Alice", "effective_date": "2026-05-01"})
    assert out == b"Hello Alice, effective 2026-05-01."


def test_template_field_name_validation():
    with pytest.raises(ValueError):
        template.TemplateField(name="Bad-Name")


# ── 4.2 Signature requests ──────────────────────────────────────────


def test_validate_signers_rejects_duplicates_and_empties():
    with pytest.raises(ValueError):
        signature_request.validate_signers([])
    with pytest.raises(ValueError):
        signature_request.validate_signers([
            {"employee_id": "EMP-1"}, {"employee_id": "EMP-1"}
        ])
    signers = signature_request.validate_signers([
        {"employee_id": "EMP-1", "role": "HOD"},
        {"employee_id": "EMP-2"},
    ])
    assert [s.employee_id for s in signers] == ["EMP-1", "EMP-2"]
    assert signers[1].role == "signer"


def test_signature_request_pending_predicate_and_current_signer():
    req = signature_request.SignatureRequest(
        request_id="r1", document_id="d1", filename="f.pdf",
        status=signature_request.SIGNATURE_STATUS_PENDING,
        signers=[
            signature_request.Signer(employee_id="EMP-A", role="HOD"),
            signature_request.Signer(employee_id="EMP-B", role="DDO"),
        ],
    )
    assert req.is_pending()
    assert req.current_signer_index() == 0

    # Wrong signer's turn
    with pytest.raises(ValueError):
        signature_request.assert_can_sign(req, signer_employee_id="EMP-B")
    # Correct signer
    assert signature_request.assert_can_sign(req, signer_employee_id="EMP-A") == 0


@pytest.mark.asyncio
async def test_signature_lifecycle_via_in_memory_repo(isolated_document_store, monkeypatch):
    """End-to-end test with an in-memory repo stub for the request collection.
    Demonstrates: create → sign A → sign B → COMPLETED + lock applied."""

    class _InMemoryRepo:
        def __init__(self):
            self.rows: dict[str, dict] = {}

        async def ensure_indexes(self):
            return

        async def upsert(self, request):
            from contexts.documents.repository.signature_request_repository import _to_doc
            self.rows[request.request_id] = _to_doc(request)

        async def get(self, request_id: str):
            from contexts.documents.repository.signature_request_repository import _from_doc
            return _from_doc(self.rows.get(request_id))

        async def list_pending_for_signer(self, employee_id):
            from contexts.documents.repository.signature_request_repository import _from_doc
            out = []
            for row in self.rows.values():
                req = _from_doc(row)
                if req and req.is_pending() and any(s.employee_id == employee_id for s in req.signers):
                    idx = req.current_signer_index()
                    if idx is not None and req.signers[idx].employee_id == employee_id:
                        out.append(req)
            return out

    stub = _InMemoryRepo()
    monkeypatch.setattr(
        signature_service,
        "SignatureRequestRepository",
        lambda *, db: stub,
    )

    # Stub the lock call — it would otherwise need a real document on disk.
    locked: list[str] = []
    async def fake_lock(attachments, **kwargs):
        for att in attachments:
            locked.append(att["filename"])
    monkeypatch.setattr(
        signature_service, "lock_documents_for_approved_request", fake_lock,
    )

    # Put a real document file on disk so storage.exists() passes for create.
    filename = "needs-sign.pdf"
    (isolated_document_store["docs"] / filename).write_bytes(b"%PDF-1.4")
    await metadata_ops.write_document_metadata(filename, {
        "document_id": "doc-1", "filename": filename,
        "uploaded_employee_id": "EMP-Issuer",
    })

    issuer = {"sub": "u-issuer", "employee_id": "EMP-Issuer"}
    created = await signature_service.create_signature_request(
        filename=filename,
        signers_input=[
            {"employee_id": "EMP-A", "role": "HOD"},
            {"employee_id": "EMP-B", "role": "APPROVING_AUTHORITY"},
        ],
        deadline_at=None,
        current_user=issuer,
        db=None,
    )
    request_id = created["request_id"]
    assert created["status"] == "PENDING"
    assert created["current_signer_index"] == 0

    # A signs
    after_a = await signature_service.sign_signature_request(
        request_id=request_id, signature_filename=None,
        current_user={"sub": "u-a", "employee_id": "EMP-A"}, db=object(),
    )
    assert after_a["current_signer_index"] == 1
    assert after_a["status"] == "PENDING"

    # B signs — request completes and document locks
    after_b = await signature_service.sign_signature_request(
        request_id=request_id, signature_filename=None,
        current_user={"sub": "u-b", "employee_id": "EMP-B"}, db=object(),
    )
    assert after_b["status"] == "COMPLETED"
    assert after_b["completed_at"]
    assert locked == [filename]


@pytest.mark.asyncio
async def test_signature_decline_marks_declined(isolated_document_store, monkeypatch):
    class _MemRepo:
        def __init__(self):
            self.rows = {}
        async def ensure_indexes(self): return
        async def upsert(self, req):
            from contexts.documents.repository.signature_request_repository import _to_doc
            self.rows[req.request_id] = _to_doc(req)
        async def get(self, rid):
            from contexts.documents.repository.signature_request_repository import _from_doc
            return _from_doc(self.rows.get(rid))
        async def list_pending_for_signer(self, eid): return []

    stub = _MemRepo()
    monkeypatch.setattr(signature_service, "SignatureRequestRepository", lambda *, db: stub)

    filename = "to-decline.pdf"
    (isolated_document_store["docs"] / filename).write_bytes(b"%PDF-1.4")
    await metadata_ops.write_document_metadata(filename, {
        "document_id": "doc-d", "filename": filename,
        "uploaded_employee_id": "EMP-Issuer",
    })

    created = await signature_service.create_signature_request(
        filename=filename,
        signers_input=[{"employee_id": "EMP-A"}],
        deadline_at=None,
        current_user={"sub": "u", "employee_id": "EMP-Issuer"},
        db=None,
    )
    result = await signature_service.decline_signature_request(
        request_id=created["request_id"], reason="Out of scope",
        current_user={"sub": "u-a", "employee_id": "EMP-A"}, db=object(),
    )
    assert result["status"] == "DECLINED"
    assert result["signers"][0]["decline_reason"] == "Out of scope"
