from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest
from fastapi.responses import Response

from contexts.documents.infrastructure import metadata_ops, storage_ops
from contexts.documents.infrastructure.storage import (
    DocumentStorage,
    ResilientDocumentStorage,
    StorageBucket,
    StorageObjectStat,
)


@dataclass
class _FakeStorage(DocumentStorage):
    names: list[str]
    fail_exists: bool = False
    fail_write: bool = False
    fail_list: bool = False
    fail_delete: bool = False
    writes: list[tuple[StorageBucket, str, bytes]] | None = None
    deleted: list[str] | None = None

    def exists(self, bucket: StorageBucket, filename: str) -> bool:
        if self.fail_exists:
            raise RuntimeError("exists failed")
        return filename in self.names

    def write_bytes(self, bucket: StorageBucket, filename: str, contents: bytes, *, content_type: str | None = None) -> None:
        if self.fail_write:
            raise RuntimeError("write failed")
        self.names.append(filename)
        if self.writes is not None:
            self.writes.append((bucket, filename, contents))

    def delete(self, bucket: StorageBucket, filename: str) -> None:
        if self.fail_delete:
            raise RuntimeError("delete failed")
        if filename in self.names:
            self.names.remove(filename)
        if self.deleted is not None:
            self.deleted.append(filename)

    def read_bytes(self, bucket: StorageBucket, filename: str) -> bytes:
        return b""

    def list_names(self, bucket: StorageBucket) -> list[str]:
        if self.fail_list:
            raise RuntimeError("list failed")
        return list(self.names)

    def stat(self, bucket: StorageBucket, filename: str) -> StorageObjectStat:
        return StorageObjectStat(filename=filename, size=3, modified_at=datetime.now(timezone.utc))

    def inline_response(self, bucket: StorageBucket, filename: str, *, media_type: str) -> Response:
        return Response(content=f"inline:{filename}", media_type=media_type)

    def download_response(self, bucket: StorageBucket, filename: str, *, media_type: str) -> Response:
        return Response(content=f"download:{filename}", media_type=media_type)


def test_resilient_storage_falls_back_on_write_failure() -> None:
    primary = _FakeStorage(names=[], fail_write=True, writes=[])
    fallback = _FakeStorage(names=[], writes=[])
    storage = ResilientDocumentStorage(primary=primary, fallback=fallback)

    storage.write_bytes(StorageBucket.DOCUMENT, "file.pdf", b"pdf")

    assert fallback.writes == [(StorageBucket.DOCUMENT, "file.pdf", b"pdf")]


def test_resilient_storage_unions_list_results_when_primary_listing_fails() -> None:
    primary = _FakeStorage(names=["primary.pdf"], fail_list=True)
    fallback = _FakeStorage(names=["fallback.pdf"])
    storage = ResilientDocumentStorage(primary=primary, fallback=fallback)

    assert storage.list_names(StorageBucket.DOCUMENT) == ["fallback.pdf"]


def test_resilient_storage_reads_from_fallback_when_primary_is_unavailable() -> None:
    primary = _FakeStorage(names=[], fail_exists=True)
    fallback = _FakeStorage(names=["fallback.pdf"])
    storage = ResilientDocumentStorage(primary=primary, fallback=fallback)

    response = storage.inline_response(
        StorageBucket.DOCUMENT,
        "fallback.pdf",
        media_type="application/pdf",
    )

    assert response.body == b"inline:fallback.pdf"


class _FakeUploadFile:
    filename = "order.pdf"
    content_type = "application/pdf"

    async def read(self) -> bytes:
        return b"%PDF-1.4\n%test\n"


@pytest.mark.asyncio
async def test_upload_document_deletes_file_when_metadata_write_fails(monkeypatch) -> None:
    fake_storage = _FakeStorage(names=[], deleted=[])

    async def fail_write_metadata(*args, **kwargs):
        raise RuntimeError("metadata unavailable")

    monkeypatch.setattr(storage_ops, "storage", lambda: fake_storage)
    monkeypatch.setattr(metadata_ops, "write_document_metadata", fail_write_metadata)

    with pytest.raises(RuntimeError, match="metadata unavailable"):
        await storage_ops.upload_document(
            _FakeUploadFile(),
            current_user={"sub": "user-1"},
            db=object(),
        )

    assert fake_storage.names == []
    assert fake_storage.deleted