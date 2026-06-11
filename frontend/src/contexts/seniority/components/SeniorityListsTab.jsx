import { useState, useEffect } from "react";
import {
  ArrowLeft,
  ArrowUpCircle,
  CheckCircle,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Download,
  Edit2,
  Eye,
  ListOrdered,
  Loader2,
  Plus,
  RefreshCw,
  Send,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { TableSkeleton } from "@/shared/ui/skeletons";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
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
import { useAuth } from "@/contexts/identity_access";
import { hasAuthority } from "@/contexts/access_control";
import { getReadablePersonName } from "@/shared/lib/readablePersonName";

const STATUS_BADGE = {
  DRAFT: { variant: "secondary", className: "" },
  SUBMITTED: { variant: "default", className: "" },
  VERIFIED: { variant: "outline", className: "border-blue-500 text-blue-700 bg-blue-50" },
  APPROVED: { variant: "outline", className: "border-green-600 text-green-700 bg-green-50" },
  REJECTED: { variant: "destructive", className: "" },
};

const SERVICES = ["MINISTERIAL", "ENGINEERING", "GENERAL"];
const DESIGNATIONS_FALLBACK = ["ASO", "SO", "UDC", "LDC", "AN", "CLERK", "JE", "AE"];
const LIST_TYPES = ["DRAFT", "PROVISIONAL", "FINAL"];
const DESIGNATION_LABELS = {
  ASO: "Assistant Section Officer",
  SO: "Section Officer",
  UDC: "Upper Division Clerk",
  LDC: "Lower Division Clerk",
  CLERK: "Clerk",
  JE: "Junior Engineer",
  AE: "Assistant Engineer",
};
const SERVICE_LABELS = {
  MINISTERIAL: "Ministerial",
  ENGINEERING: "Engineering",
  GENERAL: "General",
};

const LIST_TYPE_BADGE = {
  DRAFT: { variant: "secondary", className: "" },
  PROVISIONAL: { variant: "outline", className: "border-amber-500 text-amber-700 bg-amber-50" },
  FINAL: { variant: "outline", className: "border-emerald-600 text-emerald-700 bg-emerald-50" },
};

const PROMOTION_LABELS = {
  DRAFT: "Promote to Provisional",
  PROVISIONAL: "Promote to Final",
};

const toTitleCase = (value) => String(value)
  .toLowerCase()
  .split(/[_\s]+/)
  .filter(Boolean)
  .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
  .join(" ");

const formatEnumLabel = (value, fallback = "-") => value ? toTitleCase(value) : fallback;

const formatServiceLabel = (service) => {
  if (!service) return "-";

  const normalized = String(service).trim().toUpperCase();
  const groupMatch = normalized.match(/^GRP[-_\s]([A-Z])$/);
  if (groupMatch) return `Group ${groupMatch[1]}`;
  if (SERVICE_LABELS[normalized]) return SERVICE_LABELS[normalized];
  if (/^[A-Z]{2,4}$/.test(normalized)) return normalized;
  return formatEnumLabel(normalized);
};

const formatGroupLabel = (group) => {
  if (!group) return "-";

  const normalized = String(group).trim().toUpperCase();
  const groupMatch = normalized.match(/^(?:GROUP|GRP)[-_\s]?([A-Z])$/);
  if (groupMatch) return `Group ${groupMatch[1]}`;
  return formatEnumLabel(normalized, group);
};

const formatGeneratedListTitle = (title) => {
  if (!title) return "-";

  const value = String(title);
  const separatorIndex = value.lastIndexOf(" - ");
  if (separatorIndex === -1) return value;

  const prefix = value.slice(0, separatorIndex);
  const suffix = value.slice(separatorIndex + 3).trim();
  if (!suffix) return value;

  const segments = suffix.split("/").map((segment) => segment.trim()).filter(Boolean);
  if (segments.length === 0 || segments.length > 2) return value;
  if (!segments.every((segment) => /^[A-Z0-9_\-\s]+$/.test(segment))) return value;

  const formattedSegments = segments.map((segment, index) => {
    if (index === 0) {
      return formatServiceLabel(segment);
    }
    return formatDesignation(segment);
  });

  return `${prefix} - ${formattedSegments.join(" / ")}`;
};

const StatusBadge = ({ status, prefix = null }) => {
  const cfg = STATUS_BADGE[status] || { variant: "secondary", className: "" };
  const label = formatEnumLabel(status);
  return <Badge variant={cfg.variant} className={cfg.className}>{prefix ? `${prefix}: ${label}` : label}</Badge>;
};

const ListTypeBadge = ({ listType, prefix = null }) => {
  const t = listType || "DRAFT";
  const cfg = LIST_TYPE_BADGE[t] || { variant: "secondary", className: "" };
  const label = formatEnumLabel(t);
  return <Badge variant={cfg.variant} className={cfg.className}>{prefix ? `${prefix}: ${label}` : label}</Badge>;
};

const formatDate = (v) => v ? v.slice(0, 10) : null;
const formatDateTime = (v) => v ? v.slice(0, 16).replace("T", " ") : null;
const formatPreciseDateTime = (v) => v ? v.slice(0, 19).replace("T", " ") : null;
const formatVersionLabel = (value) => {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue) || numericValue < 1) return "Version 1";
  return `Version ${numericValue}`;
};

