import { useState } from "react";
import { serviceBookRecordsAPI } from "@/modules/service_book/records/api/serviceBookRecordsApi";
import {
  buildVoidCommand,
  getServiceRecordDisplayLabel,
} from "@/modules/service_book/records/model/serviceBookRecordsModel";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/shared/ui/sheet";
import { Button } from "@/shared/ui/button";
import { Label } from "@/shared/ui/label";
import { toast } from "sonner";
import { Loader2, AlertTriangle } from "lucide-react";

const VoidServiceBookRecordDialog = ({ event, onSuccess, onClose }) => {
  const eventId = event.id || event.service_event_id;
  const eventLabel = getServiceRecordDisplayLabel(event).toLowerCase();
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!reason.trim()) {
      toast.error("A reason is required to void a Service Book record");
      return;
    }

    setSaving(true);
    try {
      const cmd = buildVoidCommand({
        serviceEventId: eventId,
        reason: reason.trim(),
      });
      await serviceBookRecordsAPI.voidEvent(eventId, cmd);
      onSuccess();
    } catch (err) {
      const msg =
        err?.response?.data?.detail || err.message || "Failed to void event";
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Sheet open onOpenChange={(open) => !open && onClose()}>
      <SheetContent side="right" size="md">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2 text-red-700">
            <AlertTriangle className="w-5 h-5" />
            Void Service Book Record
          </SheetTitle>
          <SheetDescription>
            This will permanently void the {eventLabel} event. The event will remain in
            the record but will be marked as voided and will no longer affect the
            service book read model.
          </SheetDescription>
        </SheetHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="voidReason">Reason for Voiding *</Label>
            <textarea
              id="voidReason"
              className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              placeholder="Explain why this event should be voided..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              required
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
            <Button
              type="submit"
              variant="destructive"
              disabled={saving}
              className="gap-1"
            >
              {saving && <Loader2 className="w-4 h-4 animate-spin" />}
              Void Event
            </Button>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  );
};

export default VoidServiceBookRecordDialog;
