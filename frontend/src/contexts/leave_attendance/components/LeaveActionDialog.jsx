import { useState } from "react";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Textarea } from "@/shared/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { getApiErrorMessage } from "@/shared/lib/utils";
import { leaveAPI } from "@/contexts/leave_attendance/api/leaveApi";
import { toast } from "sonner";
import { AlertTriangle } from "lucide-react";

/**
 * Shared dialog for leave workflow actions: recommend, sanction, reject, cancel.
 *
 * @param {Object}   props
 * @param {Object}   props.dialog   - { open, action, record }
 * @param {Function} props.onClose
 * @param {Function} props.onDone   - Called after successful action (triggers data refresh)
 */
export default function LeaveActionDialog({ dialog, onClose, onDone }) {
  const [remarks, setRemarks] = useState("");
  const [orderNumber, setOrderNumber] = useState("");
  const [orderDate, setOrderDate] = useState("");

  const reset = () => {
    setRemarks("");
    setOrderNumber("");
    setOrderDate("");
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const handleSubmit = async () => {
    if (!dialog.record) return;
    const leaveId = dialog.record.id;
    try {
      if (dialog.action === "recommend") {
        await leaveAPI.recommend(leaveId, remarks);
        toast.success("Leave recommended");
      } else if (dialog.action === "sanction") {
        await leaveAPI.sanction(leaveId, { remarks, order_number: orderNumber, order_date: orderDate });
        toast.success("Leave sanctioned");
      } else if (dialog.action === "reject") {
        await leaveAPI.reject(leaveId, remarks);
        toast.success("Leave rejected");
      } else if (dialog.action === "cancel") {
        await leaveAPI.cancel(leaveId, remarks);
        toast.success("Leave cancelled");
      }
      handleClose();
      onDone?.();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Action failed"));
    }
  };

  return (
    <Dialog open={dialog.open} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            {dialog.action === "sanction" && dialog.record?.leave_type_code === "CL" && dialog.record?.status === "SUBMITTED"
              ? "APPROVE"
              : dialog.action?.toUpperCase()}{" "}Leave
          </DialogTitle>
          <DialogDescription>
            <span className="font-medium">{dialog.record?.employee_name || dialog.record?.employee_id}</span>
            {" \u2022 "}
            {dialog.record?.leave_type_code} &bull; {dialog.record?.from_date} to {dialog.record?.to_date}
            {dialog.record?.days_applied != null && ` (${dialog.record.days_applied} days)`}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          {dialog.record?.reason && (
            <div className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">
              <span className="font-medium text-slate-500">Reason: </span>{dialog.record.reason}
            </div>
          )}
          {dialog.action === "sanction" && dialog.record?.recommended_by_name && (
            <div className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">
              <span className="font-medium text-slate-500">Recommended by: </span>{dialog.record.recommended_by_name}
            </div>
          )}
          {dialog.action === "sanction" && (
            <>
              <div className="space-y-1">
                <Label>Order Number</Label>
                <Input value={orderNumber} onChange={(e) => setOrderNumber(e.target.value)} />
              </div>
              <div className="space-y-1">
                <Label>Order Date</Label>
                <Input type="date" value={orderDate} onChange={(e) => setOrderDate(e.target.value)} />
              </div>
            </>
          )}
          <div className="space-y-1">
            <Label>Remarks</Label>
            <Textarea rows={3} value={remarks} onChange={(e) => setRemarks(e.target.value)} />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>Cancel</Button>
          <Button onClick={handleSubmit}>Confirm</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
