import { Badge } from "@/shared/ui/badge";
import { getReadablePersonName } from "@/shared/lib/readablePersonName";
import { cn } from "@/shared/lib/utils";

export const STATUS_STYLES = {
  DRAFT: "bg-slate-100 text-slate-700",
  SUBMITTED: "bg-blue-100 text-blue-700",
  VERIFIED: "bg-amber-100 text-amber-700",
  APPROVED: "bg-purple-100 text-purple-700",
  LOCKED: "bg-green-100 text-green-700",
  REJECTED: "bg-red-100 text-red-700",
};

export const EMPLOYEE_STATUS_STYLES = {
  PENDING: "border-blue-300 text-blue-700 bg-blue-50",
  ACTIVE: "border-green-300 text-green-700 bg-green-50",
  RETIRED: "border-amber-300 text-amber-700 bg-amber-50",
  SUSPENDED: "border-red-300 text-red-700 bg-red-50",
  DECEASED: "border-slate-400 text-slate-600 bg-slate-100",
};

export const COLUMN_DEFS = [
  { key: "employee_code", label: "Emp. Code", sortField: "employee_code", defaultVisible: true },
  { key: "full_name", label: "Name", sortField: "full_name", defaultVisible: true },
  { key: "gender", label: "Gender", sortField: "gender", defaultVisible: false },
  { key: "date_of_birth", label: "Date of Birth", sortField: "date_of_birth", defaultVisible: false },
  { key: "designation", label: "Designation", sortField: "current_designation_id", defaultVisible: true },
  { key: "department", label: "Department", sortField: "current_department_id", defaultVisible: true },
  { key: "office", label: "Office", sortField: "current_office_id", defaultVisible: true },
  { key: "employment_type", label: "Emp. Type", sortField: "employment_type", defaultVisible: true },
  { key: "date_of_joining", label: "Date of Appointment", sortField: "date_of_initial_engagement", defaultVisible: false },
  { key: "employee_status", label: "Identity Status", sortField: "employee_status", defaultVisible: true },
  { key: "identity_workflow_status", label: "Identity Workflow", sortField: "identity_workflow_status", defaultVisible: true },
  { key: "category", label: "Category", sortField: "category", defaultVisible: false },
  { key: "recruitment_mode", label: "Recruitment", sortField: "mode_of_recruitment", defaultVisible: false },
  { key: "pay_level", label: "Pay Level", sortField: "pay_level", defaultVisible: false },
  { key: "mobile", label: "Mobile", sortField: "mobile_primary", defaultVisible: false },
  { key: "email", label: "Email", sortField: "email_official", defaultVisible: false },
  { key: "workflow_status", label: "Profile Workflow", sortField: "workflow_status", defaultVisible: true },
];

export const DEFAULT_VISIBLE_COLUMNS = new Set(COLUMN_DEFS.filter((c) => c.defaultVisible).map((c) => c.key));

export const COLUMN_STORAGE_KEY = "iems_directory_columns";

export const loadSavedColumns = () => {
  try {
    const saved = localStorage.getItem(COLUMN_STORAGE_KEY);
    if (saved) {
      const keys = JSON.parse(saved);
      if (Array.isArray(keys) && keys.length > 0) return new Set(keys);
    }
  } catch { /* ignore corrupt data */ }
  return new Set(DEFAULT_VISIBLE_COLUMNS);
};

export const saveColumns = (cols) => {
  try {
    localStorage.setItem(COLUMN_STORAGE_KEY, JSON.stringify([...cols]));
  } catch { /* quota exceeded — ignore */ }
};

export const toTitleCase = (value) => String(value || "")
  .trim()
  .replace(/[_-]+/g, " ")
  .toLowerCase()
  .replace(/\b\w/g, (char) => char.toUpperCase());

export const formatDirectoryFallbackLabel = (value) => {
  const normalized = String(value || "").trim();

  if (!normalized) return "-";
  if (/^L\d+$/i.test(normalized)) return `Level ${normalized.slice(1)}`;
  if (/[ _-]/.test(normalized)) return toTitleCase(normalized);
  if (normalized === normalized.toUpperCase() && normalized.length > 4) return toTitleCase(normalized);

  return normalized;
};

export const buildLabelMap = (options = []) => new Map(
  options
    .filter((option) => option?.value)
    .map((option) => [String(option.value).trim().toUpperCase(), option.label || option.value]),
);

