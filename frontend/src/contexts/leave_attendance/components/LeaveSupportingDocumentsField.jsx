import { useState } from "react";
import { documentsAPI } from "@/contexts/documents";
import { useLeaveDocuments } from "@/contexts/leave_attendance/hooks/useLeaveDocuments";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { ChevronDown, ChevronUp, FileText, Paperclip, Upload, X } from "lucide-react";

const ATTACHMENT_ACCEPT = ".pdf,.jpg,.jpeg,.png,.webp,.doc,.docx,.xls,.xlsx";

const getLeaveAttachmentHref = (attachment) => {
  const filename = String(attachment?.filename || "").trim();
  if (filename) {
    return documentsAPI.getFileUrl(filename);
  }
  const directUrl = String(attachment?.url || "").trim();
  return directUrl.startsWith("/api/documents/files/") ? directUrl : "";
};

const formatSourceContext = (value) => {
  const normalized = String(value || "").trim();
  if (!normalized) return "";
  if (normalized === "leave.apply") return "Leave Upload";
  return normalized;
};

export default function LeaveSupportingDocumentsField({
  attachments,
  setAttachments,
  requirementMessage = null,
  recommendation = null,
}) {
  const [browserOpen, setBrowserOpen] = useState(false);
  const recommendedDocumentTypeLabel = recommendation?.documentTypeLabel || "";
  const recommendedDocumentType = recommendation?.documentType || "";
  const docs = useLeaveDocuments({
    open: browserOpen,
    recommendedDocumentType,
  });

  return (
    <div className="space-y-3 md:col-span-2">
      <div>
        <Label className="flex items-center gap-1.5">
          <Paperclip className="h-3.5 w-3.5" />
          Supporting Documents
        </Label>
        {requirementMessage ? (
          <div className="mt-1 space-y-1">
            <p className="text-xs font-medium text-amber-700">
              Required for this leave type. {requirementMessage}
            </p>
            {recommendedDocumentTypeLabel ? (
              <p className="text-xs text-slate-500">
                Recommended document type: <span className="font-medium text-slate-700">{recommendedDocumentTypeLabel}</span>
              </p>
            ) : null}
          </div>
        ) : (
          <p className="mt-1 text-xs text-slate-500">
            Attach medical certificates, birth records, or other evidence supporting the leave request.
          </p>
        )}
      </div>

      {attachments.length > 0 && (
        <div className="space-y-2 rounded-lg border border-slate-200 bg-slate-50/70 p-3">
          {attachments.map((attachment, index) => {
            const filename = docs.getAttachmentFilename(attachment);
            const href = getLeaveAttachmentHref(attachment);
            return (
              <div key={`${filename || "attachment"}-${index}`} className="flex items-start justify-between gap-3 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 shrink-0 text-slate-500" />
                    <span className="truncate font-medium text-slate-700">
                      {attachment.original_name || filename || "Attached document"}
                    </span>
                    {attachment.file_size ? (
                      <span className="shrink-0 text-xs text-slate-400">{docs.formatSize(attachment.file_size)}</span>
                    ) : null}
                  </div>
                  {filename && <p className="mt-1 truncate text-xs text-slate-400">{filename}</p>}
                </div>
                <div className="flex items-center gap-2">
                  {href ? (
                    <Button type="button" variant="ghost" size="sm" asChild>
                      <a href={href} target="_blank" rel="noopener noreferrer">Open</a>
                    </Button>
                  ) : null}
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-slate-500 hover:text-red-600"
                    onClick={() => setAttachments((prev) => prev.filter((_, currentIndex) => currentIndex !== index))}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2">
        <label className={`inline-flex cursor-pointer items-center gap-2 rounded-md border border-dashed px-4 py-2 text-sm transition-colors hover:bg-slate-50 ${docs.uploading ? "pointer-events-none opacity-60" : ""}`}>
          <Upload className={`h-4 w-4 ${docs.uploading ? "animate-pulse" : ""}`} />
          {docs.uploading ? "Uploading..." : "Choose file"}
          <input
            type="file"
            className="hidden"
            accept={ATTACHMENT_ACCEPT}
            disabled={docs.uploading}
            onChange={async (event) => {
              const file = event.target.files?.[0];
              if (!file) return;
              event.target.value = "";
              await docs.uploadFile(file, { setAttachments });
            }}
          />
        </label>
        <Button type="button" variant="outline" size="sm" onClick={() => setBrowserOpen((open) => !open)}>
          {browserOpen ? <ChevronUp className="mr-1 h-4 w-4" /> : <ChevronDown className="mr-1 h-4 w-4" />}
          Browse uploaded files
        </Button>
      </div>

      {browserOpen && (
        <div className="space-y-3 rounded-lg border border-slate-200 p-3">
          <Input
            value={docs.documentQuery}
            onChange={(event) => docs.setDocumentQuery(event.target.value)}
            placeholder="Search uploaded documents by filename"
          />

          <div className="max-h-56 space-y-2 overflow-y-auto rounded-md border border-slate-200 p-2">
            {docs.documentsLoading ? (
              <div className="px-2 py-6 text-sm text-slate-500">Loading documents...</div>
            ) : docs.visibleDocuments.length === 0 ? (
              <div className="px-2 py-6 text-sm text-slate-500">No matching uploaded documents found.</div>
            ) : (
              docs.visibleDocuments.map((document) => (
                <div key={document.filename} className="flex items-start justify-between gap-3 rounded-md border border-slate-200 px-3 py-2">
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-slate-800">
                      {document.original_name || document.filename}
                    </p>
                    <p className="truncate text-xs text-slate-400">{document.filename}</p>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {document.document_type ? (
                        <Badge variant="outline" className="text-[10px]">
                          {document.document_type}
                        </Badge>
                      ) : null}
                      {document.source_context ? (
                        <Badge variant="secondary" className="text-[10px]">
                          {formatSourceContext(document.source_context)}
                        </Badge>
                      ) : null}
                    </div>
                    {document.uploaded_at ? (
                      <p className="mt-1 text-xs text-slate-400">Uploaded {docs.formatDate(document.uploaded_at)}</p>
                    ) : null}
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => docs.attachExistingDocument(document, { attachments, setAttachments })}
                    >
                      Attach
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => documentsAPI.downloadDocument(document.filename, { suggestedName: document.original_name })}
                    >
                      Download
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>

          {docs.hasMoreDocuments ? (
            <div className="flex justify-end">
              <Button type="button" variant="outline" size="sm" onClick={() => docs.loadMoreDocuments()} disabled={docs.loadingMoreDocuments}>
                {docs.loadingMoreDocuments ? "Loading..." : "Load More"}
              </Button>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}