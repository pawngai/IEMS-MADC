import os
import sys
from dataclasses import dataclass

import pytest
from fastapi import HTTPException
from fastapi.responses import FileResponse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contexts.documents.infrastructure import service as service
from contexts.documents.infrastructure import paths as _doc_paths
from contexts.documents.infrastructure import event_publish as _event_publish_mod
from contexts.documents.infrastructure import lock_ops as _lock_ops_mod
from contexts.documents.infrastructure import storage_ops as _storage_ops_mod
from contexts.documents.infrastructure import query as _query_mod
from contexts.documents.application import commands as _commands_mod
from contexts.documents.domain import validation
from contexts.documents.infrastructure.storage import StorageBucket
from contexts.identity_access.rbac.policies.operational import require_document_delete_permission
from app_platform.event_bus.types import EventName


def test_document_entity_type_allows_service_record_alias() -> None:
    assert validation.normalize_document_entity_type("service-record") == "SERVICE_RECORD"


@dataclass
class _FakeUploadFile:
    filename: str
    _contents: bytes
    content_type: str

    async def read(self) -> bytes:
        return self._contents


class _FakeProfileCollection:
    def __init__(self, rows):
        self.rows = list(rows)

    async def find_one(self, query, projection=None):
        for row in self.rows:
            if row.get("employee_id") != query.get("employee_id"):
                continue
            values = query.get("$or") or []
            if any(row.get(next(iter(item))) == next(iter(item.values())) for item in values):
                return row
        return None


class _FakeMediaDb:
    def __init__(self, rows):
        self.employee_profile_read_models = _FakeProfileCollection(rows)
        self.employee_profile_extensions = _FakeProfileCollection([])


@pytest.fixture
def isolated_document_store(tmp_path, monkeypatch):
    documents_dir = tmp_path / "documents"
    metadata_dir = documents_dir / "_meta"
    documents_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    # Patch the single canonical source; service.__getattr__ proxies reads here.
    monkeypatch.setattr(_doc_paths, "DOCUMENT_DIR", documents_dir)
    monkeypatch.setattr(_doc_paths, "DOCUMENT_META_DIR", metadata_dir)

    return documents_dir


@pytest.mark.asyncio
async def test_owner_can_download_own_document(isolated_document_store):
    filename = "owner-file.pdf"
    file_path = isolated_document_store / filename
    file_path.write_bytes(b"%PDF-1.4\nowner")

    await service._write_document_metadata(filename, {"uploaded_employee_id": "EMP-001"})

    response = await service.download_document(
        filename,
        current_user={
            "sub": "user-owner",
            "employee_id": "EMP-001",
            "authorities": ["EMPLOYEE"],
        },
    )

    assert isinstance(response, FileResponse)