export const getMappedLabel = (values, labelMap) => {
  for (const value of values) {
    if (!value) continue;
    const normalized = String(value).trim();
    if (!normalized) continue;
    const mapped = labelMap.get(normalized.toUpperCase());
    if (mapped) return mapped;
  }
  return formatDirectoryFallbackLabel(values.find((value) => value));
};

export const getReadableEnumLabel = (values, labelMap) => {
  for (const value of values) {
    if (!value) continue;
    const normalized = String(value).trim();
    if (!normalized) continue;
    const mapped = labelMap.get(normalized.toUpperCase());
    return mapped ? toTitleCase(mapped) : toTitleCase(normalized);
  }
  return "-";
};

export const renderTruncatedValue = (value, className) => {
  const text = value || "-";
  return (
    <span title={text !== "-" ? text : undefined} className={className}>
      {text}
    </span>
  );
};

export const getVisibleEmployeeStatus = (emp) => {
  const identityWorkflowStatus = String(emp.identity_workflow_status || "").trim().toUpperCase();
  if (identityWorkflowStatus && identityWorkflowStatus !== "-" && identityWorkflowStatus !== "ACTIVE") {
    return "PENDING";
  }
  return emp.employee_status || "-";
};

export const renderCell = (emp, colKey, formatDate, labelMaps) => {
  switch (colKey) {
    case "employee_code":
      return <span className="font-mono text-xs text-slate-700">{emp.employee_code || "-"}</span>;
    case "full_name":
      return renderTruncatedValue(
        getReadablePersonName(emp.full_name) || "—",
        "font-medium text-slate-900 truncate max-w-[220px] block group-hover:text-blue-700 transition-colors",
      );
    case "gender":
      return emp.gender || "-";
    case "date_of_birth":
      return formatDate(emp.date_of_birth);
    case "designation":
      return renderTruncatedValue(
        getMappedLabel(
          [emp.current_designation_name, emp.designation_name, emp.current_designation_id, emp.designation_code],
          labelMaps.designation,
        ),
        "truncate block max-w-[190px]",
      );
    case "department":
      return renderTruncatedValue(
        getMappedLabel(
          [emp.current_department_name, emp.department_name, emp.current_department_id, emp.department_code],
          labelMaps.department,
        ),
        "truncate block max-w-[190px]",
      );
    case "office":
      return renderTruncatedValue(
        getMappedLabel(
          [emp.current_office_name, emp.office_name, emp.current_office_id, emp.office_code],
          labelMaps.office,
        ),
        "truncate block max-w-[180px]",
      );
    case "employment_type":
      return (
        <Badge variant="outline" className="text-xs font-normal">
          {getReadableEnumLabel(
            [emp.employment_type_name, emp.employment_type, emp.employment_type_code],
            labelMaps.employmentType,
          )}
        </Badge>
      );
    case "date_of_joining":
      return formatDate(emp.date_of_initial_engagement);
    case "employee_status": {
      const visibleEmployeeStatus = getVisibleEmployeeStatus(emp);
      return (
        <Badge variant="outline" className={cn("text-xs font-normal", EMPLOYEE_STATUS_STYLES[visibleEmployeeStatus])}>
          {getReadableEnumLabel([visibleEmployeeStatus], labelMaps.employeeStatus)}
        </Badge>
      );
    }
    case "identity_workflow_status":
      return (
        <Badge variant="outline" className={cn("text-xs font-normal", STATUS_STYLES[emp.identity_workflow_status] || "bg-slate-50 text-slate-600")}>
          {getReadableEnumLabel([emp.identity_workflow_status || "-"], labelMaps.workflowStatus)}
        </Badge>
      );
    case "category":
      return emp.category || "-";
    case "recruitment_mode":
      return emp.mode_of_recruitment || "-";
    case "pay_level":
      return emp.pay_level || emp.basic_pay || "-";
    case "mobile":
      return <span className="font-mono text-xs">{emp.mobile_primary || emp.contact?.mobile_primary || "-"}</span>;
    case "email":
      return renderTruncatedValue(
        emp.email_official || emp.contact?.email_official || "-",
        "text-xs truncate block max-w-[220px]",
      );
    case "workflow_status":
      return (
        <Badge className={cn("text-xs", STATUS_STYLES[emp.profile_workflow_status || emp.workflow_status] || "bg-slate-100 text-slate-700")}>
          {getReadableEnumLabel([emp.profile_workflow_status || emp.workflow_status || "DRAFT"], labelMaps.workflowStatus)}
        </Badge>
      );
    default:
      return "-";
  }
};

