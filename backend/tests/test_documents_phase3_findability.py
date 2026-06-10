"""Phase 3 tests: tagging, version-chain, text-query fallback, preview."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.documents.domain import metadata_rules, validation
from contexts.documents.infrastructure import (
    malware_scanner,
    metadata_ops,
    paths as _doc_paths,
    preview,
    storage_ops,
)
from contexts.documents.infrastructure.preview import (
    ImagePassThroughPreviewGenerator,
    NoOpPreviewGenerator,
    set_preview_generator_for_testing,
)
from contexts.documents.repository.metadata_repository import DocumentMetadataRepository


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def isolated_document_store(tmp_path, monkeypatch):
    documents_dir = tmp_path / "documents"
    meta_dir = documents_dir / "_meta"
    archive_dir = tmp_path / "archive"
    preview_dir = tmp_path / "previews"
    for d in (documents_dir, meta_dir, archive_dir, preview_dir):
        d.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(_doc_paths, "DOCUMENT_DIR", documents_dir)
    monkeypatch.setattr(_doc_paths, "DOCUMENT_META_DIR", meta_dir)
    monkeypatch.setattr(_doc_paths, "ARCHIVE_DIR", archive_dir)
    monkeypatch.setattr(_doc_paths, "PREVIEW_DIR", preview_dir)
    return {"docs": documents_dir, "meta": meta_dir, "previews": preview_dir}


@pytest.fixture(autouse=True)
def reset_preview_generator():
    set_preview_generator_for_testing(None)
    yield
    set_preview_generator_for_testing(None)


@pytest.fixture(autouse=True)
def reset_scanner():
    malware_scanner.set_scanner_for_testing(malware_scanner.NoOpScanner())
    yield
    malware_scanner.set_scanner_for_testing(None)


# ── 3.1 Tag normalization ───────────────────────────────────────────


def test_normalize_tags_lowercases_dedupes_and_sorts():
    out = validation.normalize_tags(["Litigation", "INVOICE", "litigation", "  pay-stub  "])
    assert out == ["invoice", "litigation", "pay-stub"]


def test_normalize_tags_rejects_invalid_chars():
    with pytest.raises(ValueError):
        validation.normalize_tags(["bad tag!"])


def test_normalize_tags_caps_count():
    with pytest.raises(ValueError):
        validation.normalize_tags([f"tag-{i}" for i in range(validation.MAX_DOCUMENT_TAGS + 1)])


def test_normalize_tags_rejects_overlong_value():
    with pytest.raises(ValueError):
        validation.normalize_tags(["x" * (validation.MAX_DOCUMENT_TAG_LENGTH + 1)])


def test_metadata_rules_normalizes_tags_in_payload():
    out = metadata_rules.validate_document_metadata({"tags": ["Foo", "bar"]})
    assert out["tags"] == ["bar", "foo"]


# ── 3.4 Version chain (local fallback) ──────────────────────────────


@pytest.mark.asyncio
async def test_list_version_chain_local_walks_backwards_and_forwards(isolated_document_store):
    repo = DocumentMetadataRepository(db=None, metadata_dir=isolated_document_store["meta"])
    # v1 superseded by v2, superseded by v3
    await repo.upsert("v1.pdf", {
        "document_id": "doc-1", "filename": "v1.pdf",
        "version_number": 1, "is_current": False,
    })
    await repo.upsert("v2.pdf", {
        "document_id": "doc-2", "filename": "v2.pdf",
        "version_number": 2, "is_current": False,
        "supersedes_document_id": "doc-1",
    })
    await repo.upsert("v3.pdf", {
        "document_id": "doc-3", "filename": "v3.pdf",
        "version_number": 3, "is_current": True,
        "supersedes_document_id": "doc-2",
    })
    # Unrelated doc
    await repo.upsert("other.pdf", {
        "document_id": "doc-other", "filename": "other.pdf",
        "version_number": 1, "is_current": True,
    })

    chain_from_middle = await repo.list_version_chain("doc-2")
    assert [r["document_id"] for r in chain_from_middle] == ["doc-1", "doc-2", "doc-3"]

    chain_from_head = await repo.list_version_chain("doc-1")
    assert [r["document_id"] for r in chain_from_head] == ["doc-1", "doc-2", "doc-3"]

    assert await repo.list_version_chain("nope") == []


# ── 3.2 Text-query fallback (in-memory path) ────────────────────────


@pytest.mark.asyncio
async def test_text_query_filters_in_memory_path(isolated_document_store):
    repo = DocumentMetadataRepository(db=None, metadata_dir=isolated_document_store["meta"])
    await repo.upsert("a.pdf", {
        "document_id": "a", "filename": "a.pdf",
        "original_name": "Joining Report — Alice.pdf",
        "tags": ["joining-report"],
    })
    await repo.upsert("b.pdf", {
        "document_id": "b", "filename": "b.pdf",
        "original_name": "Transfer Order — Bob.pdf",
        "tags": ["transfer"],
    })

    items, total = await repo.list_documents(text_query="alice")
    assert total == 1
    assert items[0]["document_id"] == "a"

    items, total = await repo.list_documents(text_query="joining-report")
    assert total == 1
    assert items[0]["document_id"] == "a"

    items, total = await repo.list_documents(text_query="nothing-matches")
    assert total == 0


# ── 3.1 Tag filter (in-memory path) ─────────────────────────────────


@pytest.mark.asyncio
async def test_tags_any_and_tags_all_filter(isolated_document_store):
    repo = DocumentMetadataRepository(db=None, metadata_dir=isolated_document_store["meta"])
    await repo.upsert("a.pdf", {"document_id": "a", "filename": "a.pdf", "tags": ["invoice", "q1"]})
    await repo.upsert("b.pdf", {"document_id": "b", "filename": "b.pdf", "tags": ["invoice"]})
    await repo.upsert("c.pdf", {"document_id": "c", "filename": "c.pdf", "tags": ["litigation"]})

    items, total = await repo.list_documents(tags_any=["invoice"])
    assert total == 2

    items, total = await repo.list_documents(tags_all=["invoice", "q1"])
    assert total == 1
    assert items[0]["document_id"] == "a"

    items, total = await repo.list_documents(tags_any=["nope"])
    assert total == 0


# ── 3.3 Preview generator ───────────────────────────────────────────


def test_image_passthrough_generator_emits_preview_for_images():
    gen = ImagePassThroughPreviewGenerator()
    assert gen.can_generate(content_type="image/png")
    result = gen.generate(content=b"PNGDATA", content_type="image/png")
    assert result is not None
    assert result.content == b"PNGDATA"
    assert result.media_type == "image/png"
    assert result.suffix == "_preview"


def test_image_passthrough_generator_skips_non_images():
    gen = ImagePassThroughPreviewGenerator()
    assert not gen.can_generate(content_type="application/pdf")
    assert gen.generate(content=b"%PDF-1.4", content_type="application/pdf") is None


def test_preview_filename_for_appends_suffix_before_extension():
    assert preview.preview_filename_for("abc.png", suffix="_preview") == "abc_preview.png"
    assert preview.preview_filename_for("no-ext", suffix="_preview") == "no-ext_preview"


class _Upload:
    def __init__(self, contents, content_type, filename):
        self._contents = contents
        self.content_type = content_type
        self.filename = filename

    async def read(self):
        return self._contents


@pytest.mark.asyncio
async def test_upload_generates_image_preview(isolated_document_store, monkeypatch):
    # Use a real PNG-magic-byte payload so the upload's magic-byte validation passes.
    contents = b"\x89PNG\r\n\x1a\n" + b"rest-of-png"
    set_preview_generator_for_testing(ImagePassThroughPreviewGenerator())

    result = await storage_ops.upload_document(
        _Upload(contents, "image/png", "x.png"),
        current_user={"sub": "u1", "employee_id": "EMP-1"},
        db=None,
    )
    meta = await metadata_ops.read_document_metadata(result["filename"])
    assert meta["preview_filename"]
    # The preview blob should exist in the preview bucket.
    from contexts.documents.infrastructure.storage import StorageBucket
    assert storage_ops.storage().exists(StorageBucket.PREVIEW, meta["preview_filename"])


@pytest.mark.asyncio
async def test_upload_with_noop_generator_records_no_preview(isolated_document_store):
    contents = b"%PDF-1.4\nfake-pdf"
    set_preview_generator_for_testing(NoOpPreviewGenerator())

    result = await storage_ops.upload_document(
        _Upload(contents, "application/pdf", "x.pdf"),
        current_user={"sub": "u1", "employee_id": "EMP-1"},
        db=None,
    )
    meta = await metadata_ops.read_document_metadata(result["filename"])
    assert meta["preview_filename"] is None
