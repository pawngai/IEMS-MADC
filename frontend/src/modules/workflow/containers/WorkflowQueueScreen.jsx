/**
 * WorkQueue v2 — Redesigned unified work queue.
 *
 * Features:
 *  - Table view (default) + Kanban pipeline view toggle
 *  - SLA aging indicators (green / yellow / red)
 *  - Type filter pills (Profile / Service Book / Leave)
 *  - Search across name, code, type
 *  - Slide-over detail panel with audit timeline
 *  - Batch selection with bulk action
 *  - Keyboard shortcuts (j/k navigate, Enter open, Esc close)
 *  - Smart summary bar with live counts
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ESS, MAIN } from "@/shared/lib/routes";
import {
  getOpeningActionLabel,
  resolveServiceBookStatus,
  serviceBookAPI,
  serviceRecordsApi,
} from "@/modules/service_book";
import { useWorkflowQueueQuery } from "@/modules/workflow/hooks/useWorkflowQueueQuery";
import { useWorkflowQueueFilters } from "@/modules/workflow/hooks/useWorkflowQueueFilters";
import { useWorkflowQueueActions } from "@/modules/workflow/hooks/useWorkflowQueueActions";
import {
  selectCountsByType,
  selectSlaCounts,
} from "@/modules/workflow/model/workflowQueueSelectors";
import WorkflowQueueFilters from "@/modules/workflow/components/WorkflowQueueFilters";
import WorkflowQueueBulkActions from "@/modules/workflow/components/WorkflowQueueBulkActions";
import WorkflowKanbanView from "@/modules/workflow/components/WorkflowKanbanView";
import WorkflowTableView from "@/modules/workflow/components/WorkflowTableView";
import WorkflowDetailPanel from "@/modules/workflow/components/WorkflowDetailPanel";
import { MiniStat } from "@/modules/workflow/components/workflowQueuePrimitives";
import { getProfileAuditTrail } from "@/modules/workflow/model/workQueueGateway";
import {
  buildEmployeeFilePath,
  buildIdentityEditPath,
  buildProfileEditPath,
  getEmployeeEditorScope,
} from "@/shared/lib/employeeEditorRoutes";
import { cn, formatServiceBookPartsIncompleteMessage, getApiErrorMessage } from "@/shared/lib/utils";

import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent } from "@/shared/ui/card";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/shared/ui/sheet";
import { TooltipProvider } from "@/shared/ui/tooltip";
import { toast } from "sonner";
import { WorkQueueSkeleton, PageHeaderSkeleton } from "@/shared/ui/skeletons";
import {
  AlertTriangle,
  BookOpen,
  Check,
  Clock,
  Columns3,
  FileText,
  Filter,
  Keyboard,
  LayoutList,
  RefreshCw,
  Users,
} from "lucide-react";

/* ============================================================ */
/*  Main Component                                             */
/* ============================================================ */

