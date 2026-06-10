"""Phase 1 hardening tests for the documents context."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta

import pytest
from fastapi import HTTPException
from fastapi.responses import Response

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.documents.domain.validation import extension_for_content_type
from contexts.documents.infrastructure import storage_ops
from contexts.documents.infrastructure.storage import (
    DocumentStorage,
    ResilientDocumentStorage,
    StorageBucket,
    StorageObjectStat,
)
from contexts.documents.infrastructure import query as query_mod
from contexts.documents.contracts.document_metadata import (
    get_subject_document_for_current_user,
    download_subject_document_for_current_user,
)
from contexts.employee_profile.contracts.media_directory import employee_owns_media


# ── 1.1 Extension hygiene ───────────────────────────────────────────


class _FakeUpload:
    def __init__(self, filename: str | None, content_type: str | None) -> None:
        self.filename = filename
        self.content_type = content_type


@pytest.mark.parametrize(
    "filename, content_type, expected_ext",
    [
        ("photo.PDF", "application/pdf", "pdf"),
        ("photo", "image/jpeg", "jpg"),
        ("photo.<script>", "image/png", "png"),
        ("doc.exe", "application/pdf", "pdf"),
        ("photo.jpg", "image/jpeg", "jpg"),
    ],
)
def test_make_unique_filename_derives_extension_from_content_type(filename, content_type, expected_ext):
    name = storage_ops.make_unique_filename(
        _FakeUpload(filename, content_type), default_ext="bin"
    )
    assert name.endswith(f".{expected_ext}")
    # Single dot separating the unique segment from the extension.
    assert name.count(".") == 1


def test_make_unique_filename_falls_back_to_default_when_content_type_unknown():
    name = storage_ops.make_unique_filename(
        _FakeUpload("blob", "application/x-not-allowed"), default_ext="bin"
    )
    assert name.endswith(".bin")


def test_extension_for_content_type_handles_known_and_unknown():
    assert extension_for_content_type("application/pdf") == "pdf"
    assert extension_for_content_type("IMAGE/JPEG") == "jpg"
    assert extension_for_content_type(None) is None
    assert extension_for_content_type("application/x-novel") is None


# ── 1.2 Resilient storage split-state ───────────────────────────────


@dataclass
class _FakeStore(DocumentStorage):
    names: dict[str, tuple[int, datetime]] = field(default_factory=dict)
    fail_write: bool = False
    fail_exists: bool = False
    deleted: list[str] = field(default_factory=list)
    writes: list[tuple[StorageBucket, str, bytes]] = field(default_factory=list)

    def exists(self, bucket: StorageBucket, filename: str) -> bool:
        if self.fail_exists:
            raise RuntimeError("exists failed")
        return filename in self.names

    def write_bytes(self, bucket, filename, contents, *, content_type=None):
        if self.fail_write:
            # Simulate a partial write — the blob exists but is truncated.
            self.names[filename] = (0, datetime.now(timezone.utc))
            raise RuntimeError("write failed")
        self.names[filename] = (len(contents), datetime.now(timezone.utc))
        self.writes.append((bucket, filename, contents))

    def delete(self, bucket, filename):
        self.deleted.append(filename)
        self.names.pop(filename, None)

    def read_bytes(self, bucket, filename):
        return b""

    def list_names(self, bucket):
        return list(self.names.keys())

    def stat(self, bucket, filename):
        size, modified = self.names[filename]
        return StorageObjectStat(filename=filename, size=size, modified_at=modified)

    def inline_response(self, bucket, filename, *, media_type):
        return Response(content=f"inline:{filename}", media_type=media_type)

    def download_response(self, bucket, filename, *, media_type):
        return Response(content=f"download:{filename}", media_type=media_type)


def test_resilient_storage_cleans_partial_primary_after_write_failure():
    primary = _FakeStore(fail_write=True)
    fallback = _FakeStore()
    storage = ResilientDocumentStorage(primary=primary, fallback=fallback)

    storage.write_bytes(StorageBucket.DOCUMENT, "file.pdf", b"payload")

    assert "file.pdf" not in primary.names
    assert primary.deleted == ["file.pdf"]
    assert fallback.names["file.pdf"][0] == len(b"payload")


def test_resilient_storage_write_health_detects_divergence():
    now = datetime.now(timezone.utc)
    primary = _FakeStore(names={"file.pdf": (10, now)})
    fallback = _FakeStore(names={"file.pdf": (20, now + timedelta(seconds=5))})
    storage = ResilientDocumentStorage(primary=primary, fallback=fallback)

    health = storage.write_health(StorageBucket.DOCUMENT, "file.pdf")

    assert health["split_state"] is True
    assert health["primary_size"] == 10
    assert health["fallback_size"] == 20


def test_resilient_storage_write_health_clean_when_only_one_side_has_file():
    primary = _FakeStore(names={"file.pdf": (10, datetime.now(timezone.utc))})
    fallback = _FakeStore()
    storage = ResilientDocumentStorage(primary=primary, fallback=fallback)

    health = storage.write_health(StorageBucket.DOCUMENT, "file.pdf")

    assert health["split_state"] is False
    assert health["primary_exists"] is True
    assert health["fallback_exists"] is False


# ── 1.3 In-memory listing gate ──────────────────────────────────────


def _settings_module():
    # ``app_platform.config.__init__`` rebinds the ``settings`` attribute to
    # the singleton instance, shadowing the submodule. Reach for the module
    # directly via ``sys.modules`` so monkeypatching targets the right name.
    return sys.modules["app_platform.config.settings"]


def test_in_memory_listing_blocked_in_production(monkeypatch):
    fake_settings = type(
        "S",
        (),
        {"is_production": True, "allow_document_in_memory_listing": False},
    )()
    monkeypatch.setattr(_settings_module(), "settings", fake_settings)

    with pytest.raises(HTTPException) as exc:
        query_mod._require_in_memory_listing_allowed()
    assert exc.value.status_code == 503
    assert exc.value.detail["error_code"] == "DOCUMENT_LISTING_UNAVAILABLE"


def test_in_memory_listing_allowed_outside_production(monkeypatch):
    fake_settings = type(
        "S",
        (),
        {"is_production": False, "allow_document_in_memory_listing": False},
    )()
    monkeypatch.setattr(_settings_module(), "settings", fake_settings)

    # Should not raise.
    query_mod._require_in_memory_listing_allowed()


# ── 1.5 employee_profile media-directory contract ───────────────────


class _ProfileCollection:
    def __init__(self, rows):
        self.rows = rows

    async def find_one(self, query, projection=None):
        for row in self.rows:
            if row.get("employee_id") != query.get("employee_id"):
                continue
            for clause in query.get("$or", []):
                if all(row.get(k) == v for k, v in clause.items()):
                    return row
        return None


class _FakeProfileDb:
    def __init__(self, read_rows=(), ext_rows=()):
        self.employee_profile_read_models = _ProfileCollection(list(read_rows))
        self.employee_profile_extensions = _ProfileCollection(list(ext_rows))


@pytest.mark.asyncio
async def test_employee_owns_media_matches_via_expected_url():
    db = _FakeProfileDb(
        read_rows=[
            {"employee_id": "EMP-1", "photo_url": "/api/documents/photos/abc.jpg"}
        ]
    )
    assert await employee_owns_media(
        db,
        employee_id="EMP-1",
        field="photo_url",
        expected_url="/api/documents/photos/abc.jpg",
        filename="abc.jpg",
    )


@pytest.mark.asyncio
async def test_employee_owns_media_matches_legacy_bare_filename():
    db = _FakeProfileDb(
        ext_rows=[{"employee_id": "EMP-2", "signature_url": "old.png"}]
    )
    assert await employee_owns_media(
        db,
        employee_id="EMP-2",
        field="signature_url",
        expected_url="/api/documents/signatures/old.png",
        filename="old.png",
    )


@pytest.mark.asyncio
async def test_employee_owns_media_returns_false_for_other_employee():
    db = _FakeProfileDb(
        read_rows=[{"employee_id": "EMP-1", "photo_url": "/api/documents/photos/abc.jpg"}]
    )
    assert not await employee_owns_media(
        db,
        employee_id="EMP-2",
        field="photo_url",
        expected_url="/api/documents/photos/abc.jpg",
        filename="abc.jpg",
    )


def test_employee_owns_media_rejects_unknown_field():
    with pytest.raises(ValueError):
        # Sync call — function returns a coroutine but raises before awaiting.
        import asyncio
        asyncio.run(
            employee_owns_media(
                _FakeProfileDb(),
                employee_id="EMP-1",
                field="profile_pdf",  # not allowed
                expected_url="/whatever",
            )
        )


# ── 1.6 Current-user subject accessors ──────────────────────────────


@pytest.mark.asyncio
async def test_get_subject_document_for_current_user_rejects_anonymous_principal():
    with pytest.raises(HTTPException) as exc:
        await get_subject_document_for_current_user(
            "file.pdf",
            current_user={"sub": "u1"},  # no employee_id/code
            db=None,
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_download_subject_document_for_current_user_rejects_anonymous_principal():
    with pytest.raises(HTTPException) as exc:
        await download_subject_document_for_current_user(
            "file.pdf",
            current_user={"sub": "u1"},
            db=None,
        )
    assert exc.value.status_code == 403
