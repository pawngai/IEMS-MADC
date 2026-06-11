# Document Management Implementation

Date: 2026-04-09

This note documents the current document-management implementation in MyIEMS across backend and frontend code.

## 1. Ownership and Boundaries

- Backend ownership lives in `backend/contexts/documents`.
- The documents context owns file storage, metadata, file access rules, and entity links.
- The documents context does not own service-history truth. That guard is enforced in both backend and frontend metadata validation.
- Service Book Records and Service Book read/print flows may reference document IDs, but they do not delegate their domain truth to document metadata.

Relevant files:

- `backend/contexts/documents/api/router.py`
- `backend/contexts/documents/services/document_service.py`
- `backend/contexts/documents/infrastructure/service.py`
- `backend/contexts/documents/repository/metadata_repository.py`
- `backend/contexts/documents/contracts/events.py`

## 2. API Surface

The canonical router is mounted by workflow registration:

- `backend/app/bootstrap/registrations/workflow.py`

The FastAPI router prefix is `/documents`, so the effective API surface is under `/api/documents/*`.

Current endpoints:

- `POST /api/documents/photo`
- `POST /api/documents/signature`
- `GET /api/documents/photos/{filename}`
- `GET /api/documents/signatures/{filename}`
- `DELETE /api/documents/photos/{filename}`
- `DELETE /api/documents/signatures/{filename}`
- `POST /api/documents/document`
- `GET /api/documents/files`
- `GET /api/documents/files/{filename}`
- `GET /api/documents/files/{filename}/download`
- `GET /api/documents/files/{filename}/metadata`
- `DELETE /api/documents/files/{filename}`

`POST /api/documents/document` accepts optional `entity_type`, `entity_id`, `document_type`, `category`, `source_context`, and `supersedes_document_id` query parameters. These are normalized and stored as additive metadata on the document record.

`GET /api/documents/files` accepts optional `query`, `entity_type`, `entity_id`, `document_type`, `category`, `source_context`, `is_locked`, `date_from`, and `date_to` filters. These reuse the same normalization and validation rules as upload metadata where applicable.

Current accepted entity types for document links are:

- `CHANGE_REQUEST`
- `LEAVE`
- `MASTER_DATA`
- `SERVICE_BOOK`
- `SERVICE_RECORD`
- `SERVICE_EVENT`

Entity-link validation requires both `entity_type` and `entity_id` together, or neither.

Current document classification rules:

- `document_type` is optional and currently accepts:
  - `ORDER`
  - `NOTIFICATION`
  - `MEMORANDUM`
  - `CERTIFICATE`
  - `REPORT`
- `source_context` is optional and is normalized to lowercase dot/underscore notation, for example `change_requests.upload`.
- `category` is optional and is normalized to uppercase underscore notation, for example `PROMOTION_ORDER`.

Current structured metadata-validation error codes include:

- `DOCUMENT_ENTITY_TYPE_INVALID`
- `DOCUMENT_ENTITY_ID_REQUIRED`
- `DOCUMENT_ENTITY_TYPE_REQUIRED`
- `DOCUMENT_TYPE_INVALID`
- `DOCUMENT_CATEGORY_INVALID`
- `DOCUMENT_SOURCE_CONTEXT_INVALID`
- `DOCUMENT_METADATA_TRUTH_FORBIDDEN`
- `DOCUMENT_SUPERSEDE_NOT_FOUND`
- `DOCUMENT_SUPERSEDE_LOCKED`
- `DOCUMENT_DATE_FROM_INVALID`
- `DOCUMENT_DATE_TO_INVALID`

## 3. Backend Request Flow

### 3.1 Upload flow

1. `backend/contexts/documents/api/router.py` receives the multipart upload.
2. For generic documents, the router calls `attachDocumentToEntity()` in `backend/contexts/documents/services/document_service.py`.
3. `attachDocumentToEntity()` validates metadata boundaries, then delegates file persistence to `upload_document()` in `backend/contexts/documents/infrastructure/service.py`.
4. The infrastructure service validates content type, file size, magic bytes, and safe filename handling, then writes the file through the storage abstraction.
5. Initial metadata is persisted with canonical fields such as `document_id`, `filename`, `original_name`, uploader identifiers, content type, and upload timestamp.
6. The application service merges validated entity and classification metadata, supports optional version lineage via `supersedes_document_id`, marks superseded documents as `is_current = false`, publishes `DocumentMetadataUpdated.v1` when metadata changed, and then publishes `DocumentUploaded.v1` through the outbox-backed event path.

### 3.2 Read/list/download flow

1. The router delegates to `get_document()`, `download_document()`, `list_documents()`, or `get_document_metadata()`.
2. Access checks run through `_require_document_access()`.
3. Document managers can access all files; other users are limited to files they own.
4. List and metadata responses are metadata-driven and include lock state, canonical `document_id`, optional classification fields like `document_type`, `category`, and `source_context`, plus lineage fields such as `version_number`, `is_current`, and `supersedes_document_id`.

