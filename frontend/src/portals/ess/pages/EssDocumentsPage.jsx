import { useCallback, useEffect, useMemo, useState } from "react";
import { essAPI } from "@/contexts/ess";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table";
import { CardSkeleton, PageHeaderSkeleton, TableSkeleton } from "@/shared/ui/skeletons";
import { getApiErrorMessage } from "@/shared/lib/utils";
import {
  Download,
  FileText,
  FolderOpen,
  RefreshCw,
  Search,
  ShieldCheck,
  TimerReset,
} from "lucide-react";
import { toast } from "sonner";

const PAGE_SIZE = 50;

const LOCK_STATUS_OPTIONS = [
  { value: "ALL", label: "All statuses" },
  { value: "UNLOCKED", label: "Draft only" },
  { value: "LOCKED", label: "Approved only" },
];

const PREVIEWABLE_EXTENSIONS = new Set([
  "csv",
  "gif",
  "htm",
  "html",
  "jpeg",
  "jpg",
  "json",
  "pdf",
  "png",
  "svg",
  "txt",
  "webp",
  "xml",
]);

const isPreviewableContentType = (value) => {
  const normalized = String(value || "").trim().toLowerCase();
  if (!normalized) return false;
  return (
    normalized.startsWith("image/") ||
    normalized.startsWith("text/") ||
    normalized === "application/pdf" ||
    normalized === "application/json" ||
    normalized === "application/xml" ||
    normalized === "image/svg+xml"
  );
};

const canPreviewDocument = (document) => {
  if (isPreviewableContentType(document?.content_type)) return true;
  const fileName = String(document?.original_name || document?.filename || "").trim().toLowerCase();
  const extension = fileName.includes(".") ? fileName.split(".").pop() : "";
  return PREVIEWABLE_EXTENSIONS.has(extension);
};

const formatDocumentTypeLabel = (value) =>
  String(value || "")
    .trim()
    .toLowerCase()
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");

const formatSourceContextLabel = (value) =>
  String(value || "")
    .trim()
    .toLowerCase()
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

const formatDate = (value) => {
  if (!value) return "-";
  try {
    return new Date(value).toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return value;
  }
};

const formatSize = (bytes) => {
  const numeric = Number(bytes);
  if (!Number.isFinite(numeric) || numeric <= 0) return "-";
  if (numeric >= 1024 * 1024) return `${(numeric / (1024 * 1024)).toFixed(2)} MB`;
  return `${Math.max(1, Math.round(numeric / 1024))} KB`;
};

const buildStatusLabel = (document) => (document?.is_locked ? "Approved" : "Draft");

const createResponseBlob = (response, fallbackContentType) => {
  if (response?.data instanceof Blob) return response.data;

  const contentType = response?.headers?.["content-type"] || fallbackContentType || "application/octet-stream";
  return new Blob([response?.data], { type: contentType });
};

