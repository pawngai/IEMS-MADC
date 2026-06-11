import { Badge } from "@/shared/ui/badge";

const STATUS_BADGE = {
  DRAFT: { variant: "secondary", className: "" },
  SUBMITTED: { variant: "default", className: "" },
  VERIFIED: { variant: "outline", className: "border-blue-500 text-blue-700 bg-blue-50" },
  APPROVED: { variant: "outline", className: "border-green-600 text-green-700 bg-green-50" },
  REJECTED: { variant: "destructive", className: "" },
};

export const SERVICES = ["MINISTERIAL", "ENGINEERING", "GENERAL"];
export const DESIGNATIONS_FALLBACK = ["ASO", "SO", "UDC", "LDC", "AN", "CLERK", "JE", "AE"];
export const LIST_TYPES = ["DRAFT", "PROVISIONAL", "FINAL"];

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

export const PROMOTION_LABELS = {
  DRAFT: "Promote to Provisional",
  PROVISIONAL: "Promote to Final",
};

const toTitleCase = (value) => String(value)
  .toLowerCase()
  .split(/[_\s]+/)
  .filter(Boolean)
  .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
  .join(" ");

export const formatEnumLabel = (value, fallback = "-") => value ? toTitleCase(value) : fallback;

export const formatServiceLabel = (service) => {
  if (!service) return "-";

  const normalized = String(service).trim().toUpperCase();
  const groupMatch = normalized.match(/^GRP[-_\s]([A-Z])$/);
  if (groupMatch) return `Group ${groupMatch[1]}`;
  if (SERVICE_LABELS[normalized]) return SERVICE_LABELS[normalized];
  if (/^[A-Z]{2,4}$/.test(normalized)) return normalized;
  return formatEnumLabel(normalized);
};

export const formatGroupLabel = (group) => {
  if (!group) return "-";

  const normalized = String(group).trim().toUpperCase();
  const groupMatch = normalized.match(/^(?:GROUP|GRP)[-_\s]?([A-Z])$/);
  if (groupMatch) return `Group ${groupMatch[1]}`;
  return formatEnumLabel(normalized, group);
};

export const formatGeneratedListTitle = (title) => {
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

export const StatusBadge = ({ status, prefix = null }) => {
  const cfg = STATUS_BADGE[status] || { variant: "secondary", className: "" };
  const label = formatEnumLabel(status);
  return <Badge variant={cfg.variant} className={cfg.className}>{prefix ? `${prefix}: ${label}` : label}</Badge>;
};

export const ListTypeBadge = ({ listType, prefix = null }) => {
  const t = listType || "DRAFT";
  const cfg = LIST_TYPE_BADGE[t] || { variant: "secondary", className: "" };
  const label = formatEnumLabel(t);
  return <Badge variant={cfg.variant} className={cfg.className}>{prefix ? `${prefix}: ${label}` : label}</Badge>;
};

export const formatDateTime = (v) => v ? v.slice(0, 16).replace("T", " ") : null;
export const formatPreciseDateTime = (v) => v ? v.slice(0, 19).replace("T", " ") : null;
export const formatVersionLabel = (value) => {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue) || numericValue < 1) return "Version 1";
  return `Version ${numericValue}`;
};

export const buildRankValidationMessage = (employees, rankEdits) => {
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

export const getEffectiveRank = (employee, rankEdits) => Number(rankEdits[employee.employee_id] ?? employee.rank);

export const buildSwappedRankEdits = ({ employees, rankEdits, employeeId, direction }) => {
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

export const formatDesignation = (designationCode) => {
  if (!designationCode) return "All Designations";

  const normalized = String(designationCode).trim().toUpperCase();
  const levelMatch = normalized.match(/^L(\d+)$/);
  if (levelMatch) return `Level ${levelMatch[1]}`;
  if (DESIGNATION_LABELS[normalized]) return DESIGNATION_LABELS[normalized];
  if (/[\s_]/.test(normalized)) return toTitleCase(normalized);
  return designationCode;
};
