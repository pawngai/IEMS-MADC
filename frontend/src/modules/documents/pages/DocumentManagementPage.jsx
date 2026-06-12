import { useState } from "react";
import { documentsAPI } from "@/modules/documents/api/documentsApi";
import { useDocumentsBrowser } from "@/modules/documents/hooks/useDocumentsBrowser";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/shared/ui/alert-dialog";
import { AlertCircle, FileText, RefreshCw } from "lucide-react";

const LOCK_STATUS_OPTIONS = [
  { value: "ALL", label: "All statuses" },
  { value: "UNLOCKED", label: "Draft only" },
  { value: "LOCKED", label: "Approved only" },
];

const formatDocumentTypeLabel = (documentType) => {
  const normalized = String(documentType || "").trim();
  if (!normalized) return "";
  return normalized
    .toLowerCase()
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
};

const formatDocumentSourceContextLabel = (sourceContext) => {
  const normalized = String(sourceContext || "").trim().toLowerCase();
  if (!normalized) return "";

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
};

const formatUploaderLabel = (document) => {
  const employeeCode = String(document?.uploaded_employee_code || "").trim();
  if (employeeCode) {
    return employeeCode;
  }

  const employeeId = String(document?.uploaded_employee_id || "").trim();
  if (employeeId) {
    return employeeId;
  }

  return "Unknown uploader";
};

