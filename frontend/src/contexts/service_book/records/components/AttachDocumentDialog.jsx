import { useEffect, useState } from "react";
import { serviceBookRecordsAPI } from "@/contexts/service_book/records/api/serviceBookRecordsApi";
import {
  buildAttachDocumentCommand,
  getServiceRecordDisplayLabel,
} from "@/contexts/service_book/records/model/serviceBookRecordsModel";
import { formatDocumentMetadataErrorMessage, getApiErrorMessage } from "@/shared/lib/utils";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/shared/ui/sheet";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Badge } from "@/shared/ui/badge";
import { ScrollArea } from "@/shared/ui/scroll-area";
import { Separator } from "@/shared/ui/separator";
import { toast } from "sonner";
import { Loader2, Upload } from "lucide-react";

const DOCUMENT_TYPE_OPTIONS = ["", "ORDER", "NOTIFICATION", "MEMORANDUM", "CERTIFICATE", "REPORT"];

const formatDocumentDate = (value) => {
  if (!value) return "";
  try {
    return new Date(value).toLocaleDateString("en-IN");
  } catch {
    return "";
  }
};

const AttachDocumentDialog = ({ event, employeeCode, onSuccess, onClose }) => {
  const eventId = event.id || event.service_event_id;
  const eventLabel = getServiceRecordDisplayLabel(event).toLowerCase();
  const [documentSearch, setDocumentSearch] = useState("");
  const [documents, setDocuments] = useState([]);
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [selectedDocumentType, setSelectedDocumentType] = useState("");
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadDocumentType, setUploadDocumentType] = useState("ORDER");
  const [uploadCategory, setUploadCategory] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const loadDocuments = async () => {
      setLoadingDocuments(true);
      try {
        const response = await serviceBookRecordsAPI.listAccessibleDocuments({
          query: documentSearch.trim() || undefined,
          limit: 12,
          offset: 0,
        });
        if (!cancelled) {
          setDocuments(Array.isArray(response?.data?.items) ? response.data.items : []);
        }
      } catch (err) {
        if (!cancelled) {
          toast.error(getApiErrorMessage(err, "Failed to load documents"));
        }
      } finally {
        if (!cancelled) {
          setLoadingDocuments(false);
        }
      }
    };

    loadDocuments();

    return () => {
      cancelled = true;
    };
  }, [documentSearch]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedDocumentId.trim() && !uploadFile) {
      toast.error("Select an existing document or upload a new one");
      return;
    }

    setSaving(true);
    try {
      let resolvedDocumentId = selectedDocumentId.trim();
      let resolvedDocumentType = selectedDocumentType.trim() || null;

      if (!resolvedDocumentId && uploadFile) {
        const uploadResponse = await serviceBookRecordsAPI.uploadLinkedDocument(uploadFile, {
          entity_type: "SERVICE_RECORD",
          entity_id: eventId,
          document_type: uploadDocumentType || undefined,
          category: uploadCategory || undefined,
          source_context: "service_book.records.attach",
          owner_employee_code: employeeCode || undefined,
        });
        const uploadData = uploadResponse?.data || {};
        resolvedDocumentId = String(uploadData.document_id || uploadData.filename || "").trim();
        resolvedDocumentType = String(
          uploadData?.metadata?.document_type || uploadDocumentType || "",
        ).trim() || null;
        if (!resolvedDocumentId) {
          throw new Error("Uploaded document did not return a document ID");
        }
      }

      const cmd = buildAttachDocumentCommand({
        serviceEventId: eventId,
        documentId: resolvedDocumentId,
        documentType: resolvedDocumentType,
      });
      await serviceBookRecordsAPI.attachDocument(eventId, cmd);
      toast.success(uploadFile && !selectedDocumentId ? "Document uploaded and attached" : "Document attached");
      onSuccess();
    } catch (err) {
      const metadataMessage = formatDocumentMetadataErrorMessage(err);
      if (metadataMessage) {
        toast.error(metadataMessage);
      } else {
        toast.error(getApiErrorMessage(err, "Failed to attach document"));
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <Sheet open onOpenChange={(open) => !open && onClose()}>
      <SheetContent side="right" size="md">
        <SheetHeader>
          <SheetTitle>Attach Document</SheetTitle>
          <SheetDescription>
            Attach a supporting document to the {eventLabel} event. Choose an existing document from your accessible uploads or upload a new one directly from this panel.
          </SheetDescription>
        </SheetHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="documentSearch">Choose Existing Document</Label>
            <Input
              id="documentSearch"
              placeholder="Search by file name or document name"
              value={documentSearch}
              onChange={(e) => setDocumentSearch(e.target.value)}
            />
            <div className="rounded-md border bg-muted/20">
              <ScrollArea className="h-56">
                <div className="space-y-2 p-2">
                  {loadingDocuments ? (
                    <div className="flex items-center gap-2 px-2 py-6 text-sm text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Loading recent documents...
                    </div>
                  ) : documents.length === 0 ? (
                    <div className="px-2 py-6 text-sm text-muted-foreground">
                      No matching documents were found.
                    </div>
                  ) : (
                    documents.map((document) => {
                      const documentId = String(document.document_id || document.filename || "");
                      const selected = documentId === selectedDocumentId;
                      return (
                        <button
                          key={documentId}
                          type="button"
                          className={`w-full rounded-md border px-3 py-2 text-left transition ${selected ? "border-primary bg-primary/5" : "border-border bg-background hover:bg-muted/50"}`}
                          onClick={() => {
                            if (selected) {
                              setSelectedDocumentId("");
                              setSelectedDocumentType("");
                              return;
                            }
                            setSelectedDocumentId(documentId);
                            setSelectedDocumentType(String(document.document_type || ""));
                          }}
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <p className="truncate text-sm font-medium">
                                {document.original_name || document.filename}
                              </p>
                              <p className="truncate text-xs text-muted-foreground">
                                {documentId}
                              </p>
                            </div>
                            {selected && <Badge variant="secondary">Selected</Badge>}
                          </div>
                          <div className="mt-2 flex flex-wrap gap-2">
                            {document.document_type && (
                              <Badge variant="outline">{document.document_type}</Badge>
                            )}
                            {document.category && (
                              <Badge variant="outline">{document.category}</Badge>
                            )}
                            {document.source_context && (
                              <Badge variant="outline">{document.source_context}</Badge>
                            )}
                          </div>
                          {document.uploaded_at && (
                            <p className="mt-2 text-xs text-muted-foreground">
                              Uploaded {formatDocumentDate(document.uploaded_at)}
                            </p>
                          )}
                        </button>
                      );
                    })
                  )}
                </div>
              </ScrollArea>
            </div>
            <p className="text-xs text-muted-foreground">
              Pick an existing document here, or leave this blank and upload a new one below.
            </p>
          </div>

          <Separator />

          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="uploadDocument">Upload New Document</Label>
              <label className="flex cursor-pointer items-center justify-between rounded-md border border-dashed px-3 py-3 text-sm hover:bg-muted/50">
                <span className="truncate pr-3 text-muted-foreground">
                  {uploadFile ? uploadFile.name : "Choose a file to upload and attach"}
                </span>
                <span className="inline-flex items-center gap-2 font-medium text-foreground">
                  <Upload className="h-4 w-4" />
                  Browse
                </span>
                <input
                  id="uploadDocument"
                  type="file"
                  className="hidden"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  disabled={saving}
                />
              </label>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="documentType">Document Type</Label>
                <Input
                  id="documentType"
                  list="service-record-document-types"
                  placeholder="e.g., ORDER"
                  value={uploadDocumentType}
                  onChange={(e) => setUploadDocumentType(e.target.value.toUpperCase())}
                />
                <datalist id="service-record-document-types">
                  {DOCUMENT_TYPE_OPTIONS.filter(Boolean).map((option) => (
                    <option key={option} value={option} />
                  ))}
                </datalist>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="documentCategory">Category (optional)</Label>
                <Input
                  id="documentCategory"
                  placeholder="e.g., PROMOTION_ORDER"
                  value={uploadCategory}
                  onChange={(e) => setUploadCategory(e.target.value.toUpperCase().replaceAll(" ", "_").replaceAll("-", "_"))}
                />
              </div>
            </div>

            <p className="text-xs text-muted-foreground">
              New uploads are stored through the documents context with a Service Book record link and the source context set to service_book.records.attach.
            </p>
          </div>

          <div className="rounded-md border bg-muted/20 px-3 py-2 text-xs text-muted-foreground">
            Selected document: {selectedDocumentId || (uploadFile ? uploadFile.name : "None")}
          </div>

          <div className="space-y-1.5 hidden">
            <Input
              readOnly
              value={selectedDocumentType}
            />
          </div>

          <SheetFooter className="mt-4">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={saving}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={saving} className="gap-1">
              {saving && <Loader2 className="w-4 h-4 animate-spin" />}
              Attach Document
            </Button>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  );
};

export default AttachDocumentDialog;
