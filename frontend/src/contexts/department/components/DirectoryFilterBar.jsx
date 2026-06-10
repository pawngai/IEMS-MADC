import { useState } from "react";
import { format } from "date-fns";

import { cn } from "@/shared/lib/utils";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Calendar } from "@/shared/ui/calendar";
import { Input } from "@/shared/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/shared/ui/popover";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import {
  CalendarIcon, ChevronDown, ChevronUp, Filter, LayoutGrid,
  Search, SlidersHorizontal, Table2, X,
} from "lucide-react";

import { STATUS_STYLES } from "@/contexts/department/components/EmployeeCard";

function FilterSelect({ label, value, onValueChange, placeholder, options }) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium text-slate-600">{label}</label>
      <Select value={value} onValueChange={onValueChange}>
        <SelectTrigger className="w-full h-9 text-xs">
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="ALL">{placeholder}</SelectItem>
          {options.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

function FilterDatePicker({ label, value, onChange }) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium text-slate-600">{label}</label>
      <Popover>
        <PopoverTrigger asChild>
          <Button variant="outline" className={cn("w-full h-9 justify-start text-left text-xs font-normal", !value && "text-muted-foreground")}>
            <CalendarIcon className="mr-2 h-3.5 w-3.5" />
            {value ? format(new Date(value), "dd MMM yyyy") : "Pick a date"}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="single"
            selected={value ? new Date(value) : undefined}
            onSelect={(date) => onChange(date ? format(date, "yyyy-MM-dd") : "")}
            initialFocus
          />
          {value && (
            <div className="px-3 pb-3">
              <Button variant="ghost" size="sm" className="w-full text-xs" onClick={() => onChange("")}>Clear</Button>
            </div>
          )}
        </PopoverContent>
      </Popover>
    </div>
  );
}

const FILTER_GROUPS = [
  {
    key: "position",
    label: "Position & Role",
    fields: ["type", "designation", "office", "employeeStatus"],
  },
  {
    key: "service",
    label: "Service & Pay",
    fields: ["recruitment", "payLevel", "service", "group"],
  },
  {
    key: "dates",
    label: "Date Range",
    fields: ["dateFrom", "dateTo"],
  },
];

