const WORKFLOW_STAGE_LABELS = {
  NOW: "Action Needed",
  DRAFT: "Draft",
  SUBMITTED: "Submitted",
  VERIFIED: "Verified",
  APPROVED: "Approved",
  LOCKED: "Locked",
  REJECTED: "Rejected",
  RECOMMENDED: "Recommended",
  SANCTIONED: "Sanctioned",
  PENDING: "Pending",
  SUPERSEDED: "Superseded",
};

const toTitleCase = (value) => String(value || "")
  .trim()
  .replace(/[_-]+/g, " ")
  .toLowerCase()
  .replace(/\b\w/g, (char) => char.toUpperCase());

export const formatDirectoryEnumLabel = (value) => toTitleCase(value);

export const formatDirectoryFallbackLabel = (value) => {
  const normalized = String(value || "").trim();

  if (!normalized) return "-";

  const compact = normalized.toUpperCase();
  const payLevelMatch = compact.match(/^L(?:EVEL)?[_ -]?(\d+)$/i);
  if (payLevelMatch) return `Level ${payLevelMatch[1]}`;

  const serviceGroupMatch = compact.match(/^(?:GROUP[_ -]?)?([A-D])$/i);
  if (serviceGroupMatch && compact.length <= "GROUP_D".length) {
    return `Group ${serviceGroupMatch[1].toUpperCase()}`;
  }

  if (/[a-z]/.test(normalized) && !/[_-]/.test(normalized)) return normalized;
  if (/[ _-]/.test(normalized)) return toTitleCase(normalized);
  if (normalized === compact && normalized.length > 4) return toTitleCase(normalized);

  return normalized;
};

export const formatWorkflowStatusLabel = (value) => {
  const normalized = String(value || "").trim().toUpperCase();
  if (!normalized) return "Unknown";
  return WORKFLOW_STAGE_LABELS[normalized] || formatDirectoryEnumLabel(normalized);
};

const getReferenceKey = (item) => {
  if (item === null || item === undefined) return "";
  if (typeof item !== "object") return String(item).trim();

  return String(
    item.code
    || item.value
    || item.id
    || item.department_code
    || item.designation_code
    || item.office_code
    || item.employment_type_code
    || item.service_group_code
    || item.pay_level_code
    || item.name
    || ""
  ).trim();
};

const getReferenceDisplay = (item) => {
  if (item === null || item === undefined) return "";
  if (typeof item !== "object") return String(item).trim();

  return String(
    item.description
    || item.label
    || item.name
    || item.title
    || item.code
    || item.value
    || item.id
    || ""
  ).trim();
};

export const buildReferenceLabelMap = (items = []) => new Map(
  (Array.isArray(items) ? items : [])
    .map((item) => ({ key: getReferenceKey(item), label: getReferenceDisplay(item) }))
    .filter((item) => item.key && item.label)
    .map((item) => [item.key.toUpperCase(), item.label]),
);

export const resolveReferenceLabel = (values, labelMap = new Map(), fallbackFormatter = formatDirectoryFallbackLabel) => {
  const candidates = Array.isArray(values) ? values : [values];

  for (const value of candidates) {
    if (value === null || value === undefined) continue;
    const normalized = String(value).trim();
    if (!normalized) continue;
    const mapped = labelMap.get(normalized.toUpperCase());
    if (mapped) return mapped;
  }

  return fallbackFormatter(candidates.find((value) => String(value || "").trim()));
};
