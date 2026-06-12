import {
  attachDocumentToEntity,
  validateDocumentMetadata,
} from "@/modules/documents/services/documentDomainService";
import { apiClient as api, API_URL } from "@/platform/api/httpClient";

/**
 * Document file endpoints require ``Authorization: Bearer <access_token>`` —
 * plain anchor navigation does NOT attach that header, so any download or
 * preview that uses ``<a href={getFileUrl(...)}>`` would fail with 401 in
 * production. ``openDocument`` and ``downloadDocument`` below stream the
 * file through the authenticated apiClient, materialize a blob: URL, and
 * either open it in a new tab or trigger a save — keeping access-token
 * scoping intact and avoiding the cookie-auth + CSRF surface.
 */
async function _fetchAsBlob(path) {
  const response = await api.get(path, { responseType: "blob" });
  return response.data;
}

async function openDocument(filename) {
  if (!filename || typeof window === "undefined") return;
  const blob = await _fetchAsBlob(`/documents/files/${filename}`);
  const objectUrl = URL.createObjectURL(blob);
  // window.open(url, "_blank", "noopener,...") returns null per spec even on
  // success, so its return value cannot be used to detect popup-blocking.
  // Using an anchor click with target="_blank" opens the document in a new
  // tab without ever hijacking the current tab — which would otherwise force
  // a full reload (and a possible login redirect) when the user clicks Back.
  const anchor = window.document.createElement("a");
  anchor.href = objectUrl;
  anchor.target = "_blank";
  anchor.rel = "noopener noreferrer";
  window.document.body.appendChild(anchor);
  anchor.click();
  window.document.body.removeChild(anchor);
  setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
}

async function downloadDocument(filename, { suggestedName } = {}) {
  if (!filename || typeof window === "undefined") return;
  const blob = await _fetchAsBlob(`/documents/files/${filename}/download`);
  const objectUrl = URL.createObjectURL(blob);
  const anchor = window.document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = suggestedName || filename;
  anchor.rel = "noopener";
  window.document.body.appendChild(anchor);
  anchor.click();
  window.document.body.removeChild(anchor);
  setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
}

export const documentsAPI = {
  upload: (file, metadata = {}) => attachDocumentToEntity({ file, metadata }),
  get: (filename) => api.get(`/documents/files/${filename}`),
  getMetadata: (filename) => api.get(`/documents/files/${filename}/metadata`),
  // NOTE: getFileUrl / getDownloadUrl return UNauthenticated URLs and are
  // retained for places (e.g. <img src=...>) where the access token is
  // attached via a different mechanism. For document open / save flows use
  // openDocument() / downloadDocument() so the auth header is included.
  getFileUrl: (filename) => `${API_URL}/documents/files/${filename}`,
  getDownloadUrl: (filename) => `${API_URL}/documents/files/${filename}/download`,
  openDocument,
  downloadDocument,
  list: (params = {}) => api.get("/documents/files", { params }),
  remove: (filename) => api.delete(`/documents/files/${filename}`),
};

export const uploadAPI = {
  uploadPhoto: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return api.post("/documents/photo", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  uploadSignature: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return api.post("/documents/signature", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  getPhotoUrl: (filename) => `${API_URL}/documents/photos/${filename}`,
  getSignatureUrl: (filename) => `${API_URL}/documents/signatures/${filename}`,
};

export { attachDocumentToEntity, validateDocumentMetadata };
