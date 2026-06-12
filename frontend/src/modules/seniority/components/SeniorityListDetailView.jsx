import {
  ArrowLeft,
  ArrowUpCircle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Download,
  Edit2,
  ListOrdered,
  Loader2,
  Send,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { TableSkeleton } from "@/shared/ui/skeletons";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";
import { Textarea } from "@/shared/ui/textarea";
import { getReadablePersonName } from "@/shared/lib/readablePersonName";
import {
  ListTypeBadge,
  PROMOTION_LABELS,
  StatusBadge,
  buildRankValidationMessage,
  buildSwappedRankEdits,
  formatDateTime,
  formatDesignation,
  formatGeneratedListTitle,
  formatGroupLabel,
  formatServiceLabel,
  formatVersionLabel,
  getEffectiveRank,
} from "@/modules/seniority/components/SeniorityListsTab.helpers";

const SeniorityListDetailView = ({
  detail,
  detailLoading,
  transitioning,
  isDataEntry,
  isVerifier,
  isApprover,
  editingRanks,
  setEditingRanks,
  rankEdits,
  setRankEdits,
  setDetail,
  setRemarksDialog,
  remarksDialog,
  remarks,
  setRemarks,
  handleSaveRanks,
  handleWorkflowAction,
  exportCSV,
}) => {
  const listType = detail.list_type || "DRAFT";
  const canEdit = isDataEntry && (detail.status === "DRAFT" || detail.status === "REJECTED") && listType !== "FINAL";
  const canSubmit = isDataEntry && (detail.status === "DRAFT" || detail.status === "REJECTED");
  const canVerify = isVerifier && detail.status === "SUBMITTED";
  const canApprove = isApprover && detail.status === "VERIFIED";
  const canReject = (isVerifier && detail.status === "SUBMITTED") || (isApprover && detail.status === "VERIFIED");
  const canPromote = isDataEntry && detail.status === "APPROVED" && (detail.list_type || "DRAFT") !== "FINAL";
  const rankValidationMessage = editingRanks ? buildRankValidationMessage(detail.employees, rankEdits) : "";
  const orderedEmployees = editingRanks
    ? [...(detail.employees || [])].sort((left, right) => {
      const leftRank = getEffectiveRank(left, rankEdits);
      const rightRank = getEffectiveRank(right, rankEdits);
      if (leftRank !== rightRank) return leftRank - rightRank;
      return String(left.employee_id).localeCompare(String(right.employee_id));
    })
    : (detail.employees || []);
  const hasRankChanges = Object.entries(rankEdits).some(([employeeId, value]) => {
    const employee = (detail.employees || []).find((item) => item.employee_id === employeeId);
    if (!employee) return false;
    return Number(value) !== Number(employee.rank);
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Button variant="ghost" size="sm" onClick={() => setDetail(null)} className="gap-1">
          <ArrowLeft className="w-4 h-4" /> Back to Lists
        </Button>
        <div className="flex flex-wrap items-center gap-2">
          <ListTypeBadge listType={detail.list_type} prefix="Type" />
          <StatusBadge status={detail.status} prefix="Status" />
          <Button variant="outline" size="sm" onClick={() => exportCSV(detail.list_id)} className="gap-1">
            <Download className="w-4 h-4" /> Export CSV
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <ListOrdered className="w-4 h-4" />
            {formatGeneratedListTitle(detail.title)}
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Service: {formatServiceLabel(detail.service)} | Designation: {formatDesignation(detail.designation_code)} | Total: {detail.total}
          </p>
          <p className="text-xs text-muted-foreground">
            {formatVersionLabel(detail.version)}
          </p>
        </CardHeader>
        <CardContent>
          {(detail.created_by || detail.submitted_by || detail.verified_by || detail.approved_by) && (
            <div className="mb-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs rounded-lg bg-muted/50 p-3">
              {detail.created_by && (
                <div>
                  <span className="text-muted-foreground block">Created by</span>
                  <span className="font-medium">{detail.created_by_name || detail.created_by}</span>
                  {detail.created_at && <span className="text-muted-foreground block">{formatDateTime(detail.created_at)}</span>}
                </div>
              )}
              {detail.submitted_by && (
                <div>
                  <span className="text-muted-foreground block">Submitted by</span>
                  <span className="font-medium">{detail.submitted_by_name || detail.submitted_by}</span>
                  {detail.submitted_at && <span className="text-muted-foreground block">{formatDateTime(detail.submitted_at)}</span>}
                </div>
              )}
              {detail.verified_by && (
                <div>
                  <span className="text-muted-foreground block">Verified by</span>
                  <span className="font-medium">{detail.verified_by_name || detail.verified_by}</span>
                  {detail.verified_at && <span className="text-muted-foreground block">{formatDateTime(detail.verified_at)}</span>}
                </div>
              )}
              {detail.approved_by && (
                <div>
                  <span className="text-muted-foreground block">Approved by</span>
                  <span className="font-medium">{detail.approved_by_name || detail.approved_by}</span>
                  {detail.approved_at && <span className="text-muted-foreground block">{formatDateTime(detail.approved_at)}</span>}
                </div>
              )}
              {detail.remarks && (
                <div className="col-span-2 sm:col-span-4">
                  <span className="text-muted-foreground block">Remarks</span>
                  <span>{detail.remarks}</span>
                </div>
              )}
            </div>
          )}

          <div className="flex flex-wrap items-center gap-2 mb-4">
            {canEdit && !editingRanks && (
              <Button variant="outline" size="sm" onClick={() => setEditingRanks(true)} className="gap-1">
                <Edit2 className="w-3 h-3" /> Edit Ranks
              </Button>
            )}
            {editingRanks && (
              <>
                <Button size="sm" onClick={handleSaveRanks} className="gap-1" disabled={!hasRankChanges || Boolean(rankValidationMessage)}>
                  <CheckCircle className="w-3 h-3" /> Save Ranks
                </Button>
                <Button variant="ghost" size="sm" onClick={() => { setEditingRanks(false); setRankEdits({}); }}>
                  Cancel
                </Button>
              </>
            )}
            {canSubmit && (
              <Button size="sm" onClick={() => setRemarksDialog({ open: true, action: "submit", listId: detail.list_id })} className="gap-1">
                <Send className="w-3 h-3" /> Submit
              </Button>
            )}
            {canVerify && (
              <Button size="sm" variant="outline" onClick={() => setRemarksDialog({ open: true, action: "verify", listId: detail.list_id })} className="gap-1">
                <ShieldCheck className="w-3 h-3" /> Verify
              </Button>
            )}
            {canApprove && (
              <Button size="sm" onClick={() => setRemarksDialog({ open: true, action: "approve", listId: detail.list_id })} className="gap-1">
                <CheckCircle className="w-3 h-3" /> Approve
              </Button>
            )}
            {canReject && (
              <Button size="sm" variant="destructive" onClick={() => setRemarksDialog({ open: true, action: "reject", listId: detail.list_id })} className="gap-1">
                <XCircle className="w-3 h-3" /> Reject
              </Button>
            )}
            {canPromote && (
              <Button size="sm" variant="outline" onClick={() => setRemarksDialog({ open: true, action: "promote", listId: detail.list_id })} className="gap-1 border-amber-500 text-amber-700 hover:bg-amber-50">
                <ArrowUpCircle className="w-3 h-3" /> {PROMOTION_LABELS[detail.list_type || "DRAFT"]}
              </Button>
            )}
          </div>
          {editingRanks && (
            <p className={`mb-4 text-xs ${rankValidationMessage ? "text-red-600" : "text-muted-foreground"}`}>
              {rankValidationMessage || `Use the arrows for quick swaps, or type a full unique ranking from 1 to ${(detail.employees || []).length}.`}
            </p>
          )}

          {detailLoading ? (
            <TableSkeleton rows={8} columns={10} />
          ) : (
            <div className="rounded-md border overflow-auto max-h-[60vh]">
              <Table className="min-w-[900px]">
                <TableHeader className="sticky top-0 bg-background z-10">
                  <TableRow>
                    <TableHead className="w-16">Rank</TableHead>
                    <TableHead>Code</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Department</TableHead>
                    <TableHead>Initial Appointment</TableHead>
                    <TableHead>Service</TableHead>
                    <TableHead>Group</TableHead>
                    <TableHead>Latest Appointment</TableHead>
                    <TableHead>Confirmation</TableHead>
                    <TableHead>Last Promotion</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {orderedEmployees.map((emp, index) => (
                    <TableRow key={emp.employee_id}>
                      <TableCell>
                        {editingRanks ? (
                          <div className="flex items-center gap-1">
                            <Input
                              type="number"
                              min={1}
                              className="w-16 h-7 text-xs"
                              value={rankEdits[emp.employee_id] ?? String(emp.rank)}
                              onChange={(e) => setRankEdits((prev) => ({ ...prev, [emp.employee_id]: e.target.value }))}
                            />
                            <div className="flex flex-col gap-1">
                              <Button
                                type="button"
                                variant="outline"
                                size="icon"
                                className="h-6 w-6"
                                aria-label={`Move ${getReadablePersonName(emp.full_name) || emp.employee_code || emp.employee_id} up`}
                                disabled={Boolean(rankValidationMessage) || index === 0}
                                onClick={() => setRankEdits((prev) => buildSwappedRankEdits({
                                  employees: detail.employees,
                                  rankEdits: prev,
                                  employeeId: emp.employee_id,
                                  direction: "up",
                                }))}
                              >
                                <ChevronUp className="h-3 w-3" />
                              </Button>
                              <Button
                                type="button"
                                variant="outline"
                                size="icon"
                                className="h-6 w-6"
                                aria-label={`Move ${getReadablePersonName(emp.full_name) || emp.employee_code || emp.employee_id} down`}
                                disabled={Boolean(rankValidationMessage) || index === orderedEmployees.length - 1}
                                onClick={() => setRankEdits((prev) => buildSwappedRankEdits({
                                  employees: detail.employees,
                                  rankEdits: prev,
                                  employeeId: emp.employee_id,
                                  direction: "down",
                                }))}
                              >
                                <ChevronDown className="h-3 w-3" />
                              </Button>
                            </div>
                          </div>
                        ) : (
                          emp.rank
                        )}
                      </TableCell>
                      <TableCell className="font-mono text-xs">{emp.employee_code || "-"}</TableCell>
                      <TableCell>{getReadablePersonName(emp.full_name) || "-"}</TableCell>
                      <TableCell>{emp.department_code}</TableCell>
                      <TableCell>{emp.date_of_initial_engagement}</TableCell>
                      <TableCell>{formatServiceLabel(emp.service)}</TableCell>
                      <TableCell>{formatGroupLabel(emp.group)}</TableCell>
                      <TableCell>{emp.appointment_date || "-"}</TableCell>
                      <TableCell>{emp.confirmation_date || "-"}</TableCell>
                      <TableCell>{emp.last_promotion_date || "-"}</TableCell>
                    </TableRow>
                  ))}
                  {(!detail.employees || detail.employees.length === 0) && (
                    <TableRow>
                      <TableCell colSpan={10} className="text-center text-muted-foreground py-8">
                        No employees in this list
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={remarksDialog.open} onOpenChange={(open) => { if (!open) setRemarksDialog({ open: false, action: "", listId: "" }); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="capitalize">{remarksDialog.action} Seniority List</DialogTitle>
            <DialogDescription>Add optional remarks for this action.</DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label>Remarks</Label>
            <Textarea value={remarks} onChange={(e) => setRemarks(e.target.value)} placeholder="Optional remarks..." />
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setRemarksDialog({ open: false, action: "", listId: "" })}>Cancel</Button>
            <Button onClick={handleWorkflowAction} disabled={transitioning} className="capitalize">
              {transitioning && <Loader2 className="w-3 h-3 mr-1 animate-spin" />}
              {remarksDialog.action}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SeniorityListDetailView;