export function DirectoryFilterBar({ dir, viewMode, onViewModeChange }) {
  const [showFilters, setShowFilters] = useState(() => dir.activeFilterCount > 0);
  const [expandedGroup, setExpandedGroup] = useState(null);

  const toggleGroup = (key) => {
    setExpandedGroup((prev) => (prev === key ? null : key));
  };

  const renderFilterField = (field) => {
    switch (field) {
      case "type":
        return <FilterSelect key={field} label="Employment Type" value={dir.typeFilter} onValueChange={dir.setTypeFilter} placeholder="All Types" options={dir.employmentTypeOptions} />;
      case "designation":
        return <FilterSelect key={field} label="Designation" value={dir.designationFilter} onValueChange={dir.setDesignationFilter} placeholder="All Designations" options={dir.designationOptions} />;
      case "office":
        return <FilterSelect key={field} label="Office" value={dir.officeFilter} onValueChange={dir.setOfficeFilter} placeholder="All Offices" options={dir.officeOptions} />;
      case "employeeStatus":
        return <FilterSelect key={field} label="Employee Status" value={dir.employeeStatusFilter} onValueChange={dir.setEmployeeStatusFilter} placeholder="All Statuses" options={dir.employeeStatusOptions} />;
      case "recruitment":
        return <FilterSelect key={field} label="Recruitment Mode" value={dir.recruitmentFilter} onValueChange={dir.setRecruitmentFilter} placeholder="All Modes" options={dir.recruitmentModeOptions} />;
      case "payLevel":
        return <FilterSelect key={field} label="Pay Level" value={dir.payLevelFilter} onValueChange={dir.setPayLevelFilter} placeholder="All Pay Levels" options={dir.payLevelOptions} />;
      case "service":
        return <FilterSelect key={field} label="Service" value={dir.serviceFilter} onValueChange={dir.setServiceFilter} placeholder="All Services" options={dir.serviceOptions} />;
      case "group":
        return <FilterSelect key={field} label="Group" value={dir.groupFilter} onValueChange={dir.setGroupFilter} placeholder="All Groups" options={dir.serviceGroupOptions} />;
      case "dateFrom":
        return <FilterDatePicker key={field} label="Appointed From" value={dir.dateFromFilter} onChange={dir.setDateFromFilter} />;
      case "dateTo":
        return <FilterDatePicker key={field} label="Appointed To" value={dir.dateToFilter} onChange={dir.setDateToFilter} />;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-3">
      {/* Search + Filter toggle + View toggle row */}
      <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <Input
            value={dir.query}
            onChange={(e) => dir.setQuery(e.target.value)}
            placeholder="Search name, code, designation, office..."
            className="pl-9 h-9"
            data-testid="dept-directory-search"
          />
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant={showFilters ? "default" : "outline"}
            size="sm"
            className="gap-1.5 h-9"
            onClick={() => setShowFilters((v) => !v)}
            data-testid="dept-directory-toggle-filters"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            Filters
            {dir.activeFilterCount > 0 && (
              <span className="ml-1 inline-flex items-center justify-center w-5 h-5 rounded-full bg-blue-100 text-blue-700 text-[10px] font-bold">
                {dir.activeFilterCount}
              </span>
            )}
          </Button>

          {(dir.activeFilterCount > 0 || dir.query) && (
            <Button variant="ghost" size="sm" className="gap-1 text-slate-500 hover:text-slate-700 h-9" onClick={dir.clearAllFilters} data-testid="dept-directory-clear-filters">
              <X className="w-3.5 h-3.5" />
              Clear all
            </Button>
          )}

          {/* View toggle */}
          <div className="hidden sm:flex items-center border rounded-md overflow-hidden">
            <button
              onClick={() => onViewModeChange("cards")}
              className={cn(
                "p-1.5 transition-colors",
                viewMode === "cards" ? "bg-slate-900 text-white" : "bg-white text-slate-500 hover:text-slate-700"
              )}
              title="Card view"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => onViewModeChange("table")}
              className={cn(
                "p-1.5 transition-colors",
                viewMode === "table" ? "bg-slate-900 text-white" : "bg-white text-slate-500 hover:text-slate-700"
              )}
              title="Table view"
            >
              <Table2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Workflow status pills */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <Filter className="w-3.5 h-3.5 text-slate-400" />
        <button
          onClick={() => dir.setActiveStatusFilter("ALL")}
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
              className={cn(
                "px-2.5 py-1 rounded-full text-xs font-medium transition-colors",
                dir.activeStatusFilter === status
                  ? STATUS_STYLES[status] || "bg-slate-900 text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              )}
            >
              {status} ({count})
            </button>
          ))}
      </div>

      {/* Collapsible filter groups */}
      {showFilters && (
        <div className="rounded-lg border bg-white shadow-sm overflow-hidden" data-testid="dept-directory-filter-panel">
          {FILTER_GROUPS.map((group) => {
            const isExpanded = expandedGroup === group.key || expandedGroup === null;
            return (
              <div key={group.key} className="border-b last:border-b-0">
                <button
                  className="w-full flex items-center justify-between px-4 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
                  onClick={() => toggleGroup(group.key)}
                >
                  {group.label}
                  {isExpanded
                    ? <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
                    : <ChevronDown className="w-3.5 h-3.5 text-slate-400" />}
                </button>
                {isExpanded && (
                  <div className="px-4 pb-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    {group.fields.map(renderFilterField)}
                  </div>
                )}
              </div>
            );
          })}

          {/* Active filter badges */}
          {dir.activeFilterCount > 0 && (
            <div className="flex items-center gap-2 flex-wrap px-4 py-3 bg-slate-50 border-t">
              <span className="text-xs text-slate-500">Active:</span>
              {dir.activeStatusFilter !== "ALL" && (
                <Badge variant="secondary" className="gap-1 text-xs cursor-pointer hover:bg-slate-200" onClick={() => dir.setActiveStatusFilter("ALL")}>
                  Status: {dir.activeStatusFilter} <X className="w-3 h-3" />
                </Badge>
              )}
              {dir.typeFilter !== "ALL" && (
                <Badge variant="secondary" className="gap-1 text-xs cursor-pointer hover:bg-slate-200" onClick={() => dir.setTypeFilter("ALL")}>
                  Type: {dir.employmentTypeOptions.find((o) => o.value === dir.typeFilter)?.label || dir.typeFilter} <X className="w-3 h-3" />
                </Badge>
              )}
              {dir.designationFilter !== "ALL" && (
                <Badge variant="secondary" className="gap-1 text-xs cursor-pointer hover:bg-slate-200" onClick={() => dir.setDesignationFilter("ALL")}>
                  Designation: {dir.designationOptions.find((o) => o.value === dir.designationFilter)?.label || dir.designationFilter} <X className="w-3 h-3" />
                </Badge>
              )}
              {dir.officeFilter !== "ALL" && (
                <Badge variant="secondary" className="gap-1 text-xs cursor-pointer hover:bg-slate-200" onClick={() => dir.setOfficeFilter("ALL")}>
                  Office: {dir.officeOptions.find((o) => o.value === dir.officeFilter)?.label || dir.officeFilter} <X className="w-3 h-3" />
                </Badge>
              )}
              {dir.employeeStatusFilter !== "ALL" && (
                <Badge variant="secondary" className="gap-1 text-xs cursor-pointer hover:bg-slate-200" onClick={() => dir.setEmployeeStatusFilter("ALL")}>
                  Emp Status: {dir.employeeStatusFilter} <X className="w-3 h-3" />
                </Badge>
              )}
              {dir.recruitmentFilter !== "ALL" && (
                <Badge variant="secondary" className="gap-1 text-xs cursor-pointer hover:bg-slate-200" onClick={() => dir.setRecruitmentFilter("ALL")}>
                  Recruitment: {dir.recruitmentFilter} <X className="w-3 h-3" />
                </Badge>
              )}
              {dir.payLevelFilter !== "ALL" && (
                <Badge variant="secondary" className="gap-1 text-xs cursor-pointer hover:bg-slate-200" onClick={() => dir.setPayLevelFilter("ALL")}>
                  Pay: {dir.payLevelOptions.find((o) => o.value === dir.payLevelFilter)?.label || dir.payLevelFilter} <X className="w-3 h-3" />
                </Badge>
              )}
              {dir.serviceFilter !== "ALL" && (
                <Badge variant="secondary" className="gap-1 text-xs cursor-pointer hover:bg-slate-200" onClick={() => dir.setServiceFilter("ALL")}>
                  Service: {dir.serviceOptions.find((o) => o.value === dir.serviceFilter)?.label || dir.serviceFilter} <X className="w-3 h-3" />
                </Badge>
              )}
              {dir.groupFilter !== "ALL" && (
                <Badge variant="secondary" className="gap-1 text-xs cursor-pointer hover:bg-slate-200" onClick={() => dir.setGroupFilter("ALL")}>
                  Group: {dir.serviceGroupOptions.find((o) => o.value === dir.groupFilter)?.label || dir.groupFilter} <X className="w-3 h-3" />
                </Badge>
              )}
              {dir.dateFromFilter && (
                <Badge variant="secondary" className="gap-1 text-xs cursor-pointer hover:bg-slate-200" onClick={() => dir.setDateFromFilter("")}>
                  From: {dir.dateFromFilter} <X className="w-3 h-3" />
                </Badge>
              )}
              {dir.dateToFilter && (
                <Badge variant="secondary" className="gap-1 text-xs cursor-pointer hover:bg-slate-200" onClick={() => dir.setDateToFilter("")}>
                  To: {dir.dateToFilter} <X className="w-3 h-3" />
                </Badge>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