### 3.3 Delete flow

1. Delete endpoints require `require_document_delete_permission()` from `backend/contexts/identity_access/rbac/policies/operational.py`.
2. The infrastructure service rejects deletion when metadata shows the document is locked.
3. Unlocked files are removed from storage and metadata is deleted.
4. Documents that already have a newer successor version cannot be deleted; the service returns `DOCUMENT_VERSION_HISTORY_PROTECTED` instead.

## 4. Storage and Metadata Model

### 4.1 Storage abstraction

`backend/contexts/documents/infrastructure/service.py` selects the storage backend via `settings.document_storage_backend`:

- `LocalDocumentStorage` for local disk storage.
- `GcsDocumentStorage` for Google Cloud Storage.
- `ResilientDocumentStorage` as the effective runtime wrapper when GCS is selected with local fallback enabled. In that mode, writes fall back to local storage if GCS is unavailable, reads check GCS first and local storage second, and listing merges both sources.

Local storage paths remain rooted under `settings.uploads_dir`:

- `uploads/photos`
- `uploads/signatures`
- `uploads/documents`
- `uploads/documents/_meta`

### 4.2 Metadata repository

`backend/contexts/documents/repository/metadata_repository.py` persists metadata either:

- in MongoDB collection `document_metadata` when a DB handle is available, or
- in local JSON sidecar files under `uploads/documents/_meta` when DB is not available.

Normalized metadata fields include:

- `document_id`
- `filename`
- `original_name`
- `content_type`
- `file_size`
- `uploaded_by_user_id`
- `uploaded_employee_id`
- `uploaded_employee_code`
- `uploaded_at`
- `entity_type`
- `entity_id`
- `document_type`
- `category`
- `source_context`
- `is_locked`
- `locked_at`
- `lock_reason`
- `locked_by_request_id`
- `locked_status`
- `version_number`
- `is_current`
- `supersedes_document_id`

Repository indexes cover:

- `document_id`
- `filename`
- `(uploaded_employee_id, is_current)`
- `(entity_type, entity_id)`
- `locked_at`
- `uploaded_at`

## 5. Authorization and Access Rules

Document-management authority is defined in `backend/contexts/identity_access/rbac/policies/operational.py`.

Authorities allowed to manage/delete documents:

- `SYSTEM_ADMIN`
- `GLOBAL_DATA_ENTRY`
- `DEPT_DATA_ENTRY`
- `APPROVING_AUTHORITY`

Current behavior:

- Delete requires one of the authorities above.
- Read/list/download is broader, but non-manager users can only access their own uploaded documents.
- Locked documents are immutable and cannot be deleted.
- Superseded historical versions are protected from deletion even for document managers.
- Locked delete failures now return structured backend detail with `error_code = DOCUMENT_LOCKED` plus lock metadata.
- Document permissions and document-manager authorities remain the backend security boundary.
- `/api/auth/module-access` may hide or show module navigation, but it does not grant document write/delete authority by itself.

## 6. Locking and Eventing

The lock path is implemented in `lock_documents_for_approved_request()` in `backend/contexts/documents/infrastructure/service.py`.

Current lock semantics:

- Only change requests with status `APPROVED` or `APPLIED` trigger locking.
- Lock metadata is written onto the existing document record.
- The lock reason is currently `APPROVED_CHANGE_REQUEST`.
- A `DocumentLocked.v1` outbox event is emitted after metadata is updated.

Event contracts are defined in `backend/contexts/documents/contracts/events.py`:

- `DocumentUploadedPayload`
- `DocumentLockedPayload`
- `DocumentMetadataUpdatedPayload`
- `DocumentDeletedPayload`

The documents context registers those contracts in the platform event registry, and outbox publishing goes through `OutboxRepository`.

Current document lifecycle events:

- `DocumentUploaded.v1`
- `DocumentLocked.v1`
- `DocumentMetadataUpdated.v1`
- `DocumentDeleted.v1`

The audit subscriber now listens to those four document lifecycle events and records them as `resource_type = document` in the audit log stream.

## 7. Frontend Implementation

### 7.1 Canonical frontend API

The canonical frontend adapter is:

- `frontend/src/contexts/documents/api/documentsApi.js`

This adapter exposes:

- `upload(file, metadata)`
- `get(filename)`
- `getMetadata(filename)`
- `getFileUrl(filename)`
- `getDownloadUrl(filename)`
- `list(params)`
- `remove(filename)`

Metadata normalization for uploads lives in:

- `frontend/src/contexts/documents/services/documentDomainService.js`

That service mirrors the backend boundary rule that document metadata may not define service-history truth.

### 7.2 Current UI consumers

