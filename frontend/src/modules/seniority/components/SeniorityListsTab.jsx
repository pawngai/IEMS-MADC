import { useEffect, useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Eye,
  ListOrdered,
  Loader2,
  Plus,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Card, CardContent } from "@/shared/ui/card";
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
import { DataTable } from "@/shared/data-table";
import { useAuth } from "@/modules/identity_access";
import { hasAuthority } from "@/platform/permissions";
import SeniorityListDetailView from "@/modules/seniority/components/SeniorityListDetailView";
import {
  DESIGNATIONS_FALLBACK,
  LIST_TYPES,
  ListTypeBadge,
  SERVICES,
  StatusBadge,
  buildRankValidationMessage,
  formatDesignation,
  formatEnumLabel,
  formatGeneratedListTitle,
  formatPreciseDateTime,
  formatServiceLabel,
  formatVersionLabel,
} from "@/modules/seniority/components/SeniorityListsTab.helpers";

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

  const handleWorkflowAction = async () => {
    const ok = remarksDialog.action === "promote"
      ? await promote(remarksDialog.listId, remarks)
      : await transition(remarksDialog.action, remarksDialog.listId, remarks);

    if (ok) {
      setRemarksDialog({ open: false, action: "", listId: "" });
      setRemarks("");
      fetchLists();
    }
  };

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

  if (detail) {
    return (
      <SeniorityListDetailView
        detail={detail}
        detailLoading={detailLoading}
        transitioning={transitioning}
        isDataEntry={isDataEntry}
        isVerifier={isVerifier}
        isApprover={isApprover}
        editingRanks={editingRanks}
        setEditingRanks={setEditingRanks}
        rankEdits={rankEdits}
        setRankEdits={setRankEdits}
        setDetail={setDetail}
        setRemarksDialog={setRemarksDialog}
        remarksDialog={remarksDialog}
        remarks={remarks}
        setRemarks={setRemarks}
        handleSaveRanks={handleSaveRanks}
        handleWorkflowAction={handleWorkflowAction}
        exportCSV={exportCSV}
      />
    );
  }

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
            <div className="rounded-md border">
              <DataTable
                rows={lists}
                rowKey={(item) => item.list_id}
                emptyState={
                  <div className="flex flex-col items-center gap-2 py-16 text-center text-muted-foreground">
                    <ListOrdered className="w-10 h-10 opacity-30" />
                    <p className="font-medium">No seniority lists found</p>
                    <p className="text-xs">Generate a new list or adjust your filters above.</p>
                  </div>
                }
                columns={[
                  {
                    key: "title",
                    header: "Title",
                    render: (item) => (
                      <div className="space-y-1">
                        <div className="font-medium">{formatGeneratedListTitle(item.title)}</div>
                        <div className="text-xs text-muted-foreground">{formatVersionLabel(item.version)}</div>
                      </div>
                    ),
                  },
                  { key: "type", header: "Type", render: (item) => <ListTypeBadge listType={item.list_type} /> },
                  { key: "service", header: "Service", render: (item) => formatServiceLabel(item.service) },
                  { key: "designation", header: "Designation", render: (item) => formatDesignation(item.designation_code) },
                  { key: "status", header: "Status", render: (item) => <StatusBadge status={item.status} /> },
                  { key: "total", header: "Employees", className: "text-right" },
                  {
                    key: "created",
                    header: "Created",
                    className: "text-xs text-muted-foreground",
                    headClassName: "",
                    render: (item) => formatPreciseDateTime(item.created_at) || "-",
                  },
                  {
                    key: "actions",
                    header: "Actions",
                    headClassName: "w-20",
                    render: (item) => (
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
                    ),
                  },
                ]}
              />
            </div>
          </CardContent>
        </Card>
      )}

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
