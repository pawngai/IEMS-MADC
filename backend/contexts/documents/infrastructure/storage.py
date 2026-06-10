from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from fastapi.responses import FileResponse, Response
from contexts.documents.domain.validation import validate_safe_filename


class StorageBucket(str, Enum):
    PHOTO = "photo"
    SIGNATURE = "signature"
    DOCUMENT = "document"
    ARCHIVE = "archive"
    PREVIEW = "preview"


@dataclass(frozen=True)
class StorageObjectStat:
    filename: str
    size: int
    modified_at: datetime


class DocumentStorage(ABC):
    @abstractmethod
    def exists(self, bucket: StorageBucket, filename: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def write_bytes(
        self,
        bucket: StorageBucket,
        filename: str,
        contents: bytes,
        *,
        content_type: str | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, bucket: StorageBucket, filename: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def read_bytes(self, bucket: StorageBucket, filename: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def list_names(self, bucket: StorageBucket) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def stat(self, bucket: StorageBucket, filename: str) -> StorageObjectStat:
        raise NotImplementedError

    @abstractmethod
    def inline_response(
        self,
        bucket: StorageBucket,
        filename: str,
        *,
        media_type: str,
    ) -> Response:
        raise NotImplementedError

    @abstractmethod
    def download_response(
        self,
        bucket: StorageBucket,
        filename: str,
        *,
        media_type: str,
    ) -> Response:
        raise NotImplementedError


@dataclass(frozen=True)
class LocalDocumentStorage(DocumentStorage):
    photo_dir: Path
    signature_dir: Path
    document_dir: Path
    archive_dir: Path | None = None
    preview_dir: Path | None = None

    def __post_init__(self) -> None:
        self.photo_dir.mkdir(parents=True, exist_ok=True)
        self.signature_dir.mkdir(parents=True, exist_ok=True)
        self.document_dir.mkdir(parents=True, exist_ok=True)
        if self.archive_dir is not None:
            self.archive_dir.mkdir(parents=True, exist_ok=True)
        if self.preview_dir is not None:
            self.preview_dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, bucket: StorageBucket, filename: str) -> Path:
        return validate_safe_filename(filename, self._base_dir(bucket))

    def exists(self, bucket: StorageBucket, filename: str) -> bool:
        return self.path_for(bucket, filename).exists()

    def write_bytes(
        self,
        bucket: StorageBucket,
        filename: str,
        contents: bytes,
        *,
        content_type: str | None = None,
    ) -> None:
        file_path = self.path_for(bucket, filename)
        file_path.write_bytes(contents)

    def delete(self, bucket: StorageBucket, filename: str) -> None:
        file_path = self.path_for(bucket, filename)
        if file_path.exists():
            file_path.unlink()

    def read_bytes(self, bucket: StorageBucket, filename: str) -> bytes:
        return self.path_for(bucket, filename).read_bytes()

    def list_names(self, bucket: StorageBucket) -> list[str]:
        base_dir = self._base_dir(bucket)
        return [path.name for path in base_dir.iterdir() if path.is_file() and path.parent == base_dir]

    def stat(self, bucket: StorageBucket, filename: str) -> StorageObjectStat:
        file_path = self.path_for(bucket, filename)
        stat = file_path.stat()
        return StorageObjectStat(
            filename=filename,
            size=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        )

    def inline_response(
        self,
        bucket: StorageBucket,
        filename: str,
        *,
        media_type: str,
    ) -> Response:
        file_path = self.path_for(bucket, filename)
        return FileResponse(path=file_path, media_type=media_type, filename=filename)

    def download_response(
        self,
        bucket: StorageBucket,
        filename: str,
        *,
        media_type: str,
    ) -> Response:
        file_path = self.path_for(bucket, filename)
        return FileResponse(path=file_path, media_type=media_type, filename=filename)

    def _base_dir(self, bucket: StorageBucket) -> Path:
        if bucket == StorageBucket.PHOTO:
            return self.photo_dir
        if bucket == StorageBucket.SIGNATURE:
            return self.signature_dir
        if bucket == StorageBucket.ARCHIVE:
            # Fall back to a sibling directory if the archive bucket wasn't
            # explicitly wired (legacy callers expect the three-bucket
            # constructor).
            return self.archive_dir or (self.document_dir.parent / "archive")
        if bucket == StorageBucket.PREVIEW:
            return self.preview_dir or (self.document_dir.parent / "previews")
        return self.document_dir


@dataclass(frozen=True)
class GcsDocumentStorage(DocumentStorage):
    bucket_name: str
    project_id: str = ""

    def exists(self, bucket: StorageBucket, filename: str) -> bool:
        return self._blob(bucket, filename).exists()

    def write_bytes(
        self,
        bucket: StorageBucket,
        filename: str,
        contents: bytes,
        *,
        content_type: str | None = None,
    ) -> None:
        blob = self._blob(bucket, filename)
        blob.upload_from_string(contents, content_type=content_type)

    def delete(self, bucket: StorageBucket, filename: str) -> None:
        blob = self._blob(bucket, filename)
        if blob.exists():
            blob.delete()

    def read_bytes(self, bucket: StorageBucket, filename: str) -> bytes:
        return self._blob(bucket, filename).download_as_bytes()

    def list_names(self, bucket: StorageBucket) -> list[str]:
        prefix = self._prefix(bucket)
        blobs = self._bucket().list_blobs(prefix=f"{prefix}/")
        names: list[str] = []
        for blob in blobs:
            parts = blob.name.split("/", 1)
            if len(parts) == 2 and parts[1]:
                names.append(parts[1])
        return names

    def stat(self, bucket: StorageBucket, filename: str) -> StorageObjectStat:
        blob = self._blob(bucket, filename)
        blob.reload()
        updated = blob.updated or datetime.now(timezone.utc)
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        return StorageObjectStat(
            filename=filename,
            size=int(blob.size or 0),
            modified_at=updated,
        )

    def inline_response(
        self,
        bucket: StorageBucket,
        filename: str,
        *,
        media_type: str,
    ) -> Response:
        blob = self._blob(bucket, filename)
        data = blob.download_as_bytes()
        return Response(content=data, media_type=media_type)

    def download_response(
        self,
        bucket: StorageBucket,
        filename: str,
        *,
        media_type: str,
    ) -> Response:
        blob = self._blob(bucket, filename)
        data = blob.download_as_bytes()
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return Response(content=data, media_type=media_type, headers=headers)

    def _blob(self, bucket: StorageBucket, filename: str):
        safe_filename = self._validate_filename(filename)
        return self._bucket().blob(f"{self._prefix(bucket)}/{safe_filename}")

    def _bucket(self):
        from google.cloud import storage

        client = storage.Client(project=self.project_id or None)
        return client.bucket(self.bucket_name)

    def _prefix(self, bucket: StorageBucket) -> str:
        if bucket == StorageBucket.PHOTO:
            return "photos"
        if bucket == StorageBucket.SIGNATURE:
            return "signatures"
        if bucket == StorageBucket.ARCHIVE:
            return "archive"
        if bucket == StorageBucket.PREVIEW:
            return "previews"
        return "documents"

    def _validate_filename(self, filename: str) -> str:
        if "/" in filename or "\\" in filename or ".." in filename:
            raise ValueError("Invalid filename")
        return filename


@dataclass(frozen=True)
class ResilientDocumentStorage(DocumentStorage):
    primary: DocumentStorage
    fallback: DocumentStorage

    def exists(self, bucket: StorageBucket, filename: str) -> bool:
        try:
            if self.primary.exists(bucket, filename):
                return True
        except Exception:
            pass
        return self.fallback.exists(bucket, filename)

    def write_bytes(
        self,
        bucket: StorageBucket,
        filename: str,
        contents: bytes,
        *,
        content_type: str | None = None,
    ) -> None:
        try:
            self.primary.write_bytes(bucket, filename, contents, content_type=content_type)
            return
        except Exception:
            # Partial primary write could leave a stub blob behind that the
            # read path would then prefer over the (correct) fallback. Try to
            # remove it before falling back; ignore secondary failures here so
            # the original write error path still completes.
            try:
                self.primary.delete(bucket, filename)
            except Exception:
                pass
            self.fallback.write_bytes(bucket, filename, contents, content_type=content_type)

    def write_health(self, bucket: StorageBucket, filename: str) -> dict[str, Any]:
        """Diagnostic check for split-state divergence between primary and
        fallback. Returns ``{"split_state": True, ...}`` if the same object
        exists in both stores with different size or modified time. Intended
        for a periodic reconciliation job, not the request path."""
        primary_exists = self._safe_exists(self.primary, bucket, filename)
        fallback_exists = self._safe_exists(self.fallback, bucket, filename)
        if not (primary_exists and fallback_exists):
            return {"split_state": False, "primary_exists": primary_exists, "fallback_exists": fallback_exists}

        try:
            primary_stat = self.primary.stat(bucket, filename)
            fallback_stat = self.fallback.stat(bucket, filename)
        except Exception:
            return {"split_state": True, "reason": "stat_failure"}

        diverged = (
            primary_stat.size != fallback_stat.size
            or primary_stat.modified_at != fallback_stat.modified_at
        )
        return {
            "split_state": diverged,
            "primary_size": primary_stat.size,
            "fallback_size": fallback_stat.size,
            "primary_modified_at": primary_stat.modified_at,
            "fallback_modified_at": fallback_stat.modified_at,
        }

    @staticmethod
    def _safe_exists(store: DocumentStorage, bucket: StorageBucket, filename: str) -> bool:
        try:
            return store.exists(bucket, filename)
        except Exception:
            return False

    def delete(self, bucket: StorageBucket, filename: str) -> None:
        primary_error: Exception | None = None
        try:
            if self.primary.exists(bucket, filename):
                self.primary.delete(bucket, filename)
        except Exception as exc:
            primary_error = exc

        try:
            if self.fallback.exists(bucket, filename):
                self.fallback.delete(bucket, filename)
                return
        except Exception:
            if primary_error is not None:
                raise primary_error
            raise

        if primary_error is not None:
            raise primary_error

    def read_bytes(self, bucket: StorageBucket, filename: str) -> bytes:
        return self._storage_for_read(bucket, filename).read_bytes(bucket, filename)

    def list_names(self, bucket: StorageBucket) -> list[str]:
        names: set[str] = set()
        try:
            names.update(self.primary.list_names(bucket))
        except Exception:
            pass
        names.update(self.fallback.list_names(bucket))
        return sorted(names)

    def stat(self, bucket: StorageBucket, filename: str) -> StorageObjectStat:
        return self._storage_for_read(bucket, filename).stat(bucket, filename)

    def inline_response(
        self,
        bucket: StorageBucket,
        filename: str,
        *,
        media_type: str,
    ) -> Response:
        return self._storage_for_read(bucket, filename).inline_response(
            bucket,
            filename,
            media_type=media_type,
        )

    def download_response(
        self,
        bucket: StorageBucket,
        filename: str,
        *,
        media_type: str,
    ) -> Response:
        return self._storage_for_read(bucket, filename).download_response(
            bucket,
            filename,
            media_type=media_type,
        )

    def _storage_for_read(self, bucket: StorageBucket, filename: str) -> DocumentStorage:
        try:
            if self.primary.exists(bucket, filename):
                return self.primary
        except Exception:
            pass
        return self.fallback