The main document-management UI in the current frontend is the ESS change-request screen:

- `frontend/src/contexts/change_requests/hooks/useChangeRequestDocuments.js`
- `frontend/src/contexts/change_requests/containers/EssChangeRequestsScreen.jsx`

That flow supports:

- upload of supporting documents
- browsing previously uploaded documents
- search by filename
- filename search in the change-request uploaded-documents browser is debounced by 300ms before reloading the server-filtered list
- attaching an existing uploaded document to a request
- open/download actions
- delete actions for authorized roles only
- client-side presentation of locked documents as non-deletable
- upload-time classification currently sets `source_context = change_requests.upload`
- the uploaded-documents browser now shows readable `document_type` and `source_context` chips when metadata is present
- the uploaded-documents browser now sends `document_type` and `source_context` filters to `GET /api/documents/files`, so filtering works across the server-side result set instead of only the current client page
- the uploaded-documents browser now supports incremental `Load more` pagination and shows how many documents from the current server-filtered result set are loaded
- `GET /api/documents/files` now also returns `available_filters.document_types` and `available_filters.source_contexts`, allowing the browser to show complete filter options without depending on the currently loaded page
- the change-request document browser ignores stale out-of-order list responses, so slower earlier requests cannot overwrite newer search or filter results

Other direct consumers:

- `frontend/src/contexts/service_book/components/ledger/PartIIAContent.jsx`
  - uploads and downloads supporting documents from the service-book UI.
  - current uploads classify files as `document_type = CERTIFICATE` and `source_context = service_book.part_iia`.
- `frontend/src/contexts/service_book/records/components/AttachDocumentDialog.jsx`
  - supports both existing-document selection and direct inline upload before calling the Service Book Records attach endpoint.
  - inline uploads classify files with `entity_type = SERVICE_RECORD`, `entity_id = <service_event_id>`, and `source_context = service_book.records.attach`.
- `frontend/src/contexts/service_book/records/components/RecordServiceBookRecordDialog.jsx`
  - can upload supporting documents while recording a new Service Book record.
- `frontend/src/contexts/ess/api/essApi.js`
- `frontend/src/contexts/ess/api/essApi.js`
  - both still post to `/documents/document` for upload flows.

The frontend document metadata adapter now mirrors backend support for `category` and `supersedes_document_id`, and the shared error formatter handles the new structured document metadata and version-history failure codes.

## 8. Practical Data Contracts

The generic document upload response currently returns:

- `success`
- `message`
- `url`
- `document_id`
- `filename`
- `original_name`
- `file_size`
- `content_type`
- `uploaded_by`
- `uploaded_employee_id`
- `uploaded_employee_code`
- `uploaded_at`
- `metadata`
- `documents_are_not_service_history_truth`

The list response currently returns:

- `success`
- `total`
- `limit`
- `offset`
- `items[]`

Each list item currently includes:

- `document_id`
- `filename`
- `url`
- `file_size`
- `content_type`
- `uploaded_at`
- `original_name`
- `uploaded_employee_id`
- `uploaded_employee_code`
- `document_type`
- `source_context`
- `is_locked`
- `locked_at`
- `lock_reason`
- `locked_by_request_id`

Locked delete failures currently return a structured `detail` object with:

- `error_code`
- `message`
- `document_id`
- `filename`
- `lock_reason`
- `locked_by_request_id`
- `locked_status`

## 9. Test Coverage Touchpoints

The most relevant regression coverage for this area is currently:

- `backend/tests/test_uploads_document_ownership.py`
- `backend/tests/test_document_event_contracts.py`
- `backend/tests/test_contract_registry_complete.py`
- `frontend/src/contexts/documents/services/__tests__/documentDomainService.test.js`
- `frontend/src/contexts/change_requests/containers/__tests__/EssChangeRequestsScreen.test.jsx`

## 10. Current Implementation Notes

- `backend/contexts/documents/application/service.py` is intentionally a thin canonical alias over infrastructure service implementation.
- `attachDocumentToEntity()` is the backend boundary guard for entity-link metadata and event emission.
- `document_id` is currently additive and equal to the stored filename.
- Frontend Service Book Records attachment supports both existing-document selection and inline upload through the canonical documents context.
- Change-request approval is the main path that converts uploaded documents from draft state to locked state.

## Migration Summary

- No runtime behavior changed in this documentation update.
- This note reflects the current canonical `/api/documents/*` implementation and current frontend consumers.

## Risk List

- `SERVICE_RECORD` and `SERVICE_EVENT` are both accepted document entity types. Service Book Records uploads should use `SERVICE_RECORD`; older service-event metadata remains compatibility terminology.
- `document_id` currently mirrors the stored filename. Treat it as an internal document identifier unless a future migration introduces a separate stable ID.
- New document UI consumers must update this note and preserve the backend/frontend metadata allowlist in sync.
