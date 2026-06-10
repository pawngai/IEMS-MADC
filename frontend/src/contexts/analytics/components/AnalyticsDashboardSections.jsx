import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { analyticsAPI } from "@/contexts/analytics/api/analyticsApi";
import {
  buildCsvContent,
  buildWorkforceDrilldownExportDataset,
} from "@/contexts/analytics/lib/workforceDrilldownExport";
import {
  buildAnalyticsDrilldownFallbackFilename,
  buildAnalyticsLocalWorkforceFilename,
  getAnalyticsDownloadFilename,
  getAnalyticsEmployeeDisplay,
  triggerAnalyticsCsvDownload,
} from "@/contexts/analytics/lib/analyticsDashboardUiHelpers";
import {
  ANALYTICS_SECTION_CONFIG,
  AnalyticsBreakdownList,
  AnalyticsCategoryTick,
  AnalyticsDataNotice,
  AnalyticsInteractionHint,
  AnalyticsSectionLoader,
  AnalyticsTrendQuickList,
  ChartCard,
  CustomTooltip,
  EmptyChart,
  KpiCard,
} from "@/contexts/analytics/components/analyticsDashboardPrimitives";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/shared/ui/sheet";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  Users,
  ClipboardList,
  Calendar,
  TrendingUp,
  Loader2,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  Download,
  Search,
  SlidersHorizontal,
} from "lucide-react";
import { toast } from "sonner";
import {
  CHART_COLORS,
  COUNT_AXIS_PROPS,
  DRILLDOWN_EXPORT_LIMIT,
  LEAVE_STATUS_COLORS,
  STATUS_COLORS,
  WORKFLOW_STAGE_LABELS,
  WORKFLOW_STAGE_ORDER,
  formatAnalyticsCategoryLabel,
  formatAnalyticsDate,
  formatGenderAnalyticsLabel,
  formatLeaveStatusLabel,
  formatLeaveTypeLabel,
  formatServiceEventTypeLabel,
  formatWorkflowStageLabel,
  formatWorkflowStageSeries,
  getAnalyticsItemRawValues,
  sortWorkflowStageSeries,
} from "@/contexts/analytics/model/analyticsDashboardModel";

export {
  ANALYTICS_SECTION_CONFIG,
  AnalyticsDataNotice,
  AnalyticsInteractionHint,
  AnalyticsSectionLoader,
};

export const WORKFORCE_DRILLDOWN_FIELDS = [
  { key: "department", label: "Department" },
  { key: "designation", label: "Designation" },
  { key: "employmentType", label: "Employment Type" },
  { key: "status", label: "Status" },
  { key: "gender", label: "Gender" },
  { key: "office", label: "Office" },
  { key: "workflowStatus", label: "Workflow Status" },
  { key: "service", label: "Service" },
  { key: "serviceGroup", label: "Service Group" },
  { key: "maritalStatus", label: "Marital Status" },
  { key: "dateOfBirth", label: "Date of Birth" },
  { key: "initialEngagement", label: "Initial Engagement" },
  { key: "statusEffectiveDate", label: "Status Effective" },
  { key: "reportingOfficer", label: "Reporting Officer" },
  { key: "createdAt", label: "Created" },
  { key: "updatedAt", label: "Updated" },
];

export const DEFAULT_WORKFORCE_DRILLDOWN_FIELDS = [
  "department",
  "designation",
  "employmentType",
  "status",
  "gender",
];

export const AnalyticsDrilldownSheet = ({
  state,
  onOpenChange,
  departmentNameMap,
  designationNameMap,
  officeNameMap,
  serviceNameMap,
  serviceGroupNameMap,
  leaveTypeNameMap,
  serviceEventTypeNameMap,
  canOpenEmployees = false,
  canOpenServiceEvents = false,
}) => {
  const navigate = useNavigate();
  const config = state?.config || null;
  const data = state?.data || null;
  const rows = data?.rows || [];
  const total = Number(data?.total || 0);
  const [exporting, setExporting] = useState(false);
  const [workforceFilter, setWorkforceFilter] = useState("");
  const [visibleWorkforceFields, setVisibleWorkforceFields] = useState(DEFAULT_WORKFORCE_DRILLDOWN_FIELDS);
  const isWorkforceDrilldown = config?.section === "workforce";

  useEffect(() => {
    setWorkforceFilter("");
    setVisibleWorkforceFields(DEFAULT_WORKFORCE_DRILLDOWN_FIELDS);
  }, [config?.key]);

  const visibleWorkforceFieldSet = useMemo(
    () => new Set(visibleWorkforceFields),
    [visibleWorkforceFields],
  );

  const filteredWorkforceRows = useMemo(() => {
    if (!isWorkforceDrilldown) return rows;

    const query = workforceFilter.trim().toLowerCase();
    if (!query) return rows;

    return rows.filter((row) => {
      const searchText = [
        row.employee_name,
        row.employee_code,
        row.employee_id,
        formatAnalyticsCategoryLabel(row.department_id, { emptyLabel: "Unassigned", nameMap: departmentNameMap }),
        formatAnalyticsCategoryLabel(row.designation_id, { emptyLabel: "Unassigned", nameMap: designationNameMap }),
        formatAnalyticsCategoryLabel(row.employment_type),
        formatAnalyticsCategoryLabel(row.employee_status),
        formatGenderAnalyticsLabel(row.gender),
        formatAnalyticsCategoryLabel(row.office_id, { emptyLabel: "Unassigned", nameMap: officeNameMap }),
        formatWorkflowStageLabel(row.workflow_status),
        formatAnalyticsCategoryLabel(row.service, { emptyLabel: "Unassigned", nameMap: serviceNameMap }),
        formatAnalyticsCategoryLabel(row.service_group, { emptyLabel: "Unassigned", nameMap: serviceGroupNameMap }),
        formatAnalyticsCategoryLabel(row.marital_status, { emptyLabel: "Not specified" }),
        formatAnalyticsDate(row.date_of_birth),
        formatAnalyticsDate(row.date_of_initial_engagement),
        formatAnalyticsDate(row.status_effective_date),
        row.reporting_officer_id,
        formatAnalyticsDate(row.created_at, { includeTime: true }),
        formatAnalyticsDate(row.updated_at, { includeTime: true }),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return searchText.includes(query);
    });
  }, [
    departmentNameMap,
    designationNameMap,
    officeNameMap,
    isWorkforceDrilldown,
    rows,
    serviceGroupNameMap,
    serviceNameMap,
    workforceFilter,
  ]);

  const displayedRows = isWorkforceDrilldown ? filteredWorkforceRows : rows;
  const hasWorkforceFilter = workforceFilter.trim().length > 0;
  const hasCustomWorkforceFields = visibleWorkforceFields.length !== DEFAULT_WORKFORCE_DRILLDOWN_FIELDS.length
    || visibleWorkforceFields.some((fieldKey, index) => fieldKey !== DEFAULT_WORKFORCE_DRILLDOWN_FIELDS[index]);
  const shouldUseLocalWorkforceExport = isWorkforceDrilldown && (hasWorkforceFilter || hasCustomWorkforceFields);

  const closeSheet = () => onOpenChange(false);

  const resetWorkforceControls = () => {
    setWorkforceFilter("");
    setVisibleWorkforceFields(DEFAULT_WORKFORCE_DRILLDOWN_FIELDS);
  };

  const toggleWorkforceField = (fieldKey, checked) => {
    setVisibleWorkforceFields((current) => {
      const next = checked
        ? [...current, fieldKey]
        : current.filter((value) => value !== fieldKey);

      return DEFAULT_WORKFORCE_DRILLDOWN_FIELDS.filter((field) => next.includes(field));
    });
  };

  const openRowTarget = (row) => {
    if (!row?.employee_id) return;
    if (config?.section === "serviceEvents" && canOpenServiceEvents) {
      navigate(`/service-book/records/${row.employee_id}`);
      closeSheet();
      return;
    }
    if (canOpenEmployees) {
      navigate(`/employees/${row.employee_id}`);
      closeSheet();
    }
  };

  const renderActionCell = (row) => {
    const canOpenTarget = row?.employee_id && (
      (config?.section === "serviceEvents" && canOpenServiceEvents) ||
      (config?.section !== "serviceEvents" && canOpenEmployees)
    );

    if (!canOpenTarget) return null;

    return (
      <Button type="button" size="sm" variant="ghost" onClick={() => openRowTarget(row)}>
        Open
      </Button>
    );
  };

  const renderEmployeeIdentity = (row) => {
    const primary = row.employee_name || row.employee_code || row.employee_id || "-";
    const secondary = row.employee_code && row.employee_code !== row.employee_name
      ? row.employee_code
      : row.employee_id;

    return (
      <div className="min-w-0">
        <p className="truncate font-medium text-slate-900">{primary}</p>
        {secondary && <p className="truncate text-xs text-muted-foreground">{secondary}</p>}
      </div>
    );
  };

  const getWorkforceDepartmentLabel = useCallback((row) => (
    formatAnalyticsCategoryLabel(row?.department_id, { emptyLabel: "Unassigned", nameMap: departmentNameMap })
  ), [departmentNameMap]);

  const getWorkforceDesignationLabel = useCallback((row) => (
    formatAnalyticsCategoryLabel(row?.designation_id, { emptyLabel: "Unassigned", nameMap: designationNameMap })
  ), [designationNameMap]);

  const getWorkforceEmploymentTypeLabel = useCallback((row) => (
    formatAnalyticsCategoryLabel(row?.employment_type)
  ), []);

  const getWorkforceStatusLabel = useCallback((row) => (
    formatAnalyticsCategoryLabel(row?.employee_status)
  ), []);

  const getWorkforceGenderLabel = useCallback((row) => formatGenderAnalyticsLabel(row?.gender), []);

  const getWorkforceOfficeLabel = useCallback((row) => (
    formatAnalyticsCategoryLabel(row?.office_id, { emptyLabel: "Unassigned", nameMap: officeNameMap })
  ), [officeNameMap]);

  const getWorkforceWorkflowStatusLabel = useCallback((row) => formatWorkflowStageLabel(row?.workflow_status), []);

  const getWorkforceServiceLabel = useCallback((row) => (
    formatAnalyticsCategoryLabel(row?.service, { emptyLabel: "Unassigned", nameMap: serviceNameMap })
  ), [serviceNameMap]);

  const getWorkforceServiceGroupLabel = useCallback((row) => (
    formatAnalyticsCategoryLabel(row?.service_group, { emptyLabel: "Unassigned", nameMap: serviceGroupNameMap })
  ), [serviceGroupNameMap]);

  const getWorkforceMaritalStatusLabel = useCallback((row) => (
    formatAnalyticsCategoryLabel(row?.marital_status, { emptyLabel: "Not specified" })
  ), []);

  const getWorkforceDateOfBirthLabel = useCallback((row) => formatAnalyticsDate(row?.date_of_birth), []);

  const getWorkforceInitialEngagementLabel = useCallback((row) => formatAnalyticsDate(row?.date_of_initial_engagement), []);

  const getWorkforceStatusEffectiveDateLabel = useCallback((row) => formatAnalyticsDate(row?.status_effective_date), []);

  const getWorkforceReportingOfficerLabel = useCallback((row) => row?.reporting_officer_id || "-", []);

  const getWorkforceCreatedAtLabel = useCallback((row) => formatAnalyticsDate(row?.created_at, { includeTime: true }), []);

  const getWorkforceUpdatedAtLabel = useCallback((row) => formatAnalyticsDate(row?.updated_at, { includeTime: true }), []);

  const renderRows = () => {
    if (config?.section === "workforce") {
      return displayedRows.map((row) => (
        <TableRow key={row.employee_id || row.employee_code}>
          <TableCell>{renderEmployeeIdentity(row)}</TableCell>
          {visibleWorkforceFieldSet.has("department") && (
            <TableCell>{formatAnalyticsCategoryLabel(row.department_id, { emptyLabel: "Unassigned", nameMap: departmentNameMap })}</TableCell>
          )}
          {visibleWorkforceFieldSet.has("designation") && (
            <TableCell>{formatAnalyticsCategoryLabel(row.designation_id, { emptyLabel: "Unassigned", nameMap: designationNameMap })}</TableCell>
          )}
          {visibleWorkforceFieldSet.has("employmentType") && (
            <TableCell>{formatAnalyticsCategoryLabel(row.employment_type)}</TableCell>
          )}
          {visibleWorkforceFieldSet.has("status") && (
            <TableCell>
              <Badge variant="outline">{formatAnalyticsCategoryLabel(row.employee_status)}</Badge>
            </TableCell>
          )}
          {visibleWorkforceFieldSet.has("gender") && <TableCell>{formatGenderAnalyticsLabel(row.gender)}</TableCell>}
          {visibleWorkforceFieldSet.has("office") && <TableCell>{getWorkforceOfficeLabel(row)}</TableCell>}
          {visibleWorkforceFieldSet.has("workflowStatus") && <TableCell><Badge variant="outline">{getWorkforceWorkflowStatusLabel(row)}</Badge></TableCell>}
          {visibleWorkforceFieldSet.has("service") && <TableCell>{getWorkforceServiceLabel(row)}</TableCell>}
          {visibleWorkforceFieldSet.has("serviceGroup") && <TableCell>{getWorkforceServiceGroupLabel(row)}</TableCell>}
          {visibleWorkforceFieldSet.has("maritalStatus") && <TableCell>{getWorkforceMaritalStatusLabel(row)}</TableCell>}
          {visibleWorkforceFieldSet.has("dateOfBirth") && <TableCell>{getWorkforceDateOfBirthLabel(row)}</TableCell>}
          {visibleWorkforceFieldSet.has("initialEngagement") && <TableCell>{getWorkforceInitialEngagementLabel(row)}</TableCell>}
          {visibleWorkforceFieldSet.has("statusEffectiveDate") && <TableCell>{getWorkforceStatusEffectiveDateLabel(row)}</TableCell>}
          {visibleWorkforceFieldSet.has("reportingOfficer") && <TableCell>{getWorkforceReportingOfficerLabel(row)}</TableCell>}
          {visibleWorkforceFieldSet.has("createdAt") && <TableCell>{getWorkforceCreatedAtLabel(row)}</TableCell>}
          {visibleWorkforceFieldSet.has("updatedAt") && <TableCell>{getWorkforceUpdatedAtLabel(row)}</TableCell>}
          <TableCell className="text-right">{renderActionCell(row)}</TableCell>
        </TableRow>
      ));
    }

    if (config?.section === "workflow") {
      return rows.map((row) => {
        const lastStageChange = row.locked_at || row.approved_at || row.verified_at || row.submitted_at;
        return (
          <TableRow key={`${row.employee_id}-${row.workflow_status}`}> 
            <TableCell>{renderEmployeeIdentity(row)}</TableCell>
            <TableCell>
              <Badge variant="outline">{formatWorkflowStageLabel(row.workflow_status)}</Badge>
            </TableCell>
            <TableCell>{formatAnalyticsCategoryLabel(row.department_id, { emptyLabel: "Unassigned", nameMap: departmentNameMap })}</TableCell>
            <TableCell>{formatAnalyticsDate(lastStageChange)}</TableCell>
            <TableCell className="text-right">{renderActionCell(row)}</TableCell>
          </TableRow>
        );
      });
    }

    if (config?.section === "leave") {
      return rows.map((row) => (
        <TableRow key={row.leave_id || `${row.employee_id}-${row.applied_at}`}> 
          <TableCell>{renderEmployeeIdentity(row)}</TableCell>
          <TableCell>{formatLeaveTypeLabel(row.leave_type_code, leaveTypeNameMap)}</TableCell>
          <TableCell>
            <Badge variant="outline">{formatLeaveStatusLabel(row.status)}</Badge>
          </TableCell>
          <TableCell>{row.from_date && row.to_date ? `${row.from_date} to ${row.to_date}` : "-"}</TableCell>
          <TableCell>{formatAnalyticsDate(row.applied_at, { includeTime: true })}</TableCell>
          <TableCell className="text-right">{renderActionCell(row)}</TableCell>
        </TableRow>
      ));
    }

    return rows.map((row) => (
      <TableRow key={row.service_event_id || `${row.employee_id}-${row.created_at}`}> 
        <TableCell>{renderEmployeeIdentity(row)}</TableCell>
        <TableCell>{formatServiceEventTypeLabel(row.event_type, serviceEventTypeNameMap)}</TableCell>
        <TableCell>{formatAnalyticsDate(row.effective_date)}</TableCell>
        <TableCell>{formatAnalyticsDate(row.created_at, { includeTime: true })}</TableCell>
        <TableCell className="text-right">{renderActionCell(row)}</TableCell>
      </TableRow>
    ));
  };

  const renderHeaderRow = () => {
    if (config?.section === "workforce") {
      return (
        <TableRow>
          <TableHead>Employee</TableHead>
          {visibleWorkforceFieldSet.has("department") && <TableHead>Department</TableHead>}
          {visibleWorkforceFieldSet.has("designation") && <TableHead>Designation</TableHead>}
          {visibleWorkforceFieldSet.has("employmentType") && <TableHead>Employment Type</TableHead>}
          {visibleWorkforceFieldSet.has("status") && <TableHead>Status</TableHead>}
          {visibleWorkforceFieldSet.has("gender") && <TableHead>Gender</TableHead>}
          {visibleWorkforceFieldSet.has("office") && <TableHead>Office</TableHead>}
          {visibleWorkforceFieldSet.has("workflowStatus") && <TableHead>Workflow Status</TableHead>}
          {visibleWorkforceFieldSet.has("service") && <TableHead>Service</TableHead>}
          {visibleWorkforceFieldSet.has("serviceGroup") && <TableHead>Service Group</TableHead>}
          {visibleWorkforceFieldSet.has("maritalStatus") && <TableHead>Marital Status</TableHead>}
          {visibleWorkforceFieldSet.has("dateOfBirth") && <TableHead>Date of Birth</TableHead>}
          {visibleWorkforceFieldSet.has("initialEngagement") && <TableHead>Initial Engagement</TableHead>}
          {visibleWorkforceFieldSet.has("statusEffectiveDate") && <TableHead>Status Effective</TableHead>}
          {visibleWorkforceFieldSet.has("reportingOfficer") && <TableHead>Reporting Officer</TableHead>}
          {visibleWorkforceFieldSet.has("createdAt") && <TableHead>Created</TableHead>}
          {visibleWorkforceFieldSet.has("updatedAt") && <TableHead>Updated</TableHead>}
          <TableHead className="text-right">Action</TableHead>
        </TableRow>
      );
    }

    if (config?.section === "workflow") {
      return (
        <TableRow>
          <TableHead>Employee</TableHead>
          <TableHead>Stage</TableHead>
          <TableHead>Department</TableHead>
          <TableHead>Latest Stage Change</TableHead>
          <TableHead className="text-right">Action</TableHead>
        </TableRow>
      );
    }

    if (config?.section === "leave") {
      return (
        <TableRow>
          <TableHead>Employee</TableHead>
          <TableHead>Leave Type</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Dates</TableHead>
          <TableHead>Applied</TableHead>
          <TableHead className="text-right">Action</TableHead>
        </TableRow>
      );
    }

    return (
      <TableRow>
        <TableHead>Employee</TableHead>
        <TableHead>Event Type</TableHead>
        <TableHead>Effective Date</TableHead>
        <TableHead>Recorded</TableHead>
        <TableHead className="text-right">Action</TableHead>
      </TableRow>
    );
  };

  const renderWorkforceControls = () => {
    if (!isWorkforceDrilldown || state?.loading || state?.error || rows.length === 0) return null;

    return (
      <div className="space-y-3 rounded-xl border border-slate-200 bg-white px-4 py-3">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input
              value={workforceFilter}
              onChange={(event) => setWorkforceFilter(event.target.value)}
              placeholder="Filter loaded rows by employee, code, department, designation, status, or gender..."
              className="pl-10"
            />
          </div>
          <div className="flex items-center gap-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button type="button" variant="outline" size="sm" className="gap-2">
                  <SlidersHorizontal className="h-4 w-4" />
                  Fields {visibleWorkforceFields.length}/{WORKFORCE_DRILLDOWN_FIELDS.length}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>Visible workforce fields</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {WORKFORCE_DRILLDOWN_FIELDS.map((field) => (
                  <DropdownMenuCheckboxItem
                    key={field.key}
                    checked={visibleWorkforceFieldSet.has(field.key)}
                    onCheckedChange={(checked) => toggleWorkforceField(field.key, Boolean(checked))}
                  >
                    {field.label}
                  </DropdownMenuCheckboxItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
            {(hasWorkforceFilter || hasCustomWorkforceFields) && (
              <Button type="button" variant="ghost" size="sm" onClick={resetWorkforceControls}>
                Reset
              </Button>
            )}
          </div>
        </div>
        <p className="text-xs text-muted-foreground">
          {shouldUseLocalWorkforceExport
            ? `Export now matches the ${displayedRows.length} displayed workforce rows and visible columns while local controls are active.`
            : `Filters apply to the ${rows.length} loaded rows in this sheet. Export uses the full drilldown selection until you apply a local filter or hide columns.`}
        </p>
      </div>
    );
  };

  const exportDrilldown = async () => {
    if (!config || exporting) return;

    setExporting(true);
    try {
      if (shouldUseLocalWorkforceExport) {
        const dataset = buildWorkforceDrilldownExportDataset({
          rows: displayedRows,
          visibleFieldKeys: visibleWorkforceFields,
          getDepartmentLabel: getWorkforceDepartmentLabel,
          getDesignationLabel: getWorkforceDesignationLabel,
          getEmploymentTypeLabel: getWorkforceEmploymentTypeLabel,
          getStatusLabel: getWorkforceStatusLabel,
          getGenderLabel: getWorkforceGenderLabel,
          getOfficeLabel: getWorkforceOfficeLabel,
          getWorkflowStatusLabel: getWorkforceWorkflowStatusLabel,
          getServiceLabel: getWorkforceServiceLabel,
          getServiceGroupLabel: getWorkforceServiceGroupLabel,
          getMaritalStatusLabel: getWorkforceMaritalStatusLabel,
          getDateOfBirthLabel: getWorkforceDateOfBirthLabel,
          getInitialEngagementLabel: getWorkforceInitialEngagementLabel,
          getStatusEffectiveDateLabel: getWorkforceStatusEffectiveDateLabel,
          getReportingOfficerLabel: getWorkforceReportingOfficerLabel,
          getCreatedAtLabel: getWorkforceCreatedAtLabel,
          getUpdatedAtLabel: getWorkforceUpdatedAtLabel,
        });
        const csvContent = buildCsvContent(dataset);
        const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
        const filename = buildAnalyticsLocalWorkforceFilename(config, {
          hasFilter: hasWorkforceFilter,
          hasCustomFields: hasCustomWorkforceFields,
        });

        triggerAnalyticsCsvDownload(blob, filename);
        toast.success(`CSV downloaded for ${displayedRows.length} displayed workforce rows`);
        return;
      }

      const response = await analyticsAPI.exportDrilldownCSV({
        section: config.section,
        dimension: config.dimension,
        value: config.value,
        values: config.values,
        limit: DRILLDOWN_EXPORT_LIMIT,
      });
      const filename = getAnalyticsDownloadFilename(
        response.headers,
        buildAnalyticsDrilldownFallbackFilename(config),
      );
      const totalMatches = Number(response.headers?.["x-iems-analytics-total"] || 0);
      const exportedCount = Number(response.headers?.["x-iems-analytics-exported"] || 0);
      triggerAnalyticsCsvDownload(response.data, filename);

      if ((totalMatches > exportedCount && exportedCount > 0) || total > DRILLDOWN_EXPORT_LIMIT) {
        toast.success(`CSV downloaded with the first ${DRILLDOWN_EXPORT_LIMIT} matching records`);
      } else {
        toast.success("CSV downloaded");
      }
    } catch {
      toast.error("Failed to export drilldown CSV");
    } finally {
      setExporting(false);
    }
  };

  return (
    <Sheet open={Boolean(state?.open)} onOpenChange={onOpenChange}>
      <SheetContent side="right" size="5xl" className="gap-0">
        <SheetHeader className="border-b border-slate-200 pb-4">
          <div className="flex items-start justify-between gap-4 pr-10">
            <div>
              <SheetTitle>{config?.label || "Analytics drilldown"}</SheetTitle>
              <SheetDescription>{config?.description || "Matching records for the selected analytics view."}</SheetDescription>
            </div>
            <div className="flex items-center gap-2">
              {!state?.loading && <Badge variant="outline">{total} matching</Badge>}
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={exportDrilldown}
                disabled={state?.loading || Boolean(state?.error) || rows.length === 0 || exporting || (shouldUseLocalWorkforceExport && displayedRows.length === 0)}
                className="gap-2"
              >
                {exporting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                Export CSV
              </Button>
            </div>
          </div>
        </SheetHeader>

        <div className="flex-1 space-y-4 overflow-y-auto py-4">
          {state?.loading ? (
            <div className="flex h-48 items-center justify-center gap-3 text-sm text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>Loading matching records...</span>
            </div>
          ) : state?.error ? (
            <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
              {state.error}
            </div>
          ) : (
            <>
              {renderWorkforceControls()}
              {displayedRows.length === 0 ? (
                <EmptyChart message={isWorkforceDrilldown && rows.length > 0 ? "No loaded workforce rows match the current filter" : "No matching records found"} />
              ) : (
                <>
                  <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
                    {isWorkforceDrilldown && hasWorkforceFilter
                      ? `Showing ${displayedRows.length} filtered rows from ${rows.length} loaded and ${total} total matching records.`
                      : `Showing ${displayedRows.length} of ${total} matching records.`}
                    {total > rows.length ? " Refine the selection or extend the drilldown limit to inspect more." : ""}
                  </div>
                  <div className="overflow-x-auto rounded-xl border border-slate-200">
                    <Table>
                      <TableHeader>{renderHeaderRow()}</TableHeader>
                      <TableBody>{renderRows()}</TableBody>
                    </Table>
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
};

export const OverviewPanel = ({ overview, workflow, openDrilldown }) => {
  if (!overview) return <EmptyChart message="Overview data unavailable" />;

  const workflowStageData = sortWorkflowStageSeries(
    formatWorkflowStageSeries(
      Object.entries(overview.workflow_stages || {}).map(([name, value]) => ({ name, value }))
    )
  );
  const totalProfiles = workflow?.total_profiles || workflowStageData.reduce((sum, stage) => sum + stage.value, 0);
  const completedProfiles = workflow?.locked_profiles ?? overview.locked_profiles ?? 0;
  const workflowStageBreakdown = workflowStageData.map((stage) => ({
    ...stage,
    tooltipLabel: totalProfiles > 0 ? `${stage.name} (${Math.round((stage.value / totalProfiles) * 100)}%)` : stage.name,
  }));
  const openWorkflowStage = (stage) => openDrilldown({
    section: "workflow",
    dimension: "stage",
    value: stage.rawName,
    label: `${stage.name} profiles`,
    description: `Employee profiles currently in the ${stage.name} stage.`,
  });

  return (
    <div className="space-y-6">
      {/* KPI cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          icon={Users}
          label="Total Employees"
          value={overview.total_employees}
          subtitle={overview.active_employees === overview.total_employees ? "All active" : `${overview.active_employees} active`}
          color="text-blue-600"
          bg="bg-blue-50"
          onClick={() => openDrilldown({
            section: "workforce",
            dimension: "all",
            label: "All employees",
            description: "All employee identity records included in the workforce overview.",
          })}
        />
        <KpiCard
          icon={ClipboardList}
          label="Pending Profiles"
          value={overview.pending_profiles}
          subtitle={`${completedProfiles} completed`}
          color="text-amber-600"
          bg="bg-amber-50"
          onClick={() => openDrilldown({
            section: "workflow",
            dimension: "pending",
            label: "Pending profiles",
            description: "Profiles waiting in submitted, verified, or approved workflow stages.",
          })}
        />
        <KpiCard
          icon={Calendar}
          label="Leave Applications"
          value={overview.total_leave_applications}
          subtitle={`${overview.pending_leaves} awaiting action`}
          color="text-emerald-600"
          bg="bg-emerald-50"
          onClick={() => openDrilldown({
            section: "leave",
            dimension: "all",
            label: "All leave applications",
            description: "All leave applications counted in leave analytics.",
          })}
        />
        <KpiCard
          icon={TrendingUp}
          label="Recent Service Book Records"
          value={overview.recent_service_events_30d}
          subtitle="Last 30 days"
          color="text-violet-600"
          bg="bg-violet-50"
          onClick={() => openDrilldown({
            section: "serviceEvents",
            dimension: "recent_30d",
            label: "Recent Service Book records",
            description: "Service events recorded during the last 30 days.",
          })}
        />
      </div>

      {/* Workflow stage bar + completion rate */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <ChartCard
          title="Profile Workflow Pipeline"
          description="Profiles by current workflow stage"
          className="lg:col-span-2"
        >
          {workflowStageData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={workflowStageData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis {...COUNT_AXIS_PROPS} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="value" name="Profiles" radius={[6, 6, 0, 0]} onClick={openWorkflowStage}>
                    {workflowStageData.map((entry) => (
                      <Cell key={entry.rawName || entry.name} fill={STATUS_COLORS[entry.rawName] || "#6b7280"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <AnalyticsBreakdownList items={workflowStageBreakdown} onSelect={openWorkflowStage} />
            </>
          ) : (
            <EmptyChart />
          )}
        </ChartCard>

        <ChartCard title="Completion Rate" description={`Profiles reaching the ${WORKFLOW_STAGE_LABELS.LOCKED} stage`}>
          <div className="flex flex-col items-center justify-center h-[280px] gap-4">
            <div className="relative w-36 h-36">
              <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                <circle cx="50" cy="50" r="40" fill="none" stroke="#f1f5f9" strokeWidth="12" />
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  fill="none"
                  stroke="#10b981"
                  strokeWidth="12"
                  strokeLinecap="round"
                  strokeDasharray={`${(workflow?.completion_rate || 0) * 2.51} 251`}
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl font-bold">{workflow?.completion_rate ?? 0}%</span>
              </div>
            </div>
            <div className="text-center text-sm text-muted-foreground">
              <p>{workflow?.locked_profiles ?? 0} of {workflow?.total_profiles ?? 0} profiles</p>
              <button
                type="button"
                onClick={() => openDrilldown({
                  section: "workflow",
                  dimension: "stage",
                  value: "LOCKED",
                  label: "Completed profiles",
                  description: "Profiles that have reached the locked stage.",
                })}
                className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-sky-700 hover:text-sky-800"
              >
                View matching profiles
                <ArrowUpRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </ChartCard>
      </div>
    </div>
  );
};

/* ─── Workforce Panel ────────────────────────────────────────────── */

export const WorkforcePanel = ({ data, openDrilldown }) => {
  if (!data) return <EmptyChart message="Workforce data unavailable" />;

  const openCategory = (dimension, labelPrefix) => (item) => openDrilldown({
    section: "workforce",
    dimension,
    values: getAnalyticsItemRawValues(item),
    label: `${labelPrefix}: ${item.tooltipLabel || item.name}`,
    description: `Employees matching ${item.tooltipLabel || item.name}.`,
  });

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* By Department */}
        <ChartCard title="Employees by Department" description="Active employees per department">
          {data.by_department?.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={data.by_department} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 180 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis type="number" {...COUNT_AXIS_PROPS} />
                  <YAxis
                    type="category"
                    dataKey="name"
                    tick={<AnalyticsCategoryTick />}
                    width={170}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="value" name="Employees" fill="#3b82f6" radius={[0, 6, 6, 0]} onClick={openCategory("department", "Department")} />
                </BarChart>
              </ResponsiveContainer>
              <AnalyticsBreakdownList items={data.by_department} onSelect={openCategory("department", "Department")} />
            </>
          ) : (
            <EmptyChart />
          )}
        </ChartCard>

        {/* By Employment Type */}
        <ChartCard title="Employment Type Distribution" description="Breakdown of active workforce">
          {data.by_employment_type?.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <PieChart>
                <Pie
                  data={data.by_employment_type}
                  cx="50%"
                  cy="50%"
                  outerRadius={110}
                  innerRadius={60}
                  dataKey="value"
                  nameKey="name"
                  label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                  labelLine={false}
                  onClick={(entry) => openCategory("employment_type", "Employment type")(entry?.payload || entry)}
                >
                  {data.by_employment_type.map((_, i) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart />
          )}
          <AnalyticsBreakdownList items={data.by_employment_type} onSelect={openCategory("employment_type", "Employment type")} />
        </ChartCard>

        {/* By Gender */}
        <ChartCard title="Gender Distribution" description="Active employees by gender">
          {data.by_gender?.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={data.by_gender}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  dataKey="value"
                  nameKey="name"
                  label={({ name, value }) => `${name}: ${value}`}
                  onClick={(entry) => openCategory("gender", "Gender")(entry?.payload || entry)}
                >
                  {data.by_gender.map((_, i) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart />
          )}
          <AnalyticsBreakdownList items={data.by_gender} onSelect={openCategory("gender", "Gender")} />
        </ChartCard>

        {/* By Status */}
        <ChartCard title="Employee Status" description="All employees by current status">
          {data.by_status?.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={data.by_status} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis {...COUNT_AXIS_PROPS} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="value" name="Count" radius={[6, 6, 0, 0]} onClick={openCategory("status", "Status")}>
                  {data.by_status.map((entry) => (
                    <Cell key={entry.rawName || entry.name} fill={STATUS_COLORS[entry.rawName] || "#6b7280"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart />
          )}
          <AnalyticsBreakdownList items={data.by_status} onSelect={openCategory("status", "Status")} />
        </ChartCard>
      </div>

      {/* By Designation */}
      <ChartCard title="Top Designations" description="Employees by designation (top 15)">
        {data.by_designation?.length > 0 ? (
          <>
            <ResponsiveContainer width="100%" height={360}>
              <BarChart data={data.by_designation} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 210 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis type="number" {...COUNT_AXIS_PROPS} />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={<AnalyticsCategoryTick />}
                  width={200}
                />
                <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="value" name="Employees" fill="#8b5cf6" radius={[0, 6, 6, 0]} onClick={openCategory("designation", "Designation")} />
              </BarChart>
            </ResponsiveContainer>
            <AnalyticsBreakdownList items={data.by_designation} onSelect={openCategory("designation", "Designation")} />
          </>
        ) : (
          <EmptyChart />
        )}
      </ChartCard>
    </div>
  );
};

/* ─── Leave Panel ────────────────────────────────────────────────── */

export { LeavePanel, WorkflowPanel, ServiceEventsPanel } from "@/contexts/analytics/components/analyticsDashboardPanels";
