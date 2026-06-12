import { documentsAPI } from "@/modules/documents";
import {
  formatDocumentSourceContextLabel,
  formatDocumentTypeLabel,
} from "@/modules/change_requests/model/essChangeRequestDocumentDisplay";
import { cn } from "@/shared/lib/utils";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table";
import {
  ChevronDown,
  ChevronUp,
  FileText,
  Paperclip,
  RefreshCw,
  Trash2,
  Upload,
} from "lucide-react";

const EssChangeRequestDocumentPicker = ({
  canDeleteDocuments,
  docs,
  docsExpanded,
  form,
  setDocsExpanded,
}) => (
  <div className="grid gap-2">
    <Label className="flex items-center gap-1">
      <Paperclip className="h-3.5 w-3.5" />
      Supporting Documents (optional)
    </Label>
    <p className="text-xs text-muted-foreground">
      Upload PDF, images, or Office documents (max 10MB each).
    </p>

    {form.formAttachments.length > 0 && (
      <div className="space-y-1">
        {form.formAttachments.map((att, idx) => (
          <div key={idx} className="flex items-center justify-between rounded-md border bg-muted/50 px-3 py-2 text-sm">
            <div className="flex min-w-0 items-center gap-2">
              <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
              <span className="truncate">{att.original_name}</span>
              <span className="shrink-0 text-xs text-muted-foreground">
                ({(att.file_size / 1024).toFixed(0)} KB)
              </span>
            </div>
            <button
              type="button"
              className="ml-2 text-red-400 hover:text-red-600"
              onClick={() => form.setFormAttachments((prev) => prev.filter((_, i) => i !== idx))}
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    )}

    <div>
      <label
        className={cn(
          "inline-flex cursor-pointer items-center gap-2 rounded-md border border-dashed px-4 py-2 text-sm transition-colors hover:bg-muted",
          docs.uploading && "pointer-events-none opacity-50"
        )}
      >
        {docs.uploading ? (
          <RefreshCw className="h-4 w-4 animate-spin" />
        ) : (
          <Upload className="h-4 w-4" />
        )}
        {docs.uploading ? "Uploading" : "Choose file"}
        <input
          type="file"
          className="hidden"
          accept=".pdf,.jpg,.jpeg,.png,.webp,.doc,.docx,.xls,.xlsx"
          disabled={docs.uploading}
          onChange={async (e) => {
            const file = e.target.files?.[0];
            if (!file) return;
            e.target.value = "";
            await docs.uploadFile(file, { setFormAttachments: form.setFormAttachments });
          }}
        />
      </label>
    </div>

    <button
      type="button"
      className="flex w-full items-center justify-between rounded-md border border-dashed px-3 py-2 text-xs text-slate-500 transition-colors hover:bg-slate-50 hover:text-slate-700"
      onClick={() => setDocsExpanded((v) => !v)}
    >
      <span className="flex items-center gap-1.5 font-medium">
        {docsExpanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
        Browse previously uploaded files
      </span>
    </button>

    {docsExpanded && (
      <div className="space-y-2 rounded-md border p-3">
        <div className="flex items-center justify-between gap-2">
          <Label className="text-xs text-muted-foreground">Uploaded Documents</Label>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => docs.loadDocuments()}
            disabled={docs.documentsLoading || docs.loadingMoreDocuments}
          >
            <RefreshCw className={cn("h-3.5 w-3.5", (docs.documentsLoading || docs.loadingMoreDocuments) && "animate-spin")} />
          </Button>
        </div>
        <Input
          placeholder="Search by filename"
          value={docs.documentQuery}
          onChange={(e) => docs.setDocumentQuery(e.target.value)}
          className="h-8 text-xs"
        />
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          <Select value={docs.documentTypeFilter || "ALL"} onValueChange={(value) => docs.setDocumentTypeFilter(value === "ALL" ? "" : value)}>
            <SelectTrigger className="h-8 text-xs">
              <SelectValue placeholder="Filter by document type" />
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
          <Select value={docs.sourceContextFilter || "ALL"} onValueChange={(value) => docs.setSourceContextFilter(value === "ALL" ? "" : value)}>
            <SelectTrigger className="h-8 text-xs">
              <SelectValue placeholder="Filter by source" />
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
        </div>
        <div className="max-h-44 overflow-y-auto rounded-md border">
          {docs.documentsLoading ? (
            <div className="p-3 text-xs text-muted-foreground">Loading documents</div>
          ) : docs.documents.length === 0 ? (
            <div className="p-3 text-xs text-muted-foreground">No uploaded documents found.</div>
          ) : docs.visibleDocuments.length === 0 ? (
            <div className="p-3 text-xs text-muted-foreground">No uploaded documents match the selected filters.</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-xs">File</TableHead>
                  <TableHead className="hidden text-xs md:table-cell">Uploaded</TableHead>
                  <TableHead className="hidden text-xs sm:table-cell">Size</TableHead>
                  <TableHead className="hidden text-xs lg:table-cell">Status</TableHead>
                  <TableHead className="text-right text-xs">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {docs.visibleDocuments.map((doc) => (
                  <TableRow key={doc.filename}>
                    <TableCell className="max-w-[210px] text-xs">
                      <div className="truncate font-medium">{doc.original_name || doc.filename}</div>
                      <div className="truncate text-[10px] text-muted-foreground">{doc.filename}</div>
                      {(doc.document_type || doc.source_context) && (
                        <div className="mt-1 flex flex-wrap gap-1">
                          {doc.document_type && (
                            <Badge variant="outline" className="text-[10px]">
                              {formatDocumentTypeLabel(doc.document_type)}
                            </Badge>
                          )}
                          {doc.source_context && (
                            <Badge variant="secondary" className="text-[10px]">
                              {formatDocumentSourceContextLabel(doc.source_context)}
                            </Badge>
                          )}
                        </div>
                      )}
                    </TableCell>
                    <TableCell className="hidden text-xs md:table-cell">
                      {docs.formatDate(doc.uploaded_at)}
                    </TableCell>
                    <TableCell className="hidden text-xs sm:table-cell">
                      {docs.formatSize(doc.file_size)}
                    </TableCell>
                    <TableCell className="hidden text-xs lg:table-cell">
                      {doc.is_locked ? (
                        <Badge variant="secondary" className="text-[10px]">Approved</Badge>
                      ) : (
                        <Badge variant="outline" className="text-[10px]">Draft</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => docs.attachExistingDocument(doc, { formAttachments: form.formAttachments, setFormAttachments: form.setFormAttachments })}
                        >
                          Attach
                        </Button>
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
                        {canDeleteDocuments ? (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="text-red-600 hover:text-red-700"
                            disabled={docs.deletingDocument === doc.filename || doc.is_locked}
                            onClick={() => docs.handleDeleteDocument(doc.filename, { setFormAttachments: form.setFormAttachments })}
                          >
                            {doc.is_locked ? "Locked" : "Delete"}
                          </Button>
                        ) : null}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>
        {docs.documents.length > 0 && (
          <div className="flex items-center justify-between gap-2 text-[11px] text-muted-foreground">
            <span>
              Showing {docs.documents.length} of {docs.documentsTotal} uploaded document{docs.documentsTotal === 1 ? "" : "s"}
            </span>
            {docs.hasMoreDocuments ? (
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="h-7 text-[11px]"
                onClick={() => docs.loadMoreDocuments()}
                disabled={docs.documentsLoading || docs.loadingMoreDocuments}
              >
                {docs.loadingMoreDocuments ? (
                  <>
                    <RefreshCw className="mr-1 h-3 w-3 animate-spin" />
                    Loading more
                  </>
                ) : (
                  "Load more"
                )}
              </Button>
            ) : null}
          </div>
        )}
      </div>
    )}
  </div>
);

export default EssChangeRequestDocumentPicker;
