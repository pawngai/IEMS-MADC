import { CheckSquare, Upload } from "lucide-react";
import { useRef } from "react";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";

const ITEMS = ["Appointment order", "Identity proof", "Joining report", "Nomination form"];

const OpeningDocumentChecklist = ({ documents = [], disabled, uploading, onUpload }) => {
  const inputRef = useRef(null);
  const uploaded = new Set(documents.map((doc) => String(doc.type || doc.document_type || doc.name || "").toLowerCase()));
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="text-lg">Documents</CardTitle>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="gap-2"
            disabled={disabled || uploading}
            onClick={() => inputRef.current?.click()}
          >
            <Upload className="w-4 h-4" />
            {uploading ? "Uploading..." : "Upload"}
          </Button>
          <input
            ref={inputRef}
            type="file"
            className="hidden"
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) onUpload?.(file);
              event.target.value = "";
            }}
            aria-label="Upload opening document"
          />
        </div>
      </CardHeader>
      <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {ITEMS.map((item) => (
          <div key={item} className="flex items-center gap-2 text-sm text-slate-600">
            <CheckSquare className={`w-4 h-4 ${uploaded.has(item.toLowerCase()) ? "text-emerald-600" : "text-slate-300"}`} />
            {item}
          </div>
        ))}
      </CardContent>
    </Card>
  );
};

export default OpeningDocumentChecklist;
