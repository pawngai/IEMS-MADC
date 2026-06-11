import { format } from "date-fns";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Checkbox } from "@/shared/ui/checkbox";
import { Input } from "@/shared/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import { Popover, PopoverContent, PopoverTrigger } from "@/shared/ui/popover";
import { Calendar } from "@/shared/ui/calendar";
import { cn } from "@/shared/lib/utils";
import {
  CalendarIcon,
  Columns3,
  Filter,
  Search,
  SlidersHorizontal,
  X,
} from "lucide-react";
import {
  COLUMN_DEFS,
  DEFAULT_VISIBLE_COLUMNS,
  STATUS_STYLES,
  saveColumns,
} from "@/contexts/employee_master/pages/EmployeeDirectoryPage.support";

const EmployeeDirectoryFilters = ({
  dir,
  getEmployeeStatusLabel,
  getWorkflowStatusLabel,
  setShowFilters,
  setVisibleColumns,
  showFilters,
  visibleColumns,
}) => {
  const toggleColumn = (key) => {
    setVisibleColumns((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      saveColumns(next);
      return next;
    });
  };

  return (
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

      {showFilters && (
        <div id="employees-filter-panel" className="rounded-lg border bg-white p-4 shadow-sm space-y-4" data-testid="employees-filter-panel">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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
  );
};

export default EmployeeDirectoryFilters;