const EssDocumentsPage = () => {
  const [documents, setDocuments] = useState([]);
  const [total, setTotal] = useState(0);
  const [availableFilters, setAvailableFilters] = useState({ document_types: [], source_contexts: [] });
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [documentType, setDocumentType] = useState("");
  const [sourceContext, setSourceContext] = useState("");
  const [lockStatus, setLockStatus] = useState("ALL");

  useEffect(() => {
    const timeoutId = setTimeout(() => setDebouncedQuery(query), 250);
    return () => clearTimeout(timeoutId);
  }, [query]);

  const loadDocuments = async ({ offset = 0, append = false, queryOverride } = {}) => {
    if (append) {
      setLoadingMore(true);
    } else {
      setLoading(true);
      setError("");
    }

    try {
      const activeQuery = typeof queryOverride === "string" ? queryOverride : debouncedQuery;
      const response = await essAPI.getMyDocuments({
        query: activeQuery.trim() || undefined,
        document_type: documentType || undefined,
        source_context: sourceContext || undefined,
        is_locked:
          lockStatus === "LOCKED"
            ? true
            : lockStatus === "UNLOCKED"
              ? false
              : undefined,
        limit: PAGE_SIZE,
        offset,
      });
      const payload = response?.data || {};
      const items = Array.isArray(payload.items) ? payload.items : [];
      setDocuments((previous) => (append ? [...previous, ...items] : items));
      setTotal(Number(payload.total || 0));
      setAvailableFilters({
        document_types: payload.available_filters?.document_types || [],
        source_contexts: payload.available_filters?.source_contexts || [],
      });
      if (!append) setError("");
    } catch (fetchError) {
      const message = getApiErrorMessage(fetchError, "Failed to load documents");
      toast.error(message);
      if (!append) {
        setDocuments([]);
        setTotal(0);
        setError(message);
      }
    } finally {
      if (append) {
        setLoadingMore(false);
      } else {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    loadDocuments({ offset: 0 });
  }, [debouncedQuery, documentType, sourceContext, lockStatus]);

  const hasMore = documents.length < total;
  const hasActiveFilters = Boolean(debouncedQuery || documentType || sourceContext || lockStatus !== "ALL");

  const stats = useMemo(() => {
    const approvedCount = documents.filter((document) => document?.is_locked).length;
    const sourceCount = new Set(
      documents.map((document) => String(document?.source_context || "").trim()).filter(Boolean)
    ).size;
    return {
      total: total || documents.length,
      approved: approvedCount,
      sources: sourceCount,
    };
  }, [documents, total]);

  const clearFilters = () => {
    setQuery("");
    setDebouncedQuery("");
    setDocumentType("");
    setSourceContext("");
    setLockStatus("ALL");
  };

  const handlePreviewDocument = useCallback(async (documentItem) => {
    const previewWindow = window.open("", "_blank");
    if (!previewWindow) {
      toast.error("Allow pop-ups to preview this document");
      return;
    }

    try {
      const response = await essAPI.previewMyDocument(documentItem.filename);
      const blob = createResponseBlob(response, documentItem?.content_type);
      const objectUrl = URL.createObjectURL(blob);
      previewWindow.location.replace(objectUrl);
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
    } catch (previewError) {
      previewWindow.close();
      toast.error(getApiErrorMessage(previewError, "Failed to preview document"));
    }
  }, []);

  const handleDownloadDocument = useCallback(async (documentItem) => {
    try {
      const response = await essAPI.downloadMyDocument(documentItem.filename);
      const blob = createResponseBlob(response, documentItem?.content_type);
      const objectUrl = URL.createObjectURL(blob);
      const anchor = window.document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = documentItem.original_name || documentItem.filename || "document";
      anchor.click();
      URL.revokeObjectURL(objectUrl);
    } catch (downloadError) {
      toast.error(getApiErrorMessage(downloadError, "Failed to download document"));
    }
  }, []);

  return (
    <>
      <div className="max-w-6xl mx-auto space-y-6 animate-fade-in" data-testid="ess-documents-page">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Employee Self-Service Portal</p>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">My Documents</h2>
            <p className="text-sm text-slate-500 mt-1">
              Download official documents that belong to your employee record.
            </p>
          </div>
          <Button variant="outline" className="gap-2" onClick={() => loadDocuments({ offset: 0, queryOverride: query })}>
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
        </div>

        {loading ? (
          <div className="space-y-6">
            <PageHeaderSkeleton />
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <CardSkeleton lines={2} />
              <CardSkeleton lines={2} />
              <CardSkeleton lines={2} />
            </div>
            <TableSkeleton rows={6} columns={4} />
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <Card className="border-l-4 border-l-sky-500">
                <CardContent className="pt-5 flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-medium text-slate-500">Documents available</p>
                    <p className="text-3xl font-bold tracking-tight text-slate-900">{stats.total}</p>
                  </div>
                  <div className="rounded-full bg-sky-100 p-3 text-sky-700">
                    <FolderOpen className="w-5 h-5" />
                  </div>
                </CardContent>
              </Card>
              <Card className="border-l-4 border-l-emerald-500">
                <CardContent className="pt-5 flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-medium text-slate-500">Approved records</p>
                    <p className="text-3xl font-bold tracking-tight text-slate-900">{stats.approved}</p>
                  </div>
                  <div className="rounded-full bg-emerald-100 p-3 text-emerald-700">
                    <ShieldCheck className="w-5 h-5" />
                  </div>
                </CardContent>
              </Card>
              <Card className="border-l-4 border-l-amber-500">
                <CardContent className="pt-5 flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-medium text-slate-500">Source streams</p>
                    <p className="text-3xl font-bold tracking-tight text-slate-900">{stats.sources}</p>
                  </div>
                  <div className="rounded-full bg-amber-100 p-3 text-amber-700">
                    <TimerReset className="w-5 h-5" />
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <FileText className="w-5 h-5" />
                  Document Browser
                </CardTitle>
                <CardDescription>
                  Search and filter documents linked to your employee record.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-col gap-3">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                    <Input
                      className="pl-9"
                      placeholder="Search by file name"
                      value={query}
                      onChange={(event) => setQuery(event.target.value)}
                    />
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Select value={documentType || "ALL"} onValueChange={(value) => setDocumentType(value === "ALL" ? "" : value)}>
                      <SelectTrigger className="min-w-[180px] flex-1">
                        <SelectValue placeholder="All document types" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="ALL">All document types</SelectItem>
                        {availableFilters.document_types.map((option) => (
                          <SelectItem key={option} value={option}>{formatDocumentTypeLabel(option)}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Select value={sourceContext || "ALL"} onValueChange={(value) => setSourceContext(value === "ALL" ? "" : value)}>
                      <SelectTrigger className="min-w-[180px] flex-1">
                        <SelectValue placeholder="All source contexts" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="ALL">All source contexts</SelectItem>
                        {availableFilters.source_contexts.map((option) => (
                          <SelectItem key={option} value={option}>{formatSourceContextLabel(option)}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Select value={lockStatus} onValueChange={setLockStatus}>
                      <SelectTrigger className="min-w-[160px] flex-1">
                        <SelectValue placeholder="All statuses" />
                      </SelectTrigger>
                      <SelectContent>
                        {LOCK_STATUS_OPTIONS.map((option) => (
                          <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={clearFilters}
                      disabled={!hasActiveFilters}
                      className="shrink-0 text-muted-foreground hover:text-foreground disabled:opacity-30"
                    >
                      Clear filters
                    </Button>
                  </div>
                </div>

                <div className="rounded-md border">
                  {error ? (
                    <div className="p-6 space-y-3">
                      <p className="text-sm font-medium text-red-600">Failed to load documents</p>
                      <p className="text-xs text-slate-500">{error}</p>
                      <Button variant="outline" size="sm" onClick={() => loadDocuments({ offset: 0, queryOverride: query })}>
                        Retry
                      </Button>
                    </div>
                  ) : documents.length === 0 ? (
                    <div className="p-8 text-center space-y-2">
                      <FileText className="w-8 h-8 mx-auto text-slate-300" />
                      <p className="text-sm font-medium text-slate-600">
                        {hasActiveFilters ? "No documents match the current filters." : "No documents available yet."}
                      </p>
                      <p className="text-xs text-slate-500">
                        Documents uploaded against your employee record will appear here.
                      </p>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>File</TableHead>
                            <TableHead className="hidden md:table-cell">Context</TableHead>
                            <TableHead className="hidden sm:table-cell">Added</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead className="text-right">Action</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {documents.map((document) => (
                            <TableRow key={document.document_id || document.filename}>
                              <TableCell className="max-w-[260px]">
                                <div className="font-medium truncate">{document.original_name || document.filename}</div>
                                {document.original_name && document.original_name !== document.filename ? (
                                  <div className="text-xs text-slate-500 truncate">{document.filename}</div>
                                ) : null}
                                <div className="mt-1 flex flex-wrap gap-1">
                                  {document.document_type ? (
                                    <Badge variant="outline" className="text-[10px]">
                                      {formatDocumentTypeLabel(document.document_type)}
                                    </Badge>
                                  ) : null}
                                  {document.category ? (
                                    <Badge variant="secondary" className="text-[10px]">
                                      {formatDocumentTypeLabel(document.category)}
                                    </Badge>
                                  ) : null}
                                </div>
                              </TableCell>
                              <TableCell className="hidden md:table-cell">
                                <div className="text-sm text-slate-700">
                                  {document.source_context ? formatSourceContextLabel(document.source_context) : "General upload"}
                                </div>
                                {document.entity_type || document.entity_id ? (
                                  <div className="text-xs text-slate-500">
                                    {[document.entity_type, document.entity_id].filter(Boolean).join(" • ")}
                                  </div>
                                ) : null}
                              </TableCell>
                              <TableCell className="hidden sm:table-cell">
                                <div className="text-sm text-slate-700">{formatDate(document.uploaded_at)}</div>
                                <div className="text-xs text-slate-500">{formatSize(document.file_size)}</div>
                              </TableCell>
                              <TableCell>
                                <Badge variant={document.is_locked ? "secondary" : "outline"}>
                                  {buildStatusLabel(document)}
                                </Badge>
                              </TableCell>
                              <TableCell className="text-right">
                                <div className="flex items-center justify-end gap-2">
                                  {canPreviewDocument(document) ? (
                                    <Button
                                      type="button"
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => handlePreviewDocument(document)}
                                    >
                                      Preview
                                    </Button>
                                  ) : null}
                                  <Button
                                    type="button"
                                    size="sm"
                                    variant="outline"
                                    onClick={() => handleDownloadDocument(document)}
                                  >
                                      <Download className="w-4 h-4 mr-2" />
                                      Download
                                  </Button>
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </div>

                {hasMore ? (
                  <div className="flex justify-center">
                    <Button
                      variant="outline"
                      onClick={() => loadDocuments({ offset: documents.length, append: true, queryOverride: query })}
                      disabled={loadingMore}
                    >
                      {loadingMore ? "Loading..." : "Load more"}
                    </Button>
                  </div>
                ) : null}
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </>
  );
};

export default EssDocumentsPage;