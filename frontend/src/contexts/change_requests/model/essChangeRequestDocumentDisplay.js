const DOCUMENT_DELETE_AUTHORITIES = new Set([
  "SYSTEM_ADMIN",
  "GLOBAL_DATA_ENTRY",
  "DEPT_DATA_ENTRY",
  "APPROVING_AUTHORITY",
]);

const DOCUMENT_SOURCE_CONTEXT_LABELS = {
  "change_requests.upload": "Change Request Upload",
  "service_book.part_iia": "Service Book Part II-A",
};

export function canDeleteDocumentsForAuthority(authority) {
  return DOCUMENT_DELETE_AUTHORITIES.has(String(authority || "").trim().toUpperCase());
}

export function formatDocumentTypeLabel(documentType) {
  const normalized = String(documentType || "").trim();
  if (!normalized) return "";
  return normalized
    .toLowerCase()
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function formatDocumentSourceContextLabel(sourceContext) {
  const normalized = String(sourceContext || "").trim().toLowerCase();
  if (!normalized) return "";
  if (DOCUMENT_SOURCE_CONTEXT_LABELS[normalized]) {
    return DOCUMENT_SOURCE_CONTEXT_LABELS[normalized];
  }

  return normalized
    .split(".")
    .map((segment) =>
      segment
        .split("_")
        .filter(Boolean)
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(" ")
    )
    .filter(Boolean)
    .join(" / ");
}