const buildRankValidationMessage = (employees, rankEdits) => {
  const rows = Array.isArray(employees) ? employees : [];
  if (rows.length === 0) return "";

  const ranks = rows.map((employee) => {
    const editedValue = rankEdits[employee.employee_id];
    const rawValue = editedValue ?? employee.rank;
    return Number(rawValue);
  });

  if (ranks.some((rank) => !Number.isInteger(rank) || rank < 1)) {
    return "Ranks must be whole numbers starting at 1.";
  }

  const expectedRanks = Array.from({ length: rows.length }, (_, index) => index + 1);
  const sortedRanks = [...ranks].sort((left, right) => left - right);
  const hasExactSequence = sortedRanks.every((rank, index) => rank === expectedRanks[index]);
  if (!hasExactSequence) {
    return `Ranks must stay unique and continuous from 1 to ${rows.length}.`;
  }

  return "";
};

const getEffectiveRank = (employee, rankEdits) => Number(rankEdits[employee.employee_id] ?? employee.rank);

const buildSwappedRankEdits = ({ employees, rankEdits, employeeId, direction }) => {
  const rows = Array.isArray(employees) ? employees : [];
  const orderedEmployees = [...rows].sort((left, right) => {
    const leftRank = getEffectiveRank(left, rankEdits);
    const rightRank = getEffectiveRank(right, rankEdits);
    if (leftRank !== rightRank) return leftRank - rightRank;
    return String(left.employee_id).localeCompare(String(right.employee_id));
  });

  const currentIndex = orderedEmployees.findIndex((employee) => employee.employee_id === employeeId);
  if (currentIndex === -1) return rankEdits;

  const targetIndex = direction === "up" ? currentIndex - 1 : currentIndex + 1;
  if (targetIndex < 0 || targetIndex >= orderedEmployees.length) return rankEdits;

  const currentEmployee = orderedEmployees[currentIndex];
  const targetEmployee = orderedEmployees[targetIndex];
  const currentRank = getEffectiveRank(currentEmployee, rankEdits);
  const targetRank = getEffectiveRank(targetEmployee, rankEdits);

  return {
    ...rankEdits,
    [currentEmployee.employee_id]: String(targetRank),
    [targetEmployee.employee_id]: String(currentRank),
  };
};

const formatDesignation = (designationCode) => {
  if (!designationCode) return "All Designations";

  const normalized = String(designationCode).trim().toUpperCase();
  const levelMatch = normalized.match(/^L(\d+)$/);
  if (levelMatch) return `Level ${levelMatch[1]}`;
  if (DESIGNATION_LABELS[normalized]) return DESIGNATION_LABELS[normalized];
  if (/[\s_]/.test(normalized)) return toTitleCase(normalized);
  return designationCode;
};

