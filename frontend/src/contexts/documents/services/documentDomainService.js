import { apiClient as api } from "@/platform/api/httpClient";

export const ALLOWED_DOCUMENT_ENTITY_TYPES = Object.freeze([
  "CHANGE_REQUEST",
  "LEAVE",
  "MASTER_DATA",
  "SERVICE_BOOK",
  "SERVICE_RECORD",
  "SERVICE_EVENT",
]);

export const ALLOWED_DOCUMENT_TYPE_CODES = Object.freeze([
  "ORDER",
  "NOTIFICATION",
  "MEMORANDUM",
  "CERTIFICATE",
  "REPORT",
]);

const DOCUMENT_SOURCE_CONTEXT_PATTERN = /^[a-z0-9]+(?:[._][a-z0-9]+)*$/;
const DOCUMENT_CATEGORY_PATTERN = /^[A-Z0-9]+(?:_[A-Z0-9]+)*$/;

const isServiceHistoryKey = (key) =>
  ["service_history", "service_book_truth", "official_history"].includes(
    String(key || "").trim().toLowerCase(),
  );

export const validateDocumentMetadata = (metadata = {}) => {
  const normalized = { ...(metadata || {}) };
  const entityType = String(normalized.entity_type || "")
    .trim()
    .toUpperCase()
    .replaceAll("-", "_")
    .replaceAll(" ", "_");
  const entityId = String(normalized.entity_id || "").trim();
  const documentType = String(normalized.document_type || "")
    .trim()
    .toUpperCase()
    .replaceAll("-", "_")
    .replaceAll(" ", "_");
  const category = String(normalized.category || "")
    .trim()
    .toUpperCase()
    .replaceAll("-", "_")
    .replaceAll(" ", "_");
  const sourceContext = String(normalized.source_context || "")
    .trim()
    .toLowerCase()
    .replaceAll("-", "_")
    .replaceAll(" ", "_");
  const supersedesDocumentId = String(normalized.supersedes_document_id || "").trim();

  if (entityType && !entityId) {
    throw new Error("entity_id is required when entity_type is provided");
  }
  if (entityId && !entityType) {
    throw new Error("entity_type is required when entity_id is provided");
  }
  if (entityType && !ALLOWED_DOCUMENT_ENTITY_TYPES.includes(entityType)) {
    throw new Error(
      `entity_type '${normalized.entity_type}' not allowed. Allowed types: ${ALLOWED_DOCUMENT_ENTITY_TYPES.join(", ")}`,
    );
  }
  if (documentType && !ALLOWED_DOCUMENT_TYPE_CODES.includes(documentType)) {
    throw new Error(
      `document_type '${normalized.document_type}' not allowed. Allowed types: ${ALLOWED_DOCUMENT_TYPE_CODES.join(", ")}`,
    );
  }
  if (category && !DOCUMENT_CATEGORY_PATTERN.test(category)) {
    throw new Error(
      "category must contain only uppercase letters, numbers, and underscores",
    );
  }
  if (sourceContext && !DOCUMENT_SOURCE_CONTEXT_PATTERN.test(sourceContext)) {
    throw new Error(
      "source_context must contain only lowercase letters, numbers, dots, and underscores",
    );
  }

  const badKey = Object.keys(normalized).find((key) => isServiceHistoryKey(key));
  if (badKey) {
    throw new Error("Document metadata cannot define service-history truth");
  }

  if (entityType) normalized.entity_type = entityType;
  if (entityId) normalized.entity_id = entityId;
  if (documentType) normalized.document_type = documentType;
  if (category) normalized.category = category;
  if (sourceContext) normalized.source_context = sourceContext;
  if (supersedesDocumentId) normalized.supersedes_document_id = supersedesDocumentId;
  return normalized;
};

export const attachDocumentToEntity = async ({ file, metadata = {} }) => {
  const validated = validateDocumentMetadata(metadata);
  const params = new URLSearchParams();
  if (validated.entity_type) params.set("entity_type", validated.entity_type);
  if (validated.entity_id) params.set("entity_id", validated.entity_id);
  if (validated.document_type) params.set("document_type", validated.document_type);
  if (validated.category) params.set("category", validated.category);
  if (validated.source_context) params.set("source_context", validated.source_context);
  if (validated.supersedes_document_id) {
    params.set("supersedes_document_id", validated.supersedes_document_id);
  }

  const formData = new FormData();
  formData.append("file", file);

  return api.post(`/documents/document${params.toString() ? `?${params.toString()}` : ""}`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};