const WorkflowQueueScreen = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { loading, refreshing, items, refresh, authority, authorityLabel } = useWorkflowQueueQuery();
  const { getActions, performAction } = useWorkflowQueueActions({ authority });
  const getWorkQueueActions = useCallback((item) => getActions(item), [getActions]);
  const {
    query,
    setQuery,
    typeFilter,
    setTypeFilter,
    slaFilter,
    setSlaFilter,
    filteredItems,
    kanbanColumns,
  } = useWorkflowQueueFilters({ items });
  const countsByType = useMemo(() => selectCountsByType(items), [items]);
  const slaCounts = useMemo(() => selectSlaCounts(items), [items]);
  const typeOptions = useMemo(() => {
    const options = [
      { value: "ALL", label: `All (${items.length})` },
      { value: "identity", label: `Identities (${countsByType.identity || 0})`, color: "bg-emerald-100 text-emerald-700" },
      { value: "profile", label: `Profiles (${countsByType.profile || 0})`, color: "bg-blue-100 text-blue-700" },
      { value: "service", label: `Service Book (${countsByType.service || 0})`, color: "bg-amber-100 text-amber-700" },
    ];

    if (countsByType.change_request > 0) {
      options.push({ value: "change_request", label: `Change Requests (${countsByType.change_request})`, color: "bg-violet-100 text-violet-700" });
    }

    return options;
  }, [countsByType.change_request, countsByType.identity, countsByType.profile, countsByType.service, items.length]);

  const [view, setView] = useState("table");
  const [selectedId, setSelectedId] = useState(null);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [batchSelected, setBatchSelected] = useState(new Set());
  const [actionBusy, setActionBusy] = useState(false);
  const [remarks, setRemarks] = useState("");
  const [auditTrail, setAuditTrail] = useState([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [profileServiceBookAction, setProfileServiceBookAction] = useState({
    status: null,
    path: null,
    label: "View Service Book",
  });
  const [showKeyboard, setShowKeyboard] = useState(false);
  const editorScope = useMemo(() => getEmployeeEditorScope(location.pathname), [location.pathname]);
  const isPortalPath = useMemo(() => location.pathname.startsWith("/portal"), [location.pathname]);

  /* Is this user a data entry authority who edits draft profiles? */
  const isDataEntryAuthority = ["DEPT_DATA_ENTRY", "GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT", "SECTION_OFFICER"].includes(authority);
  const isIdentityDataEntryAuthority = ["DEPT_DATA_ENTRY", "GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT"].includes(authority);
  const canAccessServiceBookOpening = ["GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT"].includes(authority);

  /* -- route to profile editor for draft profiles (data entry) ---- */
  const openProfileEditorForItem = useCallback((item) => {
    if (!item?.employeeId) return;
    navigate(buildProfileEditPath(editorScope, item.employeeId), {
      state: { returnTo: location.pathname },
    });
  }, [editorScope, location.pathname, navigate]);

  const openIdentityEditorForItem = useCallback((item) => {
    if (!item?.employeeId) return;
    navigate(buildIdentityEditPath(editorScope, item.employeeId), {
      state: { returnTo: location.pathname },
    });
  }, [editorScope, location.pathname, navigate]);

  /** Decide what happens when user clicks an item. */
  const handleItemSelect = useCallback(
    (id) => {
      setSelectedId(id);
      setSheetOpen(true);
    },
    []
  );

  const selected = useMemo(() => items.find((i) => i.id === selectedId) || null, [items, selectedId]);
  const selectedProfileEmployeeId = selected?.type === "profile" && selected?.employeeId
    ? selected.employeeId
    : null;
  const selectedServiceBookRef = selected?.employeeCode || selected?.employeeId || null;
  const selectedServiceBookPath = useMemo(() => {
    if (!selectedServiceBookRef) return null;
    return isPortalPath ? `/portal/service-book/${selectedServiceBookRef}` : MAIN.SERVICE_BOOK_EMP(selectedServiceBookRef);
  }, [isPortalPath, selectedServiceBookRef]);
  const selectedServiceBookOpeningPath = useMemo(() => {
    if (!selectedServiceBookRef) return null;
    return isPortalPath ? `/portal/service-book/opening/${selectedServiceBookRef}` : MAIN.SERVICE_BOOK_OPENING_EMP(selectedServiceBookRef);
  }, [isPortalPath, selectedServiceBookRef]);
  const selectedServiceBookAction = useMemo(() => {
    if (!selected?.employeeId || !selectedServiceBookRef || selected.type === "identity") {
      return null;
    }

    if (selected.type === "service_opening") {
      const openingStatus = String(selected.raw?.workflow_status || selected.raw?.status || selected.stage || "").trim().toUpperCase();
      const isOpened = openingStatus === "LOCKED" || openingStatus === "OPENED" || openingStatus === "ATTESTED";
      return {
        path: isOpened ? selectedServiceBookPath : selectedServiceBookOpeningPath,
        label: getOpeningActionLabel(openingStatus),
      };
    }

    if (selected.type === "profile") {
      if (profileServiceBookAction.status === "OPENED") {
        return {
          path: selectedServiceBookPath,
          label: "View Service Book",
        };
      }

      if (!canAccessServiceBookOpening) {
        return null;
      }

      return {
        path: profileServiceBookAction.path || selectedServiceBookOpeningPath,
        label: profileServiceBookAction.label || "Open Service Book",
      };
    }

    return {
      path: selectedServiceBookPath,
      label: "View Service Book",
    };
  }, [
    profileServiceBookAction.label,
    profileServiceBookAction.path,
    profileServiceBookAction.status,
    selected,
    canAccessServiceBookOpening,
    selectedServiceBookOpeningPath,
    selectedServiceBookPath,
    selectedServiceBookRef,
  ]);
  const batchActionSummary = useMemo(() => {
    const selectedItems = items.filter((item) => batchSelected.has(item.id));
    const actionableItems = selectedItems
      .map((item) => ({
        item,
        action: getWorkQueueActions(item).find((action) => action.variant !== "destructive" && !action.disabled) || null,
      }))
      .filter((entry) => entry.action);

    const labels = [...new Set(actionableItems.map((entry) => entry.action.label))];

    return {
      actionableItems,
      actionableCount: actionableItems.length,
      skippedCount: selectedItems.length - actionableItems.length,
      buttonLabel:
        actionableItems.length === 0
          ? "No bulk action available"
          : labels.length === 1
          ? `${labels[0]} Selected`
          : "Process Selected",
    };
  }, [items, batchSelected, getWorkQueueActions]);

  /* keyboard navigation */
  useEffect(() => {
    const onKey = (e) => {
      if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
      const idx = filteredItems.findIndex((i) => i.id === selectedId);
      if (e.key === "j" || e.key === "ArrowDown") { e.preventDefault(); const next = Math.min(idx + 1, filteredItems.length - 1); if (filteredItems[next]) setSelectedId(filteredItems[next].id); }
      if (e.key === "k" || e.key === "ArrowUp") { e.preventDefault(); const prev = Math.max(idx - 1, 0); if (filteredItems[prev]) setSelectedId(filteredItems[prev].id); }
      if (e.key === "Enter" && selectedId) { e.preventDefault(); setSheetOpen(true); }
      if (e.key === "Escape") { setSheetOpen(false); }
      if (e.key === "r") refresh();
      if (e.key === "?") setShowKeyboard((p) => !p);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [filteredItems, selectedId, refresh]);

  /* audit trail on selection */
  useEffect(() => {
    let active = true;
    setAuditTrail([]);
    if (!selectedProfileEmployeeId) {
      setAuditLoading(false);
      return () => { active = false; };
    }
    setAuditLoading(true);
    getProfileAuditTrail(selectedProfileEmployeeId)
      .then((entries) => active && setAuditTrail(entries))
      .catch(() => active && setAuditTrail([]))
      .finally(() => active && setAuditLoading(false));
    return () => { active = false; };
  }, [selectedProfileEmployeeId]);

  useEffect(() => {
    let active = true;

    if (selected?.type !== "profile" || !selected?.employeeId) {
      setProfileServiceBookAction({
        status: null,
        path: null,
        label: "View Service Book",
      });
      return () => { active = false; };
    }

    setProfileServiceBookAction({
      status: null,
      path: selectedServiceBookOpeningPath,
      label: "Open Service Book",
    });

    Promise.all([
      serviceRecordsApi.getServiceSummary(selected.employeeId).catch(() => ({ data: null })),
      serviceBookAPI.listEntries(selected.employeeId).catch(() => ({ entries: [] })),
    ]).then(([summaryResponse, entriesResponse]) => {
      if (!active) return;

      const status = resolveServiceBookStatus({
        summary: summaryResponse?.data || selected.raw || null,
        entries: entriesResponse?.entries || [],
      });

      setProfileServiceBookAction({
        status: status.status,
        path: status.status === "OPENED" ? selectedServiceBookPath : selectedServiceBookOpeningPath,
        label: getOpeningActionLabel(status.status),
      });
    });

    return () => { active = false; };
  }, [selected, selectedServiceBookOpeningPath, selectedServiceBookPath]);

  /* actions */
  const handleAction = useCallback(
    async (item, actionId) => {
      if (actionBusy) return;
      if (actionId === "ess-open") { navigate(ESS.PROFILE); return; }
      setActionBusy(true);
      const prevSheetOpen = sheetOpen;
      setSheetOpen(false);
      try {
        await performAction(item, actionId, remarks.trim());
        toast.success("Action completed");
        setRemarks("");
        refresh();
      } catch (err) {
        if (prevSheetOpen) setSheetOpen(true);
        const validationMessage = formatServiceBookPartsIncompleteMessage(err);
        toast.error(validationMessage || getApiErrorMessage(err, "Action failed"));
      } finally {
        setActionBusy(false);
      }
    },
    [actionBusy, remarks, sheetOpen, performAction, refresh, navigate]
  );

  const handleBatchAction = useCallback(
    async () => {
      if (actionBusy || batchSelected.size === 0) return;
      if (batchActionSummary.actionableCount === 0) {
        toast.error("No selected items are ready for a bulk action");
        return;
      }

      setActionBusy(true);
      const prevSet = new Set(batchSelected);
      setBatchSelected(new Set());
      toast(`Processing ${batchActionSummary.actionableCount} of ${prevSet.size} selected items...`);
      let ok = 0;
      let fail = 0;
      for (const { item, action } of batchActionSummary.actionableItems) {
        try {
          await performAction(item, action.id, "Batch action");
          ok++;
        } catch {
          fail++;
        }
      }

      const skipped = prevSet.size - batchActionSummary.actionableCount;
      const outcome = [
        `${ok} succeeded`,
        fail > 0 ? `${fail} failed` : null,
        skipped > 0 ? `${skipped} skipped` : null,
      ].filter(Boolean).join(", ");

      if (fail > 0) {
        toast.error(`Batch complete: ${outcome}`);
      } else {
        toast.success(`Batch complete: ${outcome}`);
      }

      refresh();
      setActionBusy(false);
    },
    [actionBusy, batchSelected, batchActionSummary, performAction, refresh]
  );

  const toggleBatch = (id) =>
    setBatchSelected((prev) => { const next = new Set(prev); next.has(id) ? next.delete(id) : next.add(id); return next; });

  const toggleSelectAllFiltered = useCallback(() => {
    const filteredIds = filteredItems.map((item) => item.id);
    setBatchSelected((prev) => {
      if (filteredIds.length === 0) return prev;

      const next = new Set(prev);
      const allFilteredSelected = filteredIds.every((id) => next.has(id));

      if (allFilteredSelected) {
        filteredIds.forEach((id) => next.delete(id));
        return next;
      }

      filteredIds.forEach((id) => next.add(id));
      return next;
    });
  }, [filteredItems]);

  const summaryText = useMemo(() => {
    const total = items.length;
    if (!total) return "No pending work items.";
    const urgent = slaCounts.RED || 0;
    const parts = [`${total} item${total !== 1 ? "s" : ""}`];
    if (urgent > 0) parts.push(`${urgent} overdue`);
    return parts.join(" \u00b7 ");
  }, [items, slaCounts]);

  /* -- render ---------------------------------------------- */

  if (loading) {
    return (
      <>
        <div className="max-w-7xl mx-auto space-y-6" data-testid="work-queue-loading">
          <PageHeaderSkeleton />
          <WorkQueueSkeleton items={8} />
        </div>
      </>
    );
  }

  return (
    <>
      <TooltipProvider delayDuration={200}>
        <div className="animate-fade-in" data-testid="work-queue">
          <div className="max-w-[1440px] mx-auto space-y-5 px-2 sm:px-0">

            {/* --- Header Bar ----------------------------------- */}
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <div className="flex items-center gap-3">
                  <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">Work Queue</h2>
                  <Badge className="text-xs font-medium bg-blue-100 text-blue-800 border-blue-200">
                    {authorityLabel}
                  </Badge>
                </div>
                <p className="text-slate-500 mt-1 text-sm">{summaryText}</p>
              </div>

              <div className="flex items-center gap-2 flex-wrap">
                <div className="inline-flex rounded-lg border border-slate-200 bg-white p-0.5">
                  <button
                    onClick={() => setView("kanban")}
                    className={cn(
                      "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                      view === "kanban" ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
                    )}
                  >
                    <Columns3 className="w-3.5 h-3.5" /> Pipeline
                  </button>
                  <button
                    onClick={() => setView("table")}
                    className={cn(
                      "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                      view === "table" ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
                    )}
                  >
                    <LayoutList className="w-3.5 h-3.5" /> Table
                  </button>
                </div>

                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setShowKeyboard((p) => !p)} title="Keyboard shortcuts (?)" aria-label="Toggle keyboard shortcuts">
                  <Keyboard className="w-4 h-4" />
                </Button>

                <Button variant="outline" size="sm" className="gap-1.5" onClick={refresh} disabled={refreshing}>
                  <RefreshCw className={cn("w-3.5 h-3.5", refreshing && "animate-spin")} />
                  Refresh
                </Button>
              </div>
            </div>

            {/* --- Keyboard shortcuts card ---------------------- */}
            {showKeyboard && (
              <Card className="border-blue-200 bg-blue-50/50">
                <CardContent className="py-3 px-4">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-1 text-xs">
                    {[
                      ["j / \u2193", "Next item"],
                      ["k / \u2191", "Previous item"],
                      ["Enter", "Open detail"],
                      ["Esc", "Close panel"],
                      ["r", "Refresh"],
                      ["?", "Toggle shortcuts"],
                    ].map(([key, desc]) => (
                      <div key={key} className="flex items-center gap-2">
                        <kbd className="px-1.5 py-0.5 rounded bg-white border border-blue-200 font-mono text-blue-800">{key}</kbd>
                        <span className="text-slate-600">{desc}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* --- SLA Summary Bar ------------------------------ */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-3">
              <MiniStat label="Total" value={items.length} icon={Users} />
              <MiniStat label="On time" value={slaCounts.GREEN} icon={Check} tone="text-green-600" />
              <MiniStat label="Aging (24-72h)" value={slaCounts.YELLOW} icon={Clock} tone="text-yellow-600" />
              <MiniStat label="Overdue (>72h)" value={slaCounts.RED} icon={AlertTriangle} tone="text-red-600" />
              <MiniStat label="Identities" value={countsByType.identity} icon={Users} />
              <MiniStat label="Profiles" value={countsByType.profile} icon={FileText} />
              <MiniStat label="Service Book" value={countsByType.service} icon={BookOpen} />
            </div>

            {/* --- Filter Bar ----------------------------------- */}
            <WorkflowQueueFilters
              query={query}
              onQueryChange={setQuery}
              typeFilter={typeFilter}
              onTypeFilterChange={setTypeFilter}
              slaFilter={slaFilter}
              onSlaFilterChange={setSlaFilter}
              typeOptions={typeOptions}
            />

            <WorkflowQueueBulkActions
              selectedCount={batchSelected.size}
              actionableCount={batchActionSummary.actionableCount}
              actionLabel={batchActionSummary.buttonLabel}
              actionBusy={actionBusy}
              onClear={() => setBatchSelected(new Set())}
              onRun={handleBatchAction}
            />

            {/* --- Main Content --------------------------------- */}
            {filteredItems.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 text-slate-400">
                <Filter className="w-10 h-10 mb-3" />
                <p className="text-lg font-medium">No items match your filters</p>
                <p className="text-sm mt-1">Try adjusting search or filter criteria.</p>
              </div>
            ) : view === "kanban" ? (
              <WorkflowKanbanView
                columns={kanbanColumns}
                selectedId={selectedId}
                batchSelected={batchSelected}
                onSelect={handleItemSelect}
                onToggleBatch={toggleBatch}
                getActions={getWorkQueueActions}
                onQuickAction={handleAction}
                actionBusy={actionBusy}
              />
            ) : (
              <WorkflowTableView
                items={filteredItems}
                selectedId={selectedId}
                batchSelected={batchSelected}
                onSelect={handleItemSelect}
                onToggleBatch={toggleBatch}
                onSelectAll={toggleSelectAllFiltered}
                getActions={getWorkQueueActions}
                onQuickAction={handleAction}
                actionBusy={actionBusy}
              />
            )}
          </div>

          {/* --- Detail Slide-over ------------------------------ */}
          <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
            <SheetContent className="sm:max-w-lg overflow-y-auto">
              <SheetHeader className="sr-only">
                <SheetTitle>
                  {selected ? `Work item details for ${selected.title}` : "Work item details"}
                </SheetTitle>
                <SheetDescription>
                  {selected
                    ? "Review workflow details, audit history, and available actions for the selected work item."
                    : "Review workflow details and available actions for the selected work item."}
                </SheetDescription>
              </SheetHeader>
              {selected ? (
                <WorkflowDetailPanel
                  item={selected}
                  actions={getWorkQueueActions(selected)}
                  remarks={remarks}
                  setRemarks={setRemarks}
                  onAction={handleAction}
                  actionBusy={actionBusy}
                  auditTrail={auditTrail}
                  auditLoading={auditLoading}
                  onOpenPrimary={selected?.employeeId ? () => {
                    if (selected.type === "identity") {
                      navigate(buildIdentityEditPath(editorScope, selected.employeeId));
                      return;
                    }
                    navigate(buildEmployeeFilePath(editorScope, selected.employeeId));
                  } : null}
                  onOpenSecondary={selectedServiceBookAction?.path ? () => navigate(selectedServiceBookAction.path) : null}
                  primaryOpenLabel={selected?.type === "identity" ? "Identity" : "Profile"}
                  secondaryOpenLabel={selectedServiceBookAction?.label || "View Service Book"}
                  showActions={!!selected.employeeId && authority !== "EMPLOYEE"}
                  onEditPrimary={
                    selected?.type === "profile" &&
                    isDataEntryAuthority &&
                    ["DRAFT", "REJECTED"].includes(selected.stage)
                      ? () => {
                          setSheetOpen(false);
                          openProfileEditorForItem(selected);
                        }
                      : selected?.type === "identity" &&
                        isIdentityDataEntryAuthority &&
                        ["DRAFT", "REJECTED"].includes(selected.stage)
                      ? () => {
                          setSheetOpen(false);
                          openIdentityEditorForItem(selected);
                        }
                      : null
                  }
                  editPrimaryLabel={selected?.type === "identity" ? "Edit Identity" : "Edit / Complete Profile"}
                />
              ) : (
                <div className="flex items-center justify-center h-full text-slate-400">
                  Select an item to view details
                </div>
              )}
            </SheetContent>
          </Sheet>

        </div>
      </TooltipProvider>
    </>
  );
};

export default WorkflowQueueScreen;
