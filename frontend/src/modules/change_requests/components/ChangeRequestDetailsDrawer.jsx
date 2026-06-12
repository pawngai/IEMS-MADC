import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/shared/ui/dialog";
import { Badge } from "@/shared/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table";
import { Paperclip } from "lucide-react";

const STATUS_STYLES = {
  PENDING: "bg-amber-100 text-amber-700",
  APPROVED: "bg-blue-100 text-blue-700",
  APPLIED: "bg-green-100 text-green-700",
  REJECTED: "bg-red-100 text-red-700",
  CANCELLED: "bg-slate-100 text-slate-700",
};

const ChangeRequestDetailsDrawer = ({
  request,
  onClose,
  profileCategoryLabels,
  serviceBookCategoryLabels,
  getDownloadUrl,
  getAttachmentFilename,
}) => {
  return (
    <Dialog open={!!request} onOpenChange={() => onClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Change Request {request?.request_id}</DialogTitle>
          <DialogDescription>
            {request?.request_type === "PROFILE" ? "Profile" : "Service Book"}{" "}
            {request?.request_type === "PROFILE"
              ? profileCategoryLabels[request?.category]?.label
              : serviceBookCategoryLabels[request?.category]?.label}
          </DialogDescription>
        </DialogHeader>
        {request && (
          <div className="space-y-4 text-sm">
            <div className="flex items-center gap-2">
              <span className="font-medium">Status:</span>
              <Badge className={STATUS_STYLES[request.status]}>{request.status}</Badge>
            </div>

            <div>
              <span className="font-medium">Requested Changes:</span>
              <div className="mt-2 rounded-md border overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-xs">Field</TableHead>
                      <TableHead className="text-xs">Current</TableHead>
                      <TableHead className="text-xs">Requested</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {request.fields?.map((field, index) => (
                      <TableRow key={index}>
                        <TableCell className="text-xs font-medium">{field.field_label || field.field_name}</TableCell>
                        <TableCell className="text-xs text-muted-foreground">{field.current_value || ""}</TableCell>
                        <TableCell className="text-xs font-semibold text-blue-700">{field.requested_value}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>

            <div>
              <span className="font-medium">Reason:</span>
              <p className="mt-1 text-muted-foreground">{request.reason}</p>
            </div>

            {request.attachments?.length > 0 && (
              <div>
                <span className="font-medium">Attachments:</span>
                <div className="mt-1 space-y-1">
                  {request.attachments.map((attachment, index) => {
                    const filename = getAttachmentFilename(attachment);
                    return (
                      <div key={index} className="flex items-center justify-between gap-2 rounded-md border px-3 py-1.5 text-xs">
                        <div className="flex items-center gap-2 min-w-0">
                          <Paperclip className="h-3 w-3 text-muted-foreground" />
                          <span className="truncate">{attachment.original_name || attachment.filename}</span>
                        </div>
                        <a
                          href={filename ? getDownloadUrl(filename) : attachment.url}
                          className="text-blue-600 hover:text-blue-700 font-medium"
                        >
                          Download
                        </a>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default ChangeRequestDetailsDrawer;