const SeniorityListsTab = ({
  lists,
  total,
  loading,
  detail,
  detailLoading,
  generating,
  transitioning,
  availableServices,
  availableDesignations,
  statusFilter,
  setStatusFilter,
  serviceFilter,
  setServiceFilter,
  listTypeFilter,
  setListTypeFilter,
  yearFilter,
  setYearFilter,
  pagination,
  setPagination,
  fetchLists,
  fetchOptions,
  fetchDetail,
  generateList,
  overrideRanks,
  transition,
  promote,
  exportCSV,
  setDetail,
}) => {
  const { user } = useAuth();
  const isDataEntry = hasAuthority(user, "GLOBAL_DATA_ENTRY") || hasAuthority(user, "DEALING_ASSISTANT") || hasAuthority(user, "DEPT_DATA_ENTRY");
  const isVerifier = hasAuthority(user, "VERIFIER");
  const isApprover = hasAuthority(user, "APPROVING_AUTHORITY");

  const [generateDialog, setGenerateDialog] = useState(false);
  const [genForm, setGenForm] = useState({ service: "", designation_code: "", title: "", list_type: "DRAFT" });
  const [remarksDialog, setRemarksDialog] = useState({ open: false, action: "", listId: "" });
  const [remarks, setRemarks] = useState("");
  const [editingRanks, setEditingRanks] = useState(false);
  const [rankEdits, setRankEdits] = useState({});
  const [openingListId, setOpeningListId] = useState("");

  useEffect(() => {
    fetchOptions();
    fetchLists();
  }, [fetchLists, fetchOptions]);

  // ---- Generate handler ----
  const handleGenerate = async () => {
    const result = await generateList(genForm.service, genForm.designation_code, genForm.title, genForm.list_type);
    if (result) {
      setGenerateDialog(false);
      setGenForm({ service: "", designation_code: "", title: "", list_type: "DRAFT" });
      fetchLists();
    }
  };

  const handleOpenDetail = async (listId) => {
    setOpeningListId(listId);
    try {
      await fetchDetail(listId);
    } finally {
      setOpeningListId("");
    }
  };

  // ---- Workflow action handler ----
  const handleWorkflowAction = async () => {
    let ok;
    if (remarksDialog.action === "promote") {
      ok = await promote(remarksDialog.listId, remarks);
    } else {
      ok = await transition(remarksDialog.action, remarksDialog.listId, remarks);
    }
    if (ok) {
      setRemarksDialog({ open: false, action: "", listId: "" });
      setRemarks("");
      fetchLists();
    }
  };

  // ---- Rank save ----
  const handleSaveRanks = async () => {
    if (!detail) return;
    const validationMessage = buildRankValidationMessage(detail.employees, rankEdits);
    if (validationMessage) return;

    const currentRanks = new Map((detail.employees || []).map((employee) => [employee.employee_id, Number(employee.rank)]));
    const overrides = Object.entries(rankEdits)
      .map(([eid, rank]) => ({
      employee_id: eid,
      new_rank: Number(rank),
      }))
      .filter((override) => currentRanks.get(override.employee_id) !== override.new_rank);
    if (overrides.length === 0) return;
    const ok = await overrideRanks(detail.list_id, overrides, "Manual rank adjustment");
    if (!ok) return;
    setEditingRanks(false);
    setRankEdits({});
  };

  // ======== DETAIL VIEW ========
  if (detail) {
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
            {/* Audit trail */}
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
            {/* Workflow actions */}
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

            {/* Employee table */}
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

        {/* Remarks dialog for workflow actions */}
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
  }

  // ======== LIST VIEW ========
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <ListOrdered className="w-5 h-5" /> Seniority Lists
        </h3>
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchLists} disabled={loading} className="gap-1">
            <RefreshCw className={`w-3 h-3 ${loading ? "animate-spin" : ""}`} /> Refresh
          </Button>
          {isDataEntry && (
            <Button size="sm" onClick={() => setGenerateDialog(true)} className="gap-1">
              <Plus className="w-3 h-3" /> Generate List
            </Button>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <Select value={listTypeFilter || "all"} onValueChange={(v) => { setListTypeFilter(v === "all" ? "" : v); setPagination((p) => ({ ...p, offset: 0 })); }}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="List Type" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {LIST_TYPES.map((t) => <SelectItem key={t} value={t}>{formatEnumLabel(t)}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={statusFilter || "all"} onValueChange={(v) => { setStatusFilter(v === "all" ? "" : v); setPagination((p) => ({ ...p, offset: 0 })); }}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="DRAFT">Draft</SelectItem>
            <SelectItem value="SUBMITTED">Submitted</SelectItem>
            <SelectItem value="VERIFIED">Verified</SelectItem>
            <SelectItem value="APPROVED">Approved</SelectItem>
            <SelectItem value="REJECTED">Rejected</SelectItem>
          </SelectContent>
        </Select>
        <Select value={serviceFilter || "all"} onValueChange={(v) => { setServiceFilter(v === "all" ? "" : v); setPagination((p) => ({ ...p, offset: 0 })); }}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="Service" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Services</SelectItem>
            {(availableServices.length > 0 ? availableServices : SERVICES).map((s) => <SelectItem key={s} value={s}>{formatServiceLabel(s)}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={yearFilter || "all"} onValueChange={(v) => { setYearFilter(v === "all" ? "" : v); setPagination((p) => ({ ...p, offset: 0 })); }}>
          <SelectTrigger className="w-[120px]"><SelectValue placeholder="Year" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Years</SelectItem>
            {Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i).map((y) => (
              <SelectItem key={y} value={String(y)}>{y}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      {loading ? (
        <TableSkeleton rows={8} columns={8} />
      ) : (
        <Card>
          <CardContent className="p-0">
            {detailLoading && !detail && (
              <div className="flex items-center gap-2 border-b border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                <Loader2 className="h-4 w-4 animate-spin" />
                Opening seniority list...
              </div>
            )}
            <div className="rounded-md border overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Service</TableHead>
                    <TableHead>Designation</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Employees</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="w-20">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {lists.map((item) => (
                      <TableRow key={item.list_id}>
                      <TableCell>
                        <div className="space-y-1">
                          <div className="font-medium">{formatGeneratedListTitle(item.title)}</div>
                          <div className="text-xs text-muted-foreground">{formatVersionLabel(item.version)}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <ListTypeBadge listType={item.list_type} />
                      </TableCell>
                      <TableCell>{formatServiceLabel(item.service)}</TableCell>
                      <TableCell>{formatDesignation(item.designation_code)}</TableCell>
                      <TableCell>
                        <StatusBadge status={item.status} />
                      </TableCell>
                      <TableCell className="text-right">{item.total}</TableCell>
                      <TableCell className="text-xs text-muted-foreground">{formatPreciseDateTime(item.created_at) || "-"}</TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon"
                          title={openingListId === item.list_id ? "Opening details" : "View details"}
                          aria-label={openingListId === item.list_id ? "Opening details" : "View details"}
                          disabled={detailLoading}
                          onClick={() => handleOpenDetail(item.list_id)}
                        >
                          {openingListId === item.list_id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Eye className="w-4 h-4" />
                          )}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {lists.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center py-16">
                        <div className="flex flex-col items-center gap-2 text-muted-foreground">
                          <ListOrdered className="w-10 h-10 opacity-30" />
                          <p className="font-medium">No seniority lists found</p>
                          <p className="text-xs">Generate a new list or adjust your filters above.</p>
                        </div>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Pagination */}
      {total > pagination.limit && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>Showing {pagination.offset + 1}-{Math.min(pagination.offset + pagination.limit, total)} of {total}</span>
          <div className="flex gap-1">
            <Button
              variant="outline"
              size="icon"
              disabled={pagination.offset === 0}
              onClick={() => setPagination((p) => ({ ...p, offset: Math.max(0, p.offset - p.limit) }))}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              disabled={pagination.offset + pagination.limit >= total}
              onClick={() => setPagination((p) => ({ ...p, offset: p.offset + p.limit }))}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Generate dialog */}
      <Dialog open={generateDialog} onOpenChange={setGenerateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Generate Seniority List</DialogTitle>
            <DialogDescription>
              Select a service and optionally narrow by designation to generate a seniority list.
              Data is pulled from Employee Identity, Profile Extensions, and Service Book.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <Label>List Type *</Label>
              <Select value={genForm.list_type} onValueChange={(v) => setGenForm((f) => ({ ...f, list_type: v }))}>
                <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                <SelectContent>
                  {LIST_TYPES.map((t) => <SelectItem key={t} value={t}>{formatEnumLabel(t)}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Service *</Label>
              <Select value={genForm.service} onValueChange={(v) => setGenForm((f) => ({ ...f, service: v }))}>
                <SelectTrigger><SelectValue placeholder="Select service" /></SelectTrigger>
                <SelectContent>
                  {(availableServices.length > 0 ? availableServices : SERVICES).map((s) => <SelectItem key={s} value={s}>{formatServiceLabel(s)}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Designation Code (optional)</Label>
              <Select value={genForm.designation_code} onValueChange={(v) => setGenForm((f) => ({ ...f, designation_code: v === "__ALL__" ? "" : v }))}>
                <SelectTrigger><SelectValue placeholder="All Designations" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="__ALL__">All Designations</SelectItem>
                  {(availableDesignations.length > 0 ? availableDesignations : DESIGNATIONS_FALLBACK).map((d) => <SelectItem key={d} value={d}>{formatDesignation(d)}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Title (optional)</Label>
              <Input
                value={genForm.title}
                onChange={(e) => setGenForm((f) => ({ ...f, title: e.target.value }))}
                placeholder="Leave blank to use the default list title"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setGenerateDialog(false)}>Cancel</Button>
            <Button
              onClick={handleGenerate}
              disabled={generating || !genForm.service}
            >
              {generating && <Loader2 className="w-3 h-3 mr-1 animate-spin" />}
              Generate
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SeniorityListsTab;
