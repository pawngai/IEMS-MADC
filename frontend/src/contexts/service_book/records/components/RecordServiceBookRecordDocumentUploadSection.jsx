import {
  DOCUMENT_TYPE_OPTIONS,
  normalizeDocumentCategoryValue,
} from "@/contexts/service_book/records/model/recordServiceBookRecordDialogModel";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Upload } from "lucide-react";

const RecordServiceBookRecordDocumentUploadSection = ({
  selectedEventLabel,
  uploadFile,
  uploadDocumentType,
  uploadCategory,
  saving,
  onUploadFileChange,
  onUploadDocumentTypeChange,
  onUploadCategoryChange,
}) => (
  <div className="space-y-3 rounded-md border border-border p-3">
    <div>
      <p className="text-sm font-semibold">Supporting Document</p>
      <p className="mt-1 text-xs text-muted-foreground">
        Optional. Upload a document now and it will be attached after this {selectedEventLabel.toLowerCase()} event is recorded.
      </p>
    </div>

    <div className="space-y-1.5">
      <Label htmlFor="recordEventUpload">Upload New Document</Label>
      <label className="flex cursor-pointer items-center justify-between rounded-md border border-dashed px-3 py-3 text-sm hover:bg-muted/50">
        <span className="truncate pr-3 text-muted-foreground">
          {uploadFile ? uploadFile.name : "Choose a file to upload and attach"}
        </span>
        <span className="inline-flex items-center gap-2 font-medium text-foreground">
          <Upload className="h-4 w-4" />
          Browse
        </span>
        <input
          id="recordEventUpload"
          type="file"
          className="hidden"
          onChange={(event) => onUploadFileChange(event.target.files?.[0] || null)}
          disabled={saving}
        />
      </label>
    </div>

    <div className="grid gap-3 sm:grid-cols-2">
      <div className="space-y-1.5">
        <Label htmlFor="recordEventDocumentType">Document Type</Label>
        <Input
          id="recordEventDocumentType"
          list="record-service-record-document-types"
          placeholder="e.g., ORDER"
          value={uploadDocumentType}
          onChange={(event) => onUploadDocumentTypeChange(event.target.value.toUpperCase())}
        />
        <datalist id="record-service-record-document-types">
          {DOCUMENT_TYPE_OPTIONS.map((option) => (
            <option key={option} value={option} />
          ))}
        </datalist>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="recordEventDocumentCategory">Category (optional)</Label>
        <Input
          id="recordEventDocumentCategory"
          placeholder="e.g., PROMOTION_ORDER"
          value={uploadCategory}
          onChange={(event) => onUploadCategoryChange(normalizeDocumentCategoryValue(event.target.value))}
        />
      </div>
    </div>
  </div>
);

export default RecordServiceBookRecordDocumentUploadSection;