export default function DocumentManagementPage() {
  const docs = useDocumentsBrowser({ open: true });
  const [pendingDelete, setPendingDelete] = useState(null);

  const hasActiveFilters =
    !!docs.documentQuery ||
    !!docs.uploaderQuery ||
    !!docs.documentTypeFilter ||
    !!docs.sourceContextFilter ||
    docs.lockStatusFilter !== "ALL";

  const clearAllFilters = () => {
    docs.setDocumentQuery("");
    docs.setUploaderQuery("");
    docs.setDocumentTypeFilter("");
    docs.setSourceContextFilter("");
    docs.setLockStatusFilter("ALL");
  };

  return (
    <>
      <div className="mx-auto max-w-6xl space-y-6 p-6" data-testid="document-management-page">
        <Card>
          <CardHeader>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                <CardTitle>Document Management</CardTitle>
                {!docs.documentsLoading && docs.documentsTotal > 0 && (
                  <Badge variant="secondary" className="ml-1">{docs.documentsTotal}</Badge>
                )}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => docs.loadDocuments()}
                disabled={docs.documentsLoading || docs.loadingMoreDocuments}
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${(docs.documentsLoading || docs.loadingMoreDocuments) ? "animate-spin" : ""}`} />
                Refresh
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-col gap-2">
              <div className="flex flex-wrap gap-2">
                <Input
                  className="min-w-[180px] flex-1"
                  placeholder="Search by filename"
                  value={docs.documentQuery}
                  onChange={(event) => docs.setDocumentQuery(event.target.value)}
                />
                <Input
                  className="min-w-[160px] flex-1"
                  placeholder="Filter by uploader code"
                  value={docs.uploaderQuery}
                  onChange={(event) => docs.setUploaderQuery(event.target.value)}
                />
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Select
                  value={docs.documentTypeFilter || "ALL"}
                  onValueChange={(value) => docs.setDocumentTypeFilter(value === "ALL" ? "" : value)}
                >
                  <SelectTrigger className="min-w-[160px] flex-1">
                    <SelectValue placeholder="All document types" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">All document types</SelectItem>
                    {docs.documentTypeOptions.map((option) => (
                      <SelectItem key={option} value={option}>
                        {formatDocumentTypeLabel(option)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select
                  value={docs.sourceContextFilter || "ALL"}
                  onValueChange={(value) => docs.setSourceContextFilter(value === "ALL" ? "" : value)}
                >
                  <SelectTrigger className="min-w-[140px] flex-1">
                    <SelectValue placeholder="All sources" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">All sources</SelectItem>
                    {docs.sourceContextOptions.map((option) => (
                      <SelectItem key={option} value={option}>
                        {formatDocumentSourceContextLabel(option)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select
                  value={docs.lockStatusFilter}
                  onValueChange={docs.setLockStatusFilter}
                >
                  <SelectTrigger className="min-w-[140px] flex-1">
                    <SelectValue placeholder="All statuses" />
                  </SelectTrigger>
                  <SelectContent>
                    {LOCK_STATUS_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearAllFilters}
                  disabled={!hasActiveFilters}
                  className="shrink-0 text-muted-foreground hover:text-foreground disabled:opacity-30"
                >
                  Clear filters
                </Button>
              </div>
            </div>


            <div className="rounded-md border">
              {docs.documentsLoading ? (
                <div className="flex items-center gap-2 p-6 text-sm text-muted-foreground">
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Loading documents…
                </div>
              ) : docs.documentsError && docs.documents.length === 0 ? (
                <div className="space-y-3 p-6">
                  <div className="flex items-center gap-2 text-sm font-medium text-destructive">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    Failed to load documents
                  </div>
                  <p className="text-xs text-muted-foreground">{docs.documentsError}</p>
                  <Button variant="outline" size="sm" onClick={() => docs.loadDocuments()}>
                    Retry
                  </Button>
                </div>
              ) : docs.documents.length === 0 ? (
                <div className="flex flex-col items-center gap-2 p-8 text-center">
                  <FileText className="h-8 w-8 text-muted-foreground/40" />
                  <p className="text-sm font-medium text-muted-foreground">
                    {hasActiveFilters
                      ? "No documents match the current filters."
                      : "No documents found."}
                  </p>
                  {hasActiveFilters && (
                    <Button
                      variant="link"
                      size="sm"
                      onClick={clearAllFilters}
                      className="h-auto p-0 text-xs"
                    >
                      Clear all filters
                    </Button>
                  )}
                </div>
              ) : (
                <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>File</TableHead>
                      <TableHead className="hidden md:table-cell">Belongs to</TableHead>
                      <TableHead className="hidden md:table-cell">Uploaded by</TableHead>
                      <TableHead className="hidden sm:table-cell">Info</TableHead>
                      <TableHead className="whitespace-nowrap text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {docs.visibleDocuments.map((doc) => (
                      <TableRow key={doc.document_id || doc.filename}>
                        <TableCell className="max-w-[220px]">
                          <div className="truncate font-medium">{doc.original_name || doc.filename}</div>
                          {doc.original_name && doc.original_name !== doc.filename && (
                            <div className="truncate text-xs text-muted-foreground">{doc.filename}</div>
                          )}
                          {(doc.document_type || doc.source_context) && (
                            <div className="mt-1 flex flex-wrap gap-1">
                              {doc.document_type ? (
                                <Badge variant="outline" className="text-[10px]">
                                  {formatDocumentTypeLabel(doc.document_type)}
                                </Badge>
                              ) : null}
                              {doc.source_context ? (
                                <Badge variant="secondary" className="text-[10px]">
                                  {formatDocumentSourceContextLabel(doc.source_context)}
                                </Badge>
                              ) : null}
                            </div>
                          )}
                        </TableCell>
                        <TableCell className="hidden md:table-cell">
                          {doc.subject_employee_code ? (
                            <span className="text-sm font-medium">{doc.subject_employee_code}</span>
                          ) : (
                            <span className="text-xs text-muted-foreground">—</span>
                          )}
                        </TableCell>
                        <TableCell className="hidden md:table-cell">
                          <div className="text-sm font-medium">{formatUploaderLabel(doc)}</div>
                          {doc.uploaded_employee_code && doc.uploaded_employee_id ? (
                            <div className="text-xs text-muted-foreground">{doc.uploaded_employee_id}</div>
                          ) : null}
                        </TableCell>
                        <TableCell className="hidden sm:table-cell">
                          <div className="text-sm">{docs.formatDate(doc.uploaded_at)}</div>
                          <div className="text-xs text-muted-foreground">{docs.formatSize(doc.file_size)}</div>
                          <div className="mt-1">
                            {doc.is_locked ? (
                              <Badge variant="secondary" className="text-[10px]">Approved</Badge>
                            ) : (
                              <Badge variant="outline" className="text-[10px]">Draft</Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="whitespace-nowrap text-right">
                          <div className="flex items-center justify-end gap-1">
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              onClick={() => documentsAPI.openDocument(doc.filename)}
                            >
                              Open
                            </Button>
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              onClick={() => documentsAPI.downloadDocument(doc.filename)}
                            >
                              Download
                            </Button>
                            <AlertDialog
                              open={pendingDelete === doc.filename}
                              onOpenChange={(open) => !open && setPendingDelete(null)}
                            >
                              <AlertDialogTrigger asChild>
                                <Button
                                  type="button"
                                  variant="ghost"
                                  size="sm"
                                  className="text-red-600 hover:text-red-700"
                                  disabled={docs.deletingDocument === doc.filename || doc.is_locked}
                                  onClick={() => setPendingDelete(doc.filename)}
                                >
                                  {doc.is_locked ? "Locked" : "Delete"}
                                </Button>
                              </AlertDialogTrigger>
                              <AlertDialogContent>
                                <AlertDialogHeader>
                                  <AlertDialogTitle>Delete document?</AlertDialogTitle>
                                  <AlertDialogDescription>
                                    <strong>{doc.original_name || doc.filename}</strong> will be permanently removed. This action cannot be undone.
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                                  <AlertDialogAction
                                    className="bg-red-600 hover:bg-red-700"
                                    onClick={() => { docs.deleteDocument(doc.filename); setPendingDelete(null); }}
                                  >
                                    Delete
                                  </AlertDialogAction>
                                </AlertDialogFooter>
                              </AlertDialogContent>
                            </AlertDialog>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>                </div>              )}
            </div>

            {docs.documents.length > 0 ? (
              <div className="flex items-center justify-between gap-2 text-xs text-muted-foreground">
                <span>
                  Showing {docs.documents.length} of {docs.documentsTotal} document{docs.documentsTotal === 1 ? "" : "s"}
                </span>
                {docs.hasMoreDocuments ? (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => docs.loadMoreDocuments()}
                    disabled={docs.documentsLoading || docs.loadingMoreDocuments}
                  >
                    {docs.loadingMoreDocuments ? "Loading more" : "Load more"}
                  </Button>
                ) : null}
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </>
  );
}