@pytest.mark.asyncio
async def test_non_owner_cannot_download_document(isolated_document_store):
    filename = "owner-file.pdf"
    file_path = isolated_document_store / filename
    file_path.write_bytes(b"%PDF-1.4\nowner")

    await service._write_document_metadata(filename, {"uploaded_employee_id": "EMP-001"})

    with pytest.raises(HTTPException) as exc:
        await service.download_document(
            filename,
            current_user={
                "sub": "user-other",
                "employee_id": "EMP-999",
                "authorities": ["EMPLOYEE"],
            },
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_subject_owner_can_download_document_about_self(isolated_document_store):
    filename = "subject-file.pdf"
    file_path = isolated_document_store / filename
    file_path.write_bytes(b"%PDF-1.4\nsubject")

    await service._write_document_metadata(
        filename,
        {
            "uploaded_employee_id": "EMP-UPLOADER",
            "subject_employee_id": "EMP-001",
            "subject_employee_code": "MADC-2024-0001",
        },
    )

    response = await service.download_subject_document(
        filename,
        employee_id="EMP-001",
        employee_code="MADC-2024-0001",
    )

    assert isinstance(response, FileResponse)


@pytest.mark.asyncio
async def test_subject_owner_can_open_document_about_self(isolated_document_store):
    filename = "subject-file.pdf"
    file_path = isolated_document_store / filename
    file_path.write_bytes(b"%PDF-1.4\nsubject")

    await service._write_document_metadata(
        filename,
        {
            "uploaded_employee_id": "EMP-UPLOADER",
            "subject_employee_id": "EMP-001",
            "subject_employee_code": "MADC-2024-0001",
        },
    )

    response = await service.get_subject_document(
        filename,
        employee_id="EMP-001",
        employee_code="MADC-2024-0001",
    )

    assert isinstance(response, FileResponse)


@pytest.mark.asyncio
async def test_non_subject_owner_cannot_download_document_about_other_employee(isolated_document_store):
    filename = "subject-file.pdf"
    file_path = isolated_document_store / filename
    file_path.write_bytes(b"%PDF-1.4\nsubject")

    await service._write_document_metadata(
        filename,
        {
            "uploaded_employee_id": "EMP-UPLOADER",
            "subject_employee_id": "EMP-001",
            "subject_employee_code": "MADC-2024-0001",
        },
    )

    with pytest.raises(HTTPException) as exc:
        await service.download_subject_document(
            filename,
            employee_id="EMP-999",
            employee_code="MADC-2024-0999",
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_subject_list_documents_only_returns_documents_about_employee(isolated_document_store):
    own_filename = "subject-own.pdf"
    other_filename = "subject-other.pdf"
    (isolated_document_store / own_filename).write_bytes(b"%PDF-1.4\nown")
    (isolated_document_store / other_filename).write_bytes(b"%PDF-1.4\nother")

    await service._write_document_metadata(
        own_filename,
        {
            "subject_employee_id": "EMP-001",
            "subject_employee_code": "MADC-2024-0001",
            "document_type": "ORDER",
        },
    )
    await service._write_document_metadata(
        other_filename,
        {
            "subject_employee_id": "EMP-002",
            "subject_employee_code": "MADC-2024-0002",
            "document_type": "ORDER",
        },
    )

    result = await service.list_subject_documents(
        employee_id="EMP-001",
        employee_code="MADC-2024-0001",
        document_type="order",
    )

    assert result["success"] is True
    assert result["total"] == 1
    assert [item["filename"] for item in result["items"]] == [own_filename]


@pytest.mark.asyncio
async def test_active_employee_role_cannot_bypass_document_ownership(isolated_document_store):
    filename = "owner-file.pdf"
    file_path = isolated_document_store / filename
    file_path.write_bytes(b"%PDF-1.4\nowner")

    await service._write_document_metadata(filename, {"uploaded_employee_id": "EMP-001"})

    with pytest.raises(HTTPException) as exc:
        await service.download_document(
            filename,
            current_user={
                "sub": "user-other",
                "employee_id": "EMP-999",
                "authorities": ["EMPLOYEE", "DEPT_DATA_ENTRY"],
                "active_role": "EMPLOYEE",
            },
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_privileged_can_download_without_metadata(isolated_document_store):
    filename = "fallback-file.pdf"
    file_path = isolated_document_store / filename
    file_path.write_bytes(b"%PDF-1.4\nfallback")

    response = await service.download_document(
        filename,
        current_user={"sub": "admin-user", "authorities": ["SYSTEM_ADMIN"]},
    )

    assert isinstance(response, FileResponse)


@pytest.mark.asyncio
async def test_owner_metadata_grants_download_access(isolated_document_store):
    filename = "owner-file.pdf"
    file_path = isolated_document_store / filename
    file_path.write_bytes(b"%PDF-1.4\nowner")

    await service._write_document_metadata(filename, {"uploaded_by_user_id": "owner-user-id"})

    response = await service.download_document(
        filename,
        current_user={"sub": "owner-user-id", "authorities": ["EMPLOYEE"]},
    )

    assert isinstance(response, FileResponse)


@pytest.mark.asyncio
async def test_legacy_uploaded_by_alias_no_longer_grants_access(isolated_document_store):
    """The legacy ``uploaded_by`` alias was dropped — rows stored under it
    after migration should already have ``uploaded_by_user_id`` set. Defensive
    check: an unmigrated row carrying only ``uploaded_by`` is *not* recognised
    as owner-accessible, so the migration must run before deploy."""
    filename = "legacy-alias-file.pdf"
    file_path = isolated_document_store / filename
    file_path.write_bytes(b"%PDF-1.4\nlegacy")

    await service._write_document_metadata(filename, {"uploaded_by": "legacy-user-id"})

    with pytest.raises(HTTPException) as exc:
        await service.download_document(
            filename,
            current_user={"sub": "legacy-user-id", "authorities": ["EMPLOYEE"]},
        )
    assert exc.value.status_code == 403


def test_cross_type_employee_id_code_match_does_not_grant_ownership():
    current_user_by_id = {"sub": "user-1", "employee_id": "EMP-001"}
    metadata_by_code = {"uploaded_employee_code": "EMP-001"}

    current_user_by_code = {"sub": "user-2", "employee_code": "EMP-001"}
    metadata_by_id = {"uploaded_employee_id": "EMP-001"}

    assert validation.is_document_owner(metadata_by_code, current_user_by_id) is False
    assert validation.is_document_owner(metadata_by_id, current_user_by_code) is False


@pytest.mark.asyncio
async def test_approved_document_cannot_be_deleted(isolated_document_store):
    filename = "approved-file.pdf"
    file_path = isolated_document_store / filename
    file_path.write_bytes(b"%PDF-1.4\napproved")

    await service._write_document_metadata(
        filename,
        {
            "uploaded_employee_id": "EMP-001",
            "is_locked": True,
            "lock_reason": "APPROVED_CHANGE_REQUEST",
        },
    )

    with pytest.raises(HTTPException) as exc:
        await service.delete_document(
            filename,
            current_user={"sub": "admin-user", "authorities": ["SYSTEM_ADMIN"]},
        )

    assert exc.value.status_code == 400
    assert exc.value.detail["error_code"] == "DOCUMENT_LOCKED"
    assert exc.value.detail["message"] == "Locked documents are immutable and cannot be deleted"
    assert exc.value.detail["document_id"] == filename
    assert exc.value.detail["filename"] == filename
    assert exc.value.detail["lock_reason"] == "APPROVED_CHANGE_REQUEST"


@pytest.mark.asyncio
async def test_lock_documents_for_approved_request_marks_metadata(isolated_document_store):
    filename = "to-lock.pdf"
    file_path = isolated_document_store / filename
    file_path.write_bytes(b"%PDF-1.4\nlock")

    await service._write_document_metadata(
        filename,
        {
            "uploaded_employee_id": "EMP-001",
        },
    )

    await service.lock_documents_for_approved_request(
        [{"filename": filename}],
        request_id="CR-LOCK001",
        status="APPLIED",
    )

    meta = await service._read_document_metadata(filename)
    assert meta is not None
    assert meta.get("is_locked") is True
    assert meta.get("locked_by_request_id") == "CR-LOCK001"


@pytest.mark.asyncio
async def test_lock_documents_for_approved_request_emits_document_locked_event(isolated_document_store, monkeypatch):
    filename = "to-lock-event.pdf"
    file_path = isolated_document_store / filename
    file_path.write_bytes(b"%PDF-1.4\nlock-event")

    await service._write_document_metadata(
        filename,
        {
            "document_id": filename,
            "uploaded_employee_id": "EMP-001",
            "uploaded_employee_code": "MADC-2024-0001",
            "subject_employee_id": "EMP-010",
            "subject_employee_code": "MADC-2024-0010",
        },
    )

    published: list[dict] = []

    async def _fake_publish_document_event(**kwargs):
        published.append(kwargs)

    monkeypatch.setattr(_lock_ops_mod, "publish_document_event", _fake_publish_document_event)

    await service.lock_documents_for_approved_request(
        [{"filename": filename}],
        request_id="CR-LOCK-EVENT-001",
        status="APPROVED",
    )

    assert len(published) == 1
    assert published[0]["name"] == EventName.DOCUMENT_LOCKED.value
    assert published[0]["payload"]["document_id"] == filename
    assert published[0]["payload"]["locked_by_request_id"] == "CR-LOCK-EVENT-001"
    assert published[0]["payload"]["uploaded_employee_id"] == "EMP-001"
    assert published[0]["payload"]["subject_employee_id"] == "EMP-010"
    assert published[0]["payload"]["subject_employee_code"] == "MADC-2024-0010"


@pytest.mark.asyncio
async def test_lock_documents_for_approved_request_uses_active_storage_backend(monkeypatch):
    filename = "gcs-lock.pdf"

    class FakeStorage:
        def exists(self, bucket, candidate_filename):
            return bucket == StorageBucket.DOCUMENT and candidate_filename == filename

    monkeypatch.setattr(_lock_ops_mod, "storage", lambda: FakeStorage())

    await service._write_document_metadata(
        filename,
        {
            "uploaded_employee_id": "EMP-001",
        },
    )

    await service.lock_documents_for_approved_request(
        [{"filename": filename}],
        request_id="CR-GCS-LOCK001",
        status="APPROVED",
    )

    meta = await service._read_document_metadata(filename)
    assert meta is not None
    assert meta.get("is_locked") is True
    assert meta.get("locked_by_request_id") == "CR-GCS-LOCK001"


@pytest.mark.asyncio
async def test_lock_documents_for_approved_request_supports_custom_statuses_and_reason(isolated_document_store):
    filename = "leave-lock.pdf"
    file_path = isolated_document_store / filename
    file_path.write_bytes(b"%PDF-1.4\nleave-lock")

    await service._write_document_metadata(
        filename,
        {
            "uploaded_employee_id": "EMP-001",
        },
    )

    await service.lock_documents_for_approved_request(
        [{"filename": filename}],
        request_id="LV-LOCK-001",
        status="SANCTIONED",
        lock_reason="LEAVE_WORKFLOW_FINALIZED",
        allowed_statuses={"SANCTIONED", "REJECTED"},
    )

    meta = await service._read_document_metadata(filename)
    assert meta is not None
    assert meta.get("is_locked") is True
    assert meta.get("lock_reason") == "LEAVE_WORKFLOW_FINALIZED"
    assert meta.get("locked_status") == "SANCTIONED"
    assert meta.get("locked_by_request_id") == "LV-LOCK-001"


@pytest.mark.asyncio
async def test_attach_document_to_entity_emits_document_uploaded_event(isolated_document_store, monkeypatch):
    published: list[dict] = []

    async def _fake_publish_document_event(**kwargs):
        published.append(kwargs)

    async def _fake_resolve_subject_employee_metadata(metadata, *, db=None):
        assert metadata["subject_employee_code"] == "MADC-2024-0002"
        return {
            "subject_employee_id": "EMP-002",
            "subject_employee_code": "MADC-2024-0002",
        }

    monkeypatch.setattr(_event_publish_mod, "publish_document_event", _fake_publish_document_event)
    monkeypatch.setattr(_commands_mod, "_resolve_subject_employee", _fake_resolve_subject_employee_metadata)

    result = await _commands_mod.attach_document_to_entity(
        file=_FakeUploadFile(
            filename="appointment-order.pdf",
            _contents=b"%PDF-1.4\nupload-event",
            content_type="application/pdf",
        ),
        current_user={
            "sub": "user-123",
            "employee_id": "EMP-001",
            "employee_code": "MADC-2024-0001",
            "department_code": "FIN",
        },
        metadata={
            "entity_type": "CHANGE_REQUEST",
            "entity_id": "CR-100",
            "document_type": "order",
            "source_context": "change requests.upload",
            "subject_employee_code": "MADC-2024-0002",
        },
    )

    assert result["document_id"]  # stable UUID, distinct from filename
    assert result["filename"]
    assert result["document_id"] != result["filename"]  # UUID != timestamped filename
    assert result["metadata"]["entity_type"] == "CHANGE_REQUEST"
    assert result["metadata"]["entity_id"] == "CR-100"
    assert result["metadata"]["document_type"] == "ORDER"
    assert result["metadata"]["source_context"] == "change_requests.upload"
    assert result["metadata"]["subject_employee_id"] == "EMP-002"
    assert result["metadata"]["subject_employee_code"] == "MADC-2024-0002"

    # Three events: scan-completed (always fires on upload), metadata-updated,
    # and document-uploaded.
    assert len(published) == 3
    assert any(item["name"] == EventName.DOCUMENT_SCAN_COMPLETED.value for item in published)

    metadata_updated = next(item for item in published if item["name"] == EventName.DOCUMENT_METADATA_UPDATED.value)
    uploaded_event = next(item for item in published if item["name"] == EventName.DOCUMENT_UPLOADED.value)

    assert metadata_updated["payload"]["document_id"] == result["document_id"]
    assert metadata_updated["payload"]["entity_type"] == "CHANGE_REQUEST"
    assert metadata_updated["payload"]["entity_id"] == "CR-100"
    assert metadata_updated["payload"]["document_type"] == "ORDER"
    assert metadata_updated["payload"]["source_context"] == "change_requests.upload"
    assert metadata_updated["payload"]["subject_employee_id"] == "EMP-002"
    assert metadata_updated["payload"]["subject_employee_code"] == "MADC-2024-0002"
    assert metadata_updated["payload"]["updated_fields"] == [
        "document_type",
        "entity_id",
        "entity_type",
        "source_context",
        "subject_employee_code",
        "subject_employee_id",
    ]
    assert metadata_updated["actor_id"] == "user-123"
    assert metadata_updated["department_id"] == "FIN"

    assert uploaded_event["payload"]["document_id"] == result["document_id"]
    assert uploaded_event["payload"]["entity_type"] == "CHANGE_REQUEST"
    assert uploaded_event["payload"]["entity_id"] == "CR-100"
    assert uploaded_event["payload"]["document_type"] == "ORDER"
    assert uploaded_event["payload"]["source_context"] == "change_requests.upload"
    assert uploaded_event["payload"]["subject_employee_id"] == "EMP-002"
    assert uploaded_event["payload"]["subject_employee_code"] == "MADC-2024-0002"
    assert uploaded_event["actor_id"] == "user-123"
    assert uploaded_event["department_id"] == "FIN"


@pytest.mark.asyncio
async def test_resolve_subject_employee_metadata_rejects_unknown_subject_code(monkeypatch):
    async def _fake_resolve_identity_ref(db, *, ref, projection=None):
        assert ref == "MADC-2099-9999"
        return None

    monkeypatch.setattr(_commands_mod, "resolve_identity_ref", _fake_resolve_identity_ref)

    with pytest.raises(HTTPException) as exc:
        await _commands_mod._resolve_subject_employee(
            {"subject_employee_code": "MADC-2099-9999"},
            db=object(),
        )

    assert exc.value.status_code == 422
    assert exc.value.detail["error_code"] == "DOCUMENT_SUBJECT_EMPLOYEE_INVALID"
    assert exc.value.detail["subject_employee_code"] == "MADC-2099-9999"


@pytest.mark.asyncio
async def test_non_owner_cannot_attach_document_to_other_change_request(monkeypatch):
    async def _fake_get_change_request_by_id(_db, *, request_id, projection=None):
        assert request_id == "CR-OTHER"
        return {"request_id": request_id, "employee_id": "EMP-OTHER"}

    import contexts.change_requests.contracts.change_request_directory as change_request_directory

    monkeypatch.setattr(
        change_request_directory,
        "get_change_request_by_id",
        _fake_get_change_request_by_id,
    )

    with pytest.raises(HTTPException) as exc:
        await _commands_mod._validate_entity_access(
            "CHANGE_REQUEST",
            "CR-OTHER",
            current_user={"sub": "user-1", "employee_id": "EMP-SELF", "authorities": ["EMPLOYEE"]},
            db=object(),
        )

    assert exc.value.status_code == 403
    assert exc.value.detail["error_code"] == "DOCUMENT_ENTITY_ACCESS_DENIED"


@pytest.mark.asyncio
async def test_non_owner_cannot_open_employee_photo(isolated_document_store):
    photo_dir = _doc_paths.PHOTO_DIR
    photo_dir.mkdir(parents=True, exist_ok=True)
    filename = "profile-photo.png"
    (photo_dir / filename).write_bytes(b"\x89PNG\r\n\x1a\nphoto")

    db = _FakeMediaDb([{"employee_id": "EMP-001", "photo_url": f"/api/documents/photos/{filename}"}])

    with pytest.raises(HTTPException) as exc:
        await service.get_photo(
            filename,
            current_user={"sub": "user-other", "employee_id": "EMP-999", "authorities": ["EMPLOYEE"]},
            db=db,
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_owner_can_open_own_employee_photo(isolated_document_store):
    photo_dir = _doc_paths.PHOTO_DIR
    photo_dir.mkdir(parents=True, exist_ok=True)
    filename = "profile-photo.png"
    (photo_dir / filename).write_bytes(b"\x89PNG\r\n\x1a\nphoto")

    db = _FakeMediaDb([{"employee_id": "EMP-001", "photo_url": f"/api/documents/photos/{filename}"}])

    response = await service.get_photo(
        filename,
        current_user={"sub": "user-owner", "employee_id": "EMP-001", "authorities": ["EMPLOYEE"]},
        db=db,
    )

    assert isinstance(response, FileResponse)


@pytest.mark.asyncio
async def test_owner_can_attach_document_to_own_leave(monkeypatch):
    async def _fake_get_leave_application_by_id(_db, *, leave_id):
        assert leave_id == "LV-SELF"
        return {"id": leave_id, "employee_id": "EMP-SELF"}

    import contexts.leave_attendance.contracts.leave_directory as leave_directory

    monkeypatch.setattr(
        leave_directory,
        "get_leave_application_by_id",
        _fake_get_leave_application_by_id,
    )

    await _commands_mod._validate_entity_access(
        "LEAVE",
        "LV-SELF",
        current_user={"sub": "user-1", "employee_id": "EMP-SELF", "authorities": ["EMPLOYEE"]},
        db=object(),
    )


@pytest.mark.asyncio
async def test_delete_document_emits_document_deleted_event(isolated_document_store, monkeypatch):
    filename = "delete-me.pdf"
    file_path = isolated_document_store / filename
    file_path.write_bytes(b"%PDF-1.4\ndelete-me")

    await service._write_document_metadata(
        filename,
        {
            "document_id": filename,
            "original_name": "delete-me-original.pdf",
            "uploaded_employee_id": "EMP-001",
            "uploaded_employee_code": "MADC-2024-0001",
            "subject_employee_id": "EMP-010",
            "subject_employee_code": "MADC-2024-0010",
            "document_type": "REPORT",
            "source_context": "change_requests.review",
        },
    )

    published: list[dict] = []

    async def _fake_publish_document_event(**kwargs):
        published.append(kwargs)

    monkeypatch.setattr(_event_publish_mod, "publish_document_event", _fake_publish_document_event)

    result = await service.delete_document(
        filename,
        current_user={
            "sub": "admin-user",
            "authorities": ["SYSTEM_ADMIN"],
            "department_code": "FIN",
        },
    )

    assert result["success"] is True
    assert len(published) == 1
    assert published[0]["name"] == EventName.DOCUMENT_DELETED.value
    assert published[0]["payload"]["document_id"] == filename
    assert published[0]["payload"]["original_name"] == "delete-me-original.pdf"
    assert published[0]["payload"]["deleted_by_user_id"] == "admin-user"
    assert published[0]["payload"]["uploaded_employee_id"] == "EMP-001"
    assert published[0]["payload"]["uploaded_employee_code"] == "MADC-2024-0001"
    assert published[0]["payload"]["subject_employee_id"] == "EMP-010"
    assert published[0]["payload"]["subject_employee_code"] == "MADC-2024-0010"
    assert published[0]["payload"]["document_type"] == "REPORT"
    assert published[0]["payload"]["source_context"] == "change_requests.review"
    assert published[0]["actor_id"] == "admin-user"
    assert published[0]["department_id"] == "FIN"


@pytest.mark.asyncio
async def test_superseded_document_cannot_be_deleted(isolated_document_store):
    filename = "original-version.pdf"
    newer_filename = "current-version.pdf"
    (isolated_document_store / filename).write_bytes(b"%PDF-1.4\noriginal")
    (isolated_document_store / newer_filename).write_bytes(b"%PDF-1.4\ncurrent")

    await service._write_document_metadata(
        filename,
        {
            "document_id": "doc-1",
            "uploaded_employee_id": "EMP-001",
            "is_current": False,
            "version_number": 1,
        },
    )
    await service._write_document_metadata(
        newer_filename,
        {
            "document_id": "doc-2",
            "uploaded_employee_id": "EMP-001",
            "is_current": True,
            "version_number": 2,
            "supersedes_document_id": "doc-1",
        },
    )

    with pytest.raises(HTTPException) as exc:
        await service.delete_document(
            filename,
            current_user={"sub": "admin-user", "authorities": ["SYSTEM_ADMIN"]},
        )

    assert exc.value.status_code == 409
    assert exc.value.detail["error_code"] == "DOCUMENT_VERSION_HISTORY_PROTECTED"
    assert exc.value.detail["document_id"] == "doc-1"


@pytest.mark.asyncio
async def test_file_metadata_includes_optional_classification_fields(isolated_document_store):
    filename = "classified-file.pdf"
    (isolated_document_store / filename).write_bytes(b"%PDF-1.4\nclassified")

    await service._write_document_metadata(
        filename,
        {
            "document_id": filename,
            "document_type": "CERTIFICATE",
            "category": "MEDICAL_CERTIFICATE",
            "source_context": "service_book.upload",
        },
    )

    metadata = await service._file_metadata(filename)

    assert metadata["document_type"] == "CERTIFICATE"
    assert metadata["category"] == "MEDICAL_CERTIFICATE"
    assert metadata["source_context"] == "service_book.upload"


@pytest.mark.asyncio
async def test_list_documents_honors_active_role_scope(isolated_document_store):
    own_filename = "own-file.pdf"
    other_filename = "other-file.pdf"
    (isolated_document_store / own_filename).write_bytes(b"%PDF-1.4\nown")
    (isolated_document_store / other_filename).write_bytes(b"%PDF-1.4\nother")

    await service._write_document_metadata(own_filename, {"uploaded_employee_id": "EMP-001"})
    await service._write_document_metadata(other_filename, {"uploaded_employee_id": "EMP-002"})

    employee_result = await service.list_documents(
        current_user={
            "sub": "user-1",
            "employee_id": "EMP-001",
            "authorities": ["EMPLOYEE", "DEPT_DATA_ENTRY"],
            "active_role": "EMPLOYEE",
        }
    )
    department_result = await service.list_documents(
        current_user={
            "sub": "user-1",
            "employee_id": "EMP-001",
            "authorities": ["EMPLOYEE", "DEPT_DATA_ENTRY"],
            "active_role": "DEPT_DATA_ENTRY",
        }
    )

    assert [item["filename"] for item in employee_result["items"]] == [own_filename]
    assert sorted(item["filename"] for item in department_result["items"]) == [other_filename, own_filename]


@pytest.mark.asyncio
async def test_list_documents_for_management_role_includes_storage_files_without_db_metadata(
    isolated_document_store,
    monkeypatch,
):
    metadata_filename = "metadata-backed.pdf"
    storage_only_filename = "storage-only.pdf"
    (isolated_document_store / metadata_filename).write_bytes(b"%PDF-1.4\nmetadata")
    (isolated_document_store / storage_only_filename).write_bytes(b"%PDF-1.4\nstorage-only")

    class FakeMetadataRepository:
        async def get(self, filename):
            if filename == metadata_filename:
                return {
                    "filename": metadata_filename,
                    "original_name": "metadata-backed.pdf",
                    "uploaded_at": "2026-04-10T10:00:00+00:00",
                }
            return None

        async def get_many(self, filenames):
            assert sorted(filenames) == sorted([metadata_filename, storage_only_filename])
            return {
                metadata_filename: {
                    "filename": metadata_filename,
                    "original_name": "metadata-backed.pdf",
                    "uploaded_at": "2026-04-10T10:00:00+00:00",
                }
            }

    monkeypatch.setattr(_query_mod, "metadata_repository", lambda *, db=None: FakeMetadataRepository())

    result = await service.list_documents(
        current_user={
            "sub": "admin-user",
            "authorities": ["SYSTEM_ADMIN"],
        },
    )

    assert sorted(item["filename"] for item in result["items"]) == [metadata_filename, storage_only_filename]
    storage_only_item = next(item for item in result["items"] if item["filename"] == storage_only_filename)
    assert storage_only_item["original_name"] == storage_only_filename
    assert storage_only_item["uploaded_at"]


@pytest.mark.asyncio
async def test_db_backed_admin_list_documents_uses_metadata_repository_without_storage_scan(monkeypatch):
    class FakeMetadataRepository:
        async def list_documents(self, **kwargs):
            assert kwargs["owner_field"] is None
            assert kwargs["owner_value"] is None
            assert kwargs["document_type"] == "ORDER"
            return [
                {
                    "filename": "metadata-order.pdf",
                    "original_name": "metadata-order.pdf",
                    "document_type": "ORDER",
                    "uploaded_at": "2026-04-10T10:00:00+00:00",
                }
            ], 1

    class FakeStorage:
        def exists(self, bucket, filename):
            assert bucket == StorageBucket.DOCUMENT
            assert filename == "metadata-order.pdf"
            return True

        def list_names(self, bucket):
            raise AssertionError("DB-backed document listings should not enumerate storage")

    monkeypatch.setattr(_query_mod, "metadata_repository", lambda *, db=None: FakeMetadataRepository())
    monkeypatch.setattr(_query_mod, "storage", lambda: FakeStorage())
    async def fake_file_metadata(filename, *, db=None, metadata=None):
        return metadata or {"filename": filename}

    monkeypatch.setattr(_query_mod, "file_metadata", fake_file_metadata)

    result = await service.list_documents(
        current_user={"sub": "admin-user", "authorities": ["SYSTEM_ADMIN"]},
        document_type="order",
        db=object(),
    )

    assert result["total"] == 1
    assert [item["filename"] for item in result["items"]] == ["metadata-order.pdf"]


@pytest.mark.asyncio
async def test_list_documents_filters_by_classification_metadata(isolated_document_store):
    filenames = [
        "certificate-change-request.pdf",
        "certificate-service-book.pdf",
        "order-change-request.pdf",
    ]
    for filename in filenames:
        (isolated_document_store / filename).write_bytes(b"%PDF-1.4\nclassified")

    await service._write_document_metadata(
        "certificate-change-request.pdf",
        {
            "document_type": "CERTIFICATE",
            "category": "MEDICAL_CERTIFICATE",
            "source_context": "change_requests.upload",
        },
    )
    await service._write_document_metadata(
        "certificate-service-book.pdf",
        {
            "document_type": "CERTIFICATE",
            "category": "SERVICE_BOOK_SUPPORT",
            "source_context": "service_book.part_iia",
        },
    )
    await service._write_document_metadata(
        "order-change-request.pdf",
        {
            "document_type": "ORDER",
            "category": "APPOINTMENT_ORDER",
            "source_context": "change_requests.upload",
        },
    )

    result = await service.list_documents(
        current_user={
            "sub": "admin-user",
            "authorities": ["SYSTEM_ADMIN"],
        },
        document_type="certificate",
        source_context="change requests.upload",
    )

    assert [item["filename"] for item in result["items"]] == ["certificate-change-request.pdf"]
    assert result["available_filters"] == {
        "document_types": ["CERTIFICATE", "ORDER"],
        "categories": ["APPOINTMENT_ORDER", "MEDICAL_CERTIFICATE", "SERVICE_BOOK_SUPPORT"],
        "source_contexts": ["change_requests.upload", "service_book.part_iia"],
    }


@pytest.mark.asyncio
async def test_list_documents_filters_by_uploader_query(isolated_document_store):
    matching_filename = "matching-uploader.pdf"
    other_filename = "other-uploader.pdf"
    (isolated_document_store / matching_filename).write_bytes(b"%PDF-1.4\nmatch")
    (isolated_document_store / other_filename).write_bytes(b"%PDF-1.4\nother")

    await service._write_document_metadata(
        matching_filename,
        {
            "uploaded_employee_id": "EMP-001",
            "uploaded_employee_code": "MADC-2024-0001",
        },
    )
    await service._write_document_metadata(
        other_filename,
        {
            "uploaded_employee_id": "EMP-002",
            "uploaded_employee_code": "MADC-2024-0002",
        },
    )

    result = await service.list_documents(
        current_user={"sub": "admin-user", "authorities": ["SYSTEM_ADMIN"]},
        uploader_query="2024-0001",
    )

    assert [item["filename"] for item in result["items"]] == [matching_filename]


@pytest.mark.asyncio
async def test_list_documents_filters_by_entity_category_lock_and_date(isolated_document_store):
    filename = "service-event-order.pdf"
    other_filename = "other-order.pdf"
    (isolated_document_store / filename).write_bytes(b"%PDF-1.4\nservice-event")
    (isolated_document_store / other_filename).write_bytes(b"%PDF-1.4\nother")

    await service._write_document_metadata(
        filename,
        {
            "document_id": filename,
            "entity_type": "SERVICE_EVENT",
            "entity_id": "SE-100",
            "document_type": "ORDER",
            "category": "PROMOTION_ORDER",
            "source_context": "service_events.attach",
            "is_locked": True,
            "uploaded_at": "2026-04-09T10:00:00+00:00",
        },
    )
    await service._write_document_metadata(
        other_filename,
        {
            "document_id": other_filename,
            "entity_type": "CHANGE_REQUEST",
            "entity_id": "CR-1",
            "document_type": "ORDER",
            "category": "APPOINTMENT_ORDER",
            "source_context": "change_requests.upload",
            "is_locked": False,
            "uploaded_at": "2026-04-01T10:00:00+00:00",
        },
    )

    result = await service.list_documents(
        current_user={"sub": "admin-user", "authorities": ["SYSTEM_ADMIN"]},
        entity_type="service event",
        entity_id="SE-100",
        category="promotion order",
        is_locked=True,
        date_from="2026-04-08T00:00:00+00:00",
        date_to="2026-04-10T00:00:00+00:00",
    )

    assert [item["filename"] for item in result["items"]] == [filename]
    assert result["items"][0]["entity_type"] == "SERVICE_EVENT"
    assert result["items"][0]["category"] == "PROMOTION_ORDER"


@pytest.mark.asyncio
async def test_list_documents_rejects_invalid_source_context_filter(isolated_document_store):
    with pytest.raises(HTTPException) as exc:
        await service.list_documents(
            current_user={
                "sub": "admin-user",
                "authorities": ["SYSTEM_ADMIN"],
            },
            source_context="service/book",
        )

    assert exc.value.status_code == 422
    assert exc.value.detail["error_code"] == "DOCUMENT_SOURCE_CONTEXT_INVALID"
    assert exc.value.detail["source_context"] == "service/book"


def test_document_delete_permission_honors_active_role() -> None:
    require_document_delete_permission(
        {
            "authorities": ["EMPLOYEE", "DEPT_DATA_ENTRY"],
            "active_role": "DEPT_DATA_ENTRY",
        }
    )

    with pytest.raises(HTTPException) as exc:
        require_document_delete_permission(
            {
                "authorities": ["EMPLOYEE", "DEPT_DATA_ENTRY"],
                "active_role": "EMPLOYEE",
            }
        )

    assert exc.value.status_code == 403
