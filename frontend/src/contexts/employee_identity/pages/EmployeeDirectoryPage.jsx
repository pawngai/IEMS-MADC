import { useCallback, useMemo, useRef, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import Layout from "@/app/layout/Layout";
import { useEmployeeDirectory } from "@/contexts/employee_identity/hooks/useEmployeeDirectory";
import { employeeIdentityApi } from "@/contexts/employee_identity/api/employeeIdentityApi";
import { userManagementAPI } from "@/contexts/identity";
import { Permissions } from "@/platform/permissions";
import { useAuth } from "@/contexts/identity";
import { buildIdentityCreatePath } from "@/shared/lib/employeeEditorRoutes";
import { cn, getApiErrorMessage } from "@/shared/lib/utils";
import { Card, CardContent } from "@/shared/ui/card";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Checkbox } from "@/shared/ui/checkbox";
import { Input } from "@/shared/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table";
import { Popover, PopoverTrigger, PopoverContent } from "@/shared/ui/popover";
import { Calendar } from "@/shared/ui/calendar";
import { EmployeeTableSkeleton, SearchBarSkeleton } from "@/shared/ui/skeletons";
import { toast } from "sonner";
import { format } from "date-fns";
import {
  ArrowUpDown,
  CalendarIcon,
  ChevronLeft,
  ChevronRight,
  Filter,
  Key,
  RefreshCw,
  Search,
  UserPlus,
  Users,
  X,
  SlidersHorizontal,
  Columns3,
} from "lucide-react";
import {
  COLUMN_DEFS,
  DEFAULT_VISIBLE_COLUMNS,
  EMPLOYEE_STATUS_STYLES,
  STATUS_STYLES,
  buildLabelMap,
  getReadableEnumLabel,
  loadSavedColumns,
  renderCell,
  saveColumns,
  toTitleCase,
} from "@/contexts/employee_identity/pages/EmployeeDirectoryPage.support";
const EmployeeDirectoryPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { can, canAny, getPrimaryAuthority, isAny } = useAuth();
  const primaryAuthority = getPrimaryAuthority();
  const useIdentityDirectory = ["GLOBAL_DATA_ENTRY", "VERIFIER", "APPROVING_AUTHORITY"].includes(primaryAuthority);
  const useUserDirectory = primaryAuthority === "SYSTEM_ADMIN";

  // ── Hook: all directory data, filtering, pagination, sorting ──────
  const dir = useEmployeeDirectory({
    useUserDirectory,
    listUserDirectory: userManagementAPI.getEmployees,
    useIdentityDirectory,
    listIdentityDirectory: employeeIdentityApi.list,
  });
  const labelMaps = useMemo(() => ({
    department: buildLabelMap(dir.departmentOptions),
    designation: buildLabelMap(dir.designationOptions),
    office: buildLabelMap(dir.officeOptions),
    employmentType: buildLabelMap(dir.employmentTypeOptions),
    employeeStatus: buildLabelMap(
      dir.employeeStatusOptions.map((option) => ({
        ...option,
        label: toTitleCase(option.label || option.value),
      })),
    ),
    workflowStatus: new Map(Object.keys(STATUS_STYLES).map((status) => [status, toTitleCase(status)])),
  }), [
    dir.departmentOptions,
    dir.designationOptions,
    dir.officeOptions,
    dir.employmentTypeOptions,
    dir.employeeStatusOptions,
  ]);
  const getWorkflowStatusLabel = (status) => getReadableEnumLabel([status], labelMaps.workflowStatus);
  const getEmployeeStatusLabel = (status) => getReadableEnumLabel([status], labelMaps.employeeStatus);

  // ── Local UI state ────────────────────────────────────────────────
  const [actionLoading, setActionLoading] = useState("");
  const [showFilters, setShowFilters] = useState(() => {
    const sp = new URLSearchParams(location.search);
    return !!(sp.get("dept") || sp.get("type") || sp.get("desig") || sp.get("office") || sp.get("emp_status") || sp.get("recruit") || sp.get("pay") || sp.get("svc") || sp.get("grp") || sp.get("date_from") || sp.get("date_to"));
  });
  const [visibleColumns, setVisibleColumns] = useState(loadSavedColumns);
  const tableRef = useRef(null);
  const currentDirectoryPath = `${location.pathname}${location.search || ""}`;

  // Detect if we're inside the /portal/* route group
  const isPortalPath = location.pathname.startsWith("/portal");

  const canSeeEmployees =
    canAny([
      Permissions.PROFILE_READ_ALL,
      Permissions.PROFILE_CREATE,
      Permissions.PROFILE_UPDATE_ALL,
      Permissions.PROFILE_UPDATE_OWN_LIMITED,
      Permissions.AUDIT_READ_ALL,
    ]);

  const canCreateEmployee =
    isAny(["GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT"]) &&
    can(Permissions.PROFILE_CREATE);

  const canManageEmployeeAccounts = isAny(["SYSTEM_ADMIN", "GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT"]);

  const resolveProvisioningEmail = useCallback((employee) => (
    employee?.official_email ||
    employee?.email_official ||
    employee?.email_personal ||
    employee?.personal_email ||
    employee?.contact?.email_official ||
    employee?.contact?.email_personal ||
    ""
  ), []);

  const canProvisionEmployeeAccount = useCallback((employee) => {
    const identityWorkflowStatus = String(employee?.identity_workflow_status || employee?.workflow_status || "").trim().toUpperCase();
    return identityWorkflowStatus === "ACTIVE";
  }, []);

  const getProvisioningAvailability = useCallback((employee) => {
    if (employee?.has_login_account) {
      return {
        canProvision: false,
        label: "Login ready",
        reason: employee?.account_email || "Employee account already exists",
      };
    }

    if (!canProvisionEmployeeAccount(employee)) {
      return {
        canProvision: false,
        label: "Awaiting approval",
        reason: "Login available after identity activation",
      };
    }

    if (!resolveProvisioningEmail(employee)) {
      return {
        canProvision: false,
        label: "Email required",
        reason: "Add an account email first",
      };
    }

    return {
      canProvision: true,
      label: "Provision login",
      reason: "Create or link an employee login",
    };
  }, [canProvisionEmployeeAccount, resolveProvisioningEmail]);

  const handleProvisionAccount = useCallback(
    async (employee) => {
      const employeeId = employee?.employee_id;
      const email = resolveProvisioningEmail(employee);

      if (!employeeId) return;
      if (!canManageEmployeeAccounts) {
        toast.error("Only System Admin, Global Data Entry, or Dealing Assistant can provision login accounts");
        return;
      }
      if (!canProvisionEmployeeAccount(employee)) {
        toast.error("Login account provisioning is available only after the employee identity is active");
        return;
      }
      if (!email) {
        toast.error("Add an account email in the employee profile before provisioning a login account");
        return;
      }

      setActionLoading(`provision-${employeeId}`);
      try {
        const res = await userManagementAPI.provisionEmployeeAccount({
          employee_id: employeeId,
          email,
        });
        if (res.data?.already_exists) {
          toast.success(
            res.data?.message || `Account already exists for ${res.data?.email || email}`,
            { duration: 7000 }
          );
        } else {
          toast.success(
            `Account created. Temp password: ${res.data?.temp_password || "(see admin)"}`,
            { duration: 10000 }
          );
        }
        await dir.refresh();
      } catch (error) {
        toast.error(getApiErrorMessage(error, "Failed to provision account"));
      } finally {
        setActionLoading("");
      }
    },
    [canManageEmployeeAccounts, canProvisionEmployeeAccount, dir, resolveProvisioningEmail]
  );

  const toggleColumn = (key) => {
    setVisibleColumns((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      saveColumns(next);
      return next;
    });
  };

  const SortHeader = ({ field, children, className }) => (
    <TableHead
      className={cn("cursor-pointer select-none hover:text-slate-900 transition-colors", className)}
      onClick={() => dir.toggleSort(field)}
    >
      <span className="inline-flex items-center gap-1">
        {children}
        <ArrowUpDown
          className={cn(
            "w-3 h-3 opacity-40",
            dir.sortField === field && "opacity-100 text-blue-600"
          )}
        />
      </span>
    </TableHead>
  );

  if (!canSeeEmployees) {
    return (
      <Layout>
        <div
          className="max-w-4xl mx-auto p-8 text-center text-slate-500"
          data-testid="employees-denied"
        >
          Employee directory is not available for your role/module access.
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div
        className="max-w-full space-y-6 animate-fade-in"
        data-testid="employees-page"
      >
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">
              Directory
            </p>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">
              Employee Directory
            </h2>
            <p className="text-sm text-slate-500 mt-1">
              {dir.total} identit{dir.total === 1 ? "y" : "ies"} in system
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {canCreateEmployee && (
              <>
                <Button
                  className="gap-2"
                  onClick={() =>
                    navigate(buildIdentityCreatePath(isPortalPath ? "portal" : "default"), {
                      state: { returnTo: currentDirectoryPath },
                    })
                  }
                  data-testid="employees-new"
                >
                  <UserPlus className="w-4 h-4" />
                  Regular Employee
                </Button>
                <Button
                  variant="outline"
                  className="gap-2"
                  onClick={() =>
                    navigate(buildIdentityCreatePath(isPortalPath ? "portal" : "default"), {
                      state: { returnTo: currentDirectoryPath, creationMode: "non_regular" },
                    })
                  }
                  data-testid="employees-new-non-regular"
                >
                  <UserPlus className="w-4 h-4" />
                  Non-Regular Employee
                </Button>
              </>
            )}
            <Button
              variant="outline"
              className="gap-2"
              onClick={() => dir.refresh()}
              disabled={dir.refreshing}
              data-testid="employees-refresh"
            >
              <RefreshCw className={cn("w-4 h-4", dir.refreshing && "animate-spin")} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Search + Filter Controls */}
        <div className="space-y-3">
          <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
            <div className="relative flex-1 max-w-md">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <Input
                value={dir.query}
                onChange={(e) => dir.setQuery(e.target.value)}
                placeholder="Search name, code, department, designation..."
                aria-label="Search employees by name, code, department, or designation"
                className="pl-9"
                data-testid="employees-search"
              />
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant={showFilters ? "default" : "outline"}
                size="sm"
                className="gap-1.5"
                onClick={() => setShowFilters((v) => !v)}
                aria-expanded={showFilters}
                aria-controls="employees-filter-panel"
                data-testid="employees-toggle-filters"
              >
                <SlidersHorizontal className="w-3.5 h-3.5" />
                Filters
                {dir.activeFilterCount > 0 && (
                  <span className="ml-1 inline-flex items-center justify-center w-5 h-5 rounded-full bg-blue-100 text-blue-700 text-[10px] font-bold">
                    {dir.activeFilterCount}
                  </span>
                )}
              </Button>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5"
                    aria-label={`Choose visible columns (${visibleColumns.size} of ${COLUMN_DEFS.length} shown)`}
                  >
                    <Columns3 className="w-3.5 h-3.5" />
                    Columns
                    <span className="ml-0.5 text-[10px] text-slate-400">
                      {visibleColumns.size}/{COLUMN_DEFS.length}
                    </span>
                  </Button>
                </PopoverTrigger>
                <PopoverContent align="end" className="w-52 p-3">
                  <div className="space-y-0.5">
                    <p className="text-xs font-medium text-slate-500 mb-2">Toggle columns</p>
                    {COLUMN_DEFS.map((col) => (
                      <label
                        key={col.key}
                        className="flex items-center gap-2 rounded px-1.5 py-1 hover:bg-slate-50 cursor-pointer text-sm"
                      >
                        <Checkbox
                          checked={visibleColumns.has(col.key)}
                          onCheckedChange={() => toggleColumn(col.key)}
                        />
                        {col.label}
                      </label>
                    ))}
                    <div className="border-t pt-2 mt-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="w-full text-xs"
                        onClick={() => {
                          setVisibleColumns(new Set(DEFAULT_VISIBLE_COLUMNS));
                          saveColumns(DEFAULT_VISIBLE_COLUMNS);
                        }}
                      >
                        Reset to default
                      </Button>
                    </div>
                  </div>
                </PopoverContent>
              </Popover>
              {(dir.activeFilterCount > 0 || dir.query) && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="gap-1 text-slate-500 hover:text-slate-700"
                  onClick={dir.clearAllFilters}
                  data-testid="employees-clear-filters"
                >
                  <X className="w-3.5 h-3.5" />
                  Clear all
                </Button>
              )}
            </div>
          </div>

          {/* Status Filter Pills */}
          <div className="flex items-center gap-1.5 flex-wrap" role="group" aria-label={`${dir.workflowFilterKind} workflow status filters`}>
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <button
              onClick={() => dir.setActiveStatusFilter("ALL")}
              aria-pressed={dir.activeStatusFilter === "ALL"}
              className={cn(
                "px-2.5 py-1 rounded-full text-xs font-medium transition-colors",
                dir.activeStatusFilter === "ALL"
                  ? "bg-slate-900 text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              )}
            >
              All ({dir.total})
            </button>
            {Object.entries(dir.statusCounts)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([status, count]) => (
                <button
                  key={status}
                  onClick={() => dir.setActiveStatusFilter(status)}
                  aria-pressed={dir.activeStatusFilter === status}
                  className={cn(
                    "px-2.5 py-1 rounded-full text-xs font-medium transition-colors",
                    dir.activeStatusFilter === status
                      ? STATUS_STYLES[status] || "bg-slate-900 text-white"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  )}
                >
                  {getWorkflowStatusLabel(status)} ({count})
                </button>
              ))}
          </div>

          {/* Rich Filter Panel */}
          {showFilters && (
            <div id="employees-filter-panel" className="rounded-lg border bg-white p-4 shadow-sm space-y-4" data-testid="employees-filter-panel">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Department */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600">Department</label>
                  <Select value={dir.departmentFilter} onValueChange={dir.setDepartmentFilter}>
                    <SelectTrigger className="w-full" data-testid="filter-department">
                      <SelectValue placeholder="All Departments" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ALL">All Departments</SelectItem>
                      {dir.departmentOptions.map((d) => (
                        <SelectItem key={d.value} value={d.value}>{d.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Employment Type */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600">Employment Type</label>
                  <Select value={dir.typeFilter} onValueChange={dir.setTypeFilter}>
                    <SelectTrigger className="w-full" data-testid="filter-employment-type">
                      <SelectValue placeholder="All Types" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ALL">All Types</SelectItem>
                      {dir.employmentTypeOptions.map((t) => (
                        <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Designation */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600">Designation</label>
                  <Select value={dir.designationFilter} onValueChange={dir.setDesignationFilter}>
                    <SelectTrigger className="w-full" data-testid="filter-designation">
                      <SelectValue placeholder="All Designations" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ALL">All Designations</SelectItem>
                      {dir.designationOptions.map((d) => (
                        <SelectItem key={d.value} value={d.value}>{d.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Office */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600">Office</label>
                  <Select value={dir.officeFilter} onValueChange={dir.setOfficeFilter}>
                    <SelectTrigger className="w-full" data-testid="filter-office">
                      <SelectValue placeholder="All Offices" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ALL">All Offices</SelectItem>
                      {dir.officeOptions.map((o) => (
                        <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Employee Status */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600">Employee Status</label>
                  <Select value={dir.employeeStatusFilter} onValueChange={dir.setEmployeeStatusFilter}>
                    <SelectTrigger className="w-full" data-testid="filter-employee-status">
                      <SelectValue placeholder="All Statuses" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ALL">All Statuses</SelectItem>
                      {dir.employeeStatusOptions.map((s) => (
                        <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Recruitment Mode */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600">Recruitment Mode</label>
                  <Select value={dir.recruitmentFilter} onValueChange={dir.setRecruitmentFilter}>
                    <SelectTrigger className="w-full" data-testid="filter-recruitment">
                      <SelectValue placeholder="All Modes" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ALL">All Modes</SelectItem>
                      {dir.recruitmentModeOptions.map((m) => (
                        <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Pay Level */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600">Pay Level</label>
                  <Select value={dir.payLevelFilter} onValueChange={dir.setPayLevelFilter}>
                    <SelectTrigger className="w-full" data-testid="filter-pay-level">
                      <SelectValue placeholder="All Pay Levels" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ALL">All Pay Levels</SelectItem>
                      {dir.payLevelOptions.map((p) => (
                        <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Service */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600">Service</label>
                  <Select value={dir.serviceFilter} onValueChange={dir.setServiceFilter}>
                    <SelectTrigger className="w-full" data-testid="filter-service">
                      <SelectValue placeholder="All Services" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ALL">All Services</SelectItem>
                      {dir.serviceOptions.map((s) => (
                        <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Service Group */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600">Group</label>
                  <Select value={dir.groupFilter} onValueChange={dir.setGroupFilter}>
                    <SelectTrigger className="w-full" data-testid="filter-group">
                      <SelectValue placeholder="All Groups" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ALL">All Groups</SelectItem>
                      {dir.serviceGroupOptions.map((g) => (
                        <SelectItem key={g.value} value={g.value}>{g.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Date of Appointment - From */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600">Appointed From</label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button variant="outline" className={cn("w-full justify-start text-left font-normal", !dir.dateFromFilter && "text-muted-foreground")} data-testid="filter-date-from">
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {dir.dateFromFilter ? format(new Date(dir.dateFromFilter), "dd MMM yyyy") : "Pick a date"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="start">
                      <Calendar
                        mode="single"
                        selected={dir.dateFromFilter ? new Date(dir.dateFromFilter) : undefined}
                        onSelect={(date) => dir.setDateFromFilter(date ? format(date, "yyyy-MM-dd") : "")}
                        initialFocus
                      />
                      {dir.dateFromFilter && (
                        <div className="px-3 pb-3">
                          <Button variant="ghost" size="sm" className="w-full text-xs" onClick={() => dir.setDateFromFilter("")}>Clear</Button>
                        </div>
                      )}
                    </PopoverContent>
                  </Popover>
                </div>

                {/* Date of Appointment - To */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600">Appointed To</label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button variant="outline" className={cn("w-full justify-start text-left font-normal", !dir.dateToFilter && "text-muted-foreground")} data-testid="filter-date-to">
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {dir.dateToFilter ? format(new Date(dir.dateToFilter), "dd MMM yyyy") : "Pick a date"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="start">
                      <Calendar
                        mode="single"
                        selected={dir.dateToFilter ? new Date(dir.dateToFilter) : undefined}
                        onSelect={(date) => dir.setDateToFilter(date ? format(date, "yyyy-MM-dd") : "")}
                        initialFocus
                      />
                      {dir.dateToFilter && (
                        <div className="px-3 pb-3">
                          <Button variant="ghost" size="sm" className="w-full text-xs" onClick={() => dir.setDateToFilter("")}>Clear</Button>
                        </div>
                      )}
                    </PopoverContent>
                  </Popover>
                </div>
              </div>

              {/* Active Filter Badges */}
              {dir.activeFilterCount > 0 && (
                <div className="flex items-center gap-2 flex-wrap pt-1 border-t">
                  <span className="text-xs text-slate-500">Active:</span>
                  {dir.activeStatusFilter !== "ALL" && (
                    <Badge variant="secondary" className="gap-1 text-xs cursor-pointer hover:bg-slate-200" onClick={() => dir.setActiveStatusFilter("ALL")}>
                      {dir.workflowFilterKind}: {getWorkflowStatusLabel(dir.activeStatusFilter)}
                      <X className="w-3 h-3" />
                    </Badge>
                  )}
                  {dir.departmentFilter !== "ALL" && (
                    <Badge variant="secondary" className="gap-1 text-xs cursor-pointer hover:bg-slate-200" onClick={() => dir.setDepartmentFilter("ALL")}>
                      Dept: {dir.departmentOptions.find((d) => d.value === dir.departmentFilter)?.label || dir.departmentFilter}
                      <X className="w-3 h-3" />
                    </Badge>
                  )}
                  {dir.typeFilter !== "ALL" && (
                    <Badge variant="secondary" className="gap-1 text-xs cursor-pointer hover:bg-slate-200" onClick={() => dir.setTypeFilter("ALL")}>
                      Type: {dir.employmentTypeOptions.find((t) => t.value === dir.typeFilter)?.label || dir.typeFilter}
                      <X className="w-3 h-3" />
                    </Badge>
                  )}
                  {dir.designationFilter !== "ALL" && (
                    <Badge variant="secondary" className="gap-1 text-xs cursor-pointer hover:bg-slate-200" onClick={() => dir.setDesignationFilter("ALL")}>
                      Designation: {dir.designationOptions.find((d) => d.value === dir.designationFilter)?.label || dir.designationFilter}
                      <X className="w-3 h-3" />
                    </Badge>
                  )}
                  {dir.officeFilter !== "ALL" && (
                    <Badge variant="secondary" className="gap-1 text-xs cursor-pointer hover:bg-slate-200" onClick={() => dir.setOfficeFilter("ALL")}>
                      Office: {dir.officeOptions.find((o) => o.value === dir.officeFilter)?.label || dir.officeFilter}
                      <X className="w-3 h-3" />
                    </Badge>
                  )}
                  {dir.employeeStatusFilter !== "ALL" && (
                    <Badge variant="secondary" className="gap-1 text-xs cursor-pointer hover:bg-slate-200" onClick={() => dir.setEmployeeStatusFilter("ALL")}>
                      Emp Status: {getEmployeeStatusLabel(dir.employeeStatusFilter)}
                      <X className="w-3 h-3" />
                    </Badge>
                  )}
                  {dir.recruitmentFilter !== "ALL" && (
                    <Badge variant="secondary" className="gap-1 text-xs cursor-pointer hover:bg-slate-200" onClick={() => dir.setRecruitmentFilter("ALL")}>
                      Recruitment: {dir.recruitmentFilter}
                      <X className="w-3 h-3" />
                    </Badge>
                  )}
                  {dir.payLevelFilter !== "ALL" && (
                    <Badge variant="secondary" className="gap-1 text-xs cursor-pointer hover:bg-slate-200" onClick={() => dir.setPayLevelFilter("ALL")}>
                      Pay: {dir.payLevelOptions.find((p) => p.value === dir.payLevelFilter)?.label || dir.payLevelFilter}
                      <X className="w-3 h-3" />
                    </Badge>
                  )}
                  {dir.serviceFilter !== "ALL" && (
                    <Badge variant="secondary" className="gap-1 text-xs cursor-pointer hover:bg-slate-200" onClick={() => dir.setServiceFilter("ALL")}>
                      Service: {dir.serviceOptions.find((s) => s.value === dir.serviceFilter)?.label || dir.serviceFilter}
                      <X className="w-3 h-3" />
                    </Badge>
                  )}
                  {dir.groupFilter !== "ALL" && (
                    <Badge variant="secondary" className="gap-1 text-xs cursor-pointer hover:bg-slate-200" onClick={() => dir.setGroupFilter("ALL")}>
                      Group: {dir.serviceGroupOptions.find((g) => g.value === dir.groupFilter)?.label || dir.groupFilter}
                      <X className="w-3 h-3" />
                    </Badge>
                  )}
                  {dir.dateFromFilter && (
                    <Badge variant="secondary" className="gap-1 text-xs cursor-pointer hover:bg-slate-200" onClick={() => dir.setDateFromFilter("")}>
                      From: {dir.dateFromFilter}
                      <X className="w-3 h-3" />
                    </Badge>
                  )}
                  {dir.dateToFilter && (
                    <Badge variant="secondary" className="gap-1 text-xs cursor-pointer hover:bg-slate-200" onClick={() => dir.setDateToFilter("")}>
                      To: {dir.dateToFilter}
                      <X className="w-3 h-3" />
                    </Badge>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Table */}
        {dir.loading ? (
          <div data-testid="employees-loading" className="space-y-6">
            <SearchBarSkeleton />
            <EmployeeTableSkeleton rows={8} />
          </div>
        ) : dir.employees.length === 0 ? (
          <Card>
            <CardContent className="py-16">
              <div className="flex flex-col items-center justify-center text-center">
                <Users className="w-7 h-7 text-slate-300 mb-3" />
                <p className="text-sm font-medium text-slate-600">No employees found</p>
                <p className="text-xs text-slate-400 mt-1">
                  {dir.query ? "Try a different search term" : "No employee records yet"}
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div
            className="rounded-xl border bg-white shadow-sm overflow-hidden"
            data-testid="employees-table"
          >
            <div
              ref={tableRef}
              className="max-h-[70vh] overflow-auto"
            >
            <Table>
              <TableHeader className="sticky top-0 z-10 bg-slate-50/95 backdrop-blur-sm">
                <TableRow className="border-b-2 border-slate-200">
                  {COLUMN_DEFS.filter((col) => visibleColumns.has(col.key)).map((col) => (
                    <SortHeader key={col.key} field={col.sortField}>{col.label}</SortHeader>
                  ))}
                  {canManageEmployeeAccounts && (
                    <TableHead className="text-right">Login Account</TableHead>
                  )}
                </TableRow>
              </TableHeader>
              <TableBody>
                {dir.employees.map((emp, rowIdx) => {
                  const profilePath = isPortalPath
                    ? `/portal/employees/${emp.employee_id}`
                    : `/employees/${emp.employee_id}`;

                  const formatDate = (d) => {
                    if (!d) return "-";
                    try { return new Date(d).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }); }
                    catch { return d; }
                  };

                  return (
                    <TableRow
                      key={emp.employee_id}
                      className={cn(
                        "hover:bg-blue-50/60 cursor-pointer group transition-colors",
                        rowIdx % 2 === 1 && "bg-slate-50/40"
                      )}
                      onClick={() => navigate(profilePath)}
                      data-testid={`employees-row-${emp.employee_id}`}
                    >
                      {COLUMN_DEFS.filter((col) => visibleColumns.has(col.key)).map((col) => (
                        <TableCell key={col.key} className="whitespace-nowrap text-sm text-slate-600">
                          {renderCell(emp, col.key, formatDate, labelMaps)}
                        </TableCell>
                      ))}
                      {canManageEmployeeAccounts && (
                        <TableCell className="text-right">
                          {(() => {
                            const availability = getProvisioningAvailability(emp);
                            const isProvisioning = actionLoading === `provision-${emp.employee_id}`;

                            return availability.canProvision ? (
                              <Button
                                variant="outline"
                                size="sm"
                                className="gap-1.5"
                                data-testid={`employees-provision-${emp.employee_id}`}
                                disabled={isProvisioning}
                                title={availability.reason}
                                onClick={(event) => {
                                  event.stopPropagation();
                                  void handleProvisionAccount(emp);
                                }}
                              >
                                {isProvisioning ? (
                                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                                ) : (
                                  <Key className="w-3.5 h-3.5" />
                                )}
                                {isProvisioning ? "Provisioning..." : availability.label}
                              </Button>
                            ) : (
                              <div className="inline-flex flex-col items-end gap-1">
                                <Badge
                                  variant="outline"
                                  className={cn(
                                    "text-[11px] font-normal",
                                    emp?.has_login_account
                                      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                                      : "text-slate-500"
                                  )}
                                >
                                  {availability.label}
                                </Badge>
                                <span className="text-[11px] text-slate-400">{availability.reason}</span>
                              </div>
                            );
                          })()}
                        </TableCell>
                      )}
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
            </div>
          </div>
        )}

        {/* Pagination + Count */}
        {dir.total > 0 && (
          <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-500">
            <span>
              Showing {dir.showingFrom}-{dir.showingTo} of {dir.total} employee
              {dir.total !== 1 ? "s" : ""}
              {dir.activeStatusFilter !== "ALL" && ` (${dir.workflowFilterKind} ${getWorkflowStatusLabel(dir.activeStatusFilter)})`}
            </span>
            {dir.totalPages > 1 && (
              <div className="flex items-center gap-1">
                <Button
                  variant="outline"
                  size="icon"
                  className="h-7 w-7"
                  disabled={dir.currentPage <= 1}
                  onClick={() => dir.setPage((p) => p - 1)}
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                </Button>
                {Array.from({ length: dir.totalPages }, (_, i) => i + 1)
                  .filter(
                    (p) =>
                      p === 1 ||
                      p === dir.totalPages ||
                      Math.abs(p - dir.currentPage) <= 1
                  )
                  .reduce((acc, p, idx, arr) => {
                    if (idx > 0 && p - arr[idx - 1] > 1) acc.push("...");
                    acc.push(p);
                    return acc;
                  }, [])
                  .map((item, idx) =>
                    item === "..." ? (
                      <span key={`dots-${idx}`} className="px-1 text-slate-400">
                        
                      </span>
                    ) : (
                      <Button
                        key={item}
                        variant={dir.currentPage === item ? "default" : "outline"}
                        size="icon"
                        className={cn(
                          "h-7 w-7 text-xs",
                          dir.currentPage === item && "pointer-events-none"
                        )}
                        onClick={() => dir.setPage(item)}
                      >
                        {item}
                      </Button>
                    )
                  )}
                <Button
                  variant="outline"
                  size="icon"
                  className="h-7 w-7"
                  disabled={dir.currentPage >= dir.totalPages}
                  onClick={() => dir.setPage((p) => p + 1)}
                >
                  <ChevronRight className="w-3.5 h-3.5" />
                </Button>
              </div>
            )}
          </div>
        )}
      </div>

    </Layout>
  );
};

export default EmployeeDirectoryPage;


