import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import { documentsAPI } from "@/contexts/documents/api/documentsApi";
import { formatDocumentMetadataErrorMessage, getApiErrorMessage } from "@/shared/lib/utils";

const normalizeDocumentFilterValue = (value) => String(value || "").trim();
const DOCUMENT_PAGE_SIZE = 50;

export const getDocumentFilterOptions = (documents, fieldName) => {
  const options = new Set();
  for (const document of documents || []) {
    const value = normalizeDocumentFilterValue(document?.[fieldName]);
    if (value) {
      options.add(value);
    }
  }
  return [...options].sort((left, right) => left.localeCompare(right));
};

export function useDocumentsBrowser({ open = true, uploadMetadata = {} } = {}) {
  const [documents, setDocuments] = useState([]);
  const [documentsTotal, setDocumentsTotal] = useState(0);
  const [availableFilters, setAvailableFilters] = useState({
    document_types: [],
    source_contexts: [],
  });
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [loadingMoreDocuments, setLoadingMoreDocuments] = useState(false);
  const [documentsError, setDocumentsError] = useState(null);
  const [documentQuery, setDocumentQuery] = useState("");
  const [debouncedDocumentQuery, setDebouncedDocumentQuery] = useState("");
  const [uploaderQuery, setUploaderQuery] = useState("");
  const [debouncedUploaderQuery, setDebouncedUploaderQuery] = useState("");
  const [documentTypeFilter, setDocumentTypeFilter] = useState("");
  const [sourceContextFilter, setSourceContextFilter] = useState("");
  const [lockStatusFilter, setLockStatusFilter] = useState("ALL");
  const [deletingDocument, setDeletingDocument] = useState(null);
  const [uploading, setUploading] = useState(false);
  const searchDebounceRef = useRef(null);
  const nextListRequestIdRef = useRef(0);
  const latestListRequestIdRef = useRef(0);

  const documentTypeOptions = useMemo(
    () =>
      availableFilters.document_types.length > 0
        ? availableFilters.document_types
        : getDocumentFilterOptions(documents, "document_type"),
    [availableFilters.document_types, documents]
  );

  const sourceContextOptions = useMemo(
    () =>
      availableFilters.source_contexts.length > 0
        ? availableFilters.source_contexts
        : getDocumentFilterOptions(documents, "source_context"),
    [availableFilters.source_contexts, documents]
  );

  const visibleDocuments = documents;
  const hasMoreDocuments = documents.length < documentsTotal;

  useEffect(() => {
    clearTimeout(searchDebounceRef.current);
    searchDebounceRef.current = setTimeout(() => setDebouncedDocumentQuery(documentQuery), 300);
    return () => clearTimeout(searchDebounceRef.current);
  }, [documentQuery]);

  useEffect(() => {
    const timeoutId = setTimeout(() => setDebouncedUploaderQuery(uploaderQuery), 300);
    return () => clearTimeout(timeoutId);
  }, [uploaderQuery]);

  const fetchDocuments = useCallback(async ({ offset = 0, append = false, queryOverride } = {}) => {
    const requestId = nextListRequestIdRef.current + 1;
    nextListRequestIdRef.current = requestId;
    latestListRequestIdRef.current = requestId;

    if (append) {
      setLoadingMoreDocuments(true);
    } else {
      setDocumentsLoading(true);
      setLoadingMoreDocuments(false);
      setDocumentsError(null);
    }

    try {
      const activeQuery = typeof queryOverride === "string" ? queryOverride : debouncedDocumentQuery;
      const res = await documentsAPI.list({
        query: activeQuery.trim() || undefined,
        uploader_query: debouncedUploaderQuery.trim() || undefined,
        document_type: documentTypeFilter || undefined,
        source_context: sourceContextFilter || undefined,
        is_locked:
          lockStatusFilter === "LOCKED"
            ? true
            : lockStatusFilter === "UNLOCKED"
              ? false
              : undefined,
        limit: DOCUMENT_PAGE_SIZE,
        offset,
      });
      if (requestId !== latestListRequestIdRef.current) {
        return;
      }
      const items = res?.data?.items || [];
      setDocumentsTotal(Number(res?.data?.total ?? 0));
      setAvailableFilters({
        document_types: res?.data?.available_filters?.document_types || [],
        source_contexts: res?.data?.available_filters?.source_contexts || [],
      });
      setDocuments((prev) => (append ? [...prev, ...items] : items));
      if (!append) setDocumentsError(null);
    } catch (err) {
      if (requestId !== latestListRequestIdRef.current) {
        return;
      }
      const metadataMessage = formatDocumentMetadataErrorMessage(err);
      if (metadataMessage) {
        toast.error(metadataMessage);
        if (!append) setDocumentsError(metadataMessage);
        return;
      }
      const listErrorMessage = getApiErrorMessage(err, "Failed to load documents");
      toast.error(listErrorMessage);
      if (!append) setDocumentsError(listErrorMessage);
    } finally {
      if (requestId === latestListRequestIdRef.current) {
        if (append) {
          setLoadingMoreDocuments(false);
        } else {
          setDocumentsLoading(false);
        }
      }
    }
  }, [debouncedDocumentQuery, debouncedUploaderQuery, documentTypeFilter, lockStatusFilter, sourceContextFilter]);

  const loadDocuments = useCallback(async () => {
    await fetchDocuments({ offset: 0, append: false, queryOverride: documentQuery });
  }, [documentQuery, fetchDocuments]);

  const syncDocuments = useCallback(async () => {
    await fetchDocuments({ offset: 0, append: false });
  }, [fetchDocuments]);

  const loadMoreDocuments = useCallback(async () => {
    if (!hasMoreDocuments || loadingMoreDocuments || documentsLoading) {
      return;
    }
    await fetchDocuments({ offset: documents.length, append: true });
  }, [documents.length, documentsLoading, fetchDocuments, hasMoreDocuments, loadingMoreDocuments]);

  useEffect(() => {
    if (open) {
      syncDocuments();
    }
  }, [open, syncDocuments]);

  const deleteDocument = useCallback(
    async (filename) => {
      setDeletingDocument(filename);
      try {
        await documentsAPI.remove(filename);
        await loadDocuments();
        toast.success("Document deleted");
        return true;
      } catch (err) {
        const detail = err?.response?.data?.detail;
        if (detail?.error_code === "DOCUMENT_LOCKED") {
          toast.error(
            detail?.lock_reason === "APPROVED_CHANGE_REQUEST"
              ? "Approved document cannot be deleted"
              : detail?.lock_reason === "LEAVE_WORKFLOW_FINALIZED"
                ? "Finalized leave evidence cannot be deleted"
              : detail?.message || "Locked document cannot be deleted"
          );
          return false;
        }
        toast.error(getApiErrorMessage(err, "Failed to delete document"));
        return false;
      } finally {
        setDeletingDocument(null);
      }
    },
    [loadDocuments]
  );

  const uploadDocument = useCallback(
    async (file, metadataOverrides = {}) => {
      setUploading(true);
      try {
        const res = await documentsAPI.upload(file, {
          ...(uploadMetadata || {}),
          ...(metadataOverrides || {}),
        });
        const data = res?.data;
        if (data?.success) {
          await loadDocuments();
          toast.success("Document uploaded");
        }
        return data ?? null;
      } catch (err) {
        const metadataMessage = formatDocumentMetadataErrorMessage(err);
        if (metadataMessage) {
          toast.error(metadataMessage);
          return null;
        }
        toast.error(getApiErrorMessage(err, "Upload failed"));
        return null;
      } finally {
        setUploading(false);
      }
    },
    [loadDocuments, uploadMetadata]
  );

  const formatSize = useCallback((bytes) => {
    if (!bytes || Number.isNaN(bytes)) return "";
    if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    return `${(bytes / 1024).toFixed(0)} KB`;
  }, []);

  const formatDate = useCallback((isoDate) => {
    if (!isoDate) return "";
    try {
      return new Date(isoDate).toLocaleDateString("en-IN");
    } catch {
      return "";
    }
  }, []);

  const resetDocuments = useCallback(() => {
    clearTimeout(searchDebounceRef.current);
    latestListRequestIdRef.current = nextListRequestIdRef.current + 1;
    nextListRequestIdRef.current = latestListRequestIdRef.current;
    setDocuments([]);
    setDocumentsTotal(0);
    setDocumentsError(null);
    setAvailableFilters({
      document_types: [],
      source_contexts: [],
    });
    setDocumentQuery("");
    setDebouncedDocumentQuery("");
    setUploaderQuery("");
    setDebouncedUploaderQuery("");
    setDocumentTypeFilter("");
    setSourceContextFilter("");
    setLockStatusFilter("ALL");
  }, []);

  return {
    documents,
    visibleDocuments,
    documentsTotal,
    documentsLoading,
    documentsError,
    loadingMoreDocuments,
    hasMoreDocuments,
    documentQuery,
    setDocumentQuery,
    uploaderQuery,
    setUploaderQuery,
    documentTypeFilter,
    setDocumentTypeFilter,
    documentTypeOptions,
    sourceContextFilter,
    setSourceContextFilter,
    sourceContextOptions,
    lockStatusFilter,
    setLockStatusFilter,
    deletingDocument,
    uploading,
    loadDocuments,
    loadMoreDocuments,
    deleteDocument,
    uploadDocument,
    formatSize,
    formatDate,
    resetDocuments,
  };
}