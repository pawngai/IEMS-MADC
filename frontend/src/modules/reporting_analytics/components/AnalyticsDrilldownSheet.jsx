import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { analyticsAPI } from "@/modules/reporting_analytics/api/analyticsApi";
import {
  buildCsvContent,
  buildWorkforceDrilldownExportDataset,
} from "@/modules/reporting_analytics/lib/workforceDrilldownExport";
import {
  buildAnalyticsDrilldownFallbackFilename,
  buildAnalyticsLocalWorkforceFilename,
  getAnalyticsDownloadFilename,
  triggerAnalyticsCsvDownload,
} from "@/modules/reporting_analytics/lib/analyticsDashboardUiHelpers";
import { EmptyChart } from "@/modules/reporting_analytics/components/analyticsDashboardPrimitives";
import AnalyticsDrilldownTable from "@/modules/reporting_analytics/components/AnalyticsDrilldownTable";
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
import { Download, Loader2, Search, SlidersHorizontal } from "lucide-react";
import { toast } from "sonner";
import {
  DRILLDOWN_EXPORT_LIMIT,
  formatAnalyticsCategoryLabel,
  formatAnalyticsDate,
  formatGenderAnalyticsLabel,
  formatWorkflowStageLabel,
} from "@/modules/reporting_analytics/model/analyticsDashboardModel";

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
                    <AnalyticsDrilldownTable
                      config={config}
                      departmentNameMap={departmentNameMap}
                      designationNameMap={designationNameMap}
                      displayedRows={displayedRows}
                      leaveTypeNameMap={leaveTypeNameMap}
                      officeNameMap={officeNameMap}
                      renderActionCell={renderActionCell}
                      rows={rows}
                      serviceEventTypeNameMap={serviceEventTypeNameMap}
                      serviceGroupNameMap={serviceGroupNameMap}
                      serviceNameMap={serviceNameMap}
                      visibleWorkforceFieldSet={visibleWorkforceFieldSet}
                    />
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
