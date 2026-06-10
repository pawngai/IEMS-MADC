const safeArray = (value) => (Array.isArray(value) ? value : []);

const SERVICE_BOOK_PART_NAMES = {
  I: "Bio-Data",
  "II-A": "Immutable Certs",
  "II-B": "Mutable Certs",
  III: "Previous Service",
  IV: "Service History",
  V: "Verification",
  VI: "Leave Account",
  VII: "Other Records",
  VIII: "Audit Comments",
};

import { getReadablePersonName } from "@/shared/lib/readablePersonName";

const toTitleCase = (value) => String(value || "")
  .trim()
  .toLowerCase()
  .replace(/\b\w/g, (char) => char.toUpperCase());

const OPAQUE_IDENTIFIER_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

const isOpaqueIdentifier = (value) => OPAQUE_IDENTIFIER_PATTERN.test(String(value || "").trim());

const formatOpaqueReference = (label, value) => {
  const normalized = String(value || "").trim();
  if (!normalized) return "";
  if (!isOpaqueIdentifier(normalized)) return normalized;
  return `${label} ${normalized.slice(0, 8)}`;
};

const normalizeServiceBookPartKey = (value) => {
  const normalized = String(value || "").trim().toUpperCase().replace(/_/g, "-");
  if (!normalized) return "";
  if (normalized.startsWith("SB-PART-")) return normalized.slice("SB-PART-".length);
  if (normalized.startsWith("SB PART ")) return normalized.slice("SB PART ".length);
  return normalized;
};

const formatServiceBookPartLabel = (partKey) => {
  const normalizedPart = normalizeServiceBookPartKey(partKey);
  if (!normalizedPart) return "";

  const partName = SERVICE_BOOK_PART_NAMES[normalizedPart];
  return partName ? `Part ${normalizedPart}: ${partName}` : `Part ${normalizedPart}`;
};

const formatServiceBookSchemaLabel = (schemaKey) => {
  const rawValue = String(schemaKey || "").trim().toUpperCase();
  if (!rawValue) return "";

  let normalized = rawValue.replace(/^SB_?PART_/, "");
  if (normalized === rawValue) {
    normalized = rawValue.replace(/^SB_/, "");
  }
  normalized = normalized.replace(/^IIA_/, "");
  normalized = normalized.replace(/^IIB_/, "");
  normalized = normalized.replace(/^(I|II_A|II_B|III|IV|V|VI|VII|VIII)_/, "");
  normalized = normalized.replace(/_ROW$/, "");
  normalized = normalized.replace(/_ENTRY$/, "");
  normalized = normalized.replace(/_/g, " ").trim();

  return normalized ? toTitleCase(normalized).replace(/\bGpf\b/g, "Pcf") : "";
};

const buildServiceBookQueueLabels = (entry) => {
  const partLabel = formatServiceBookPartLabel(entry.part_key || entry.schema_key);
  const schemaLabel = formatServiceBookSchemaLabel(entry.schema_key);
  const displayName = getReadablePersonName(entry.full_name);
  const identityLabel = entry.employee_code || formatOpaqueReference("Employee", entry.employee_id);
  const entryReference = formatOpaqueReference("Entry", entry.id);
  const title = displayName || identityLabel || schemaLabel || "Service Book Entry";
  const subtitleParts = [];
  const schemaLabelCoveredByPart = partLabel && schemaLabel && partLabel.endsWith(`: ${schemaLabel}`);

  if (displayName && identityLabel) subtitleParts.push(identityLabel);
  if (partLabel) subtitleParts.push(partLabel);
  if (schemaLabel && schemaLabel !== title && !schemaLabelCoveredByPart) subtitleParts.push(schemaLabel);
  if (!displayName && !entry.employee_code && isOpaqueIdentifier(entry.employee_id) && entryReference) {
    subtitleParts.push(entryReference);
  }

  return {
    title,
    subtitle: subtitleParts.join(" • "),
    displayName: displayName || null,
  };
};

const pickTimestamp = (item) =>
  item?.updated_at || item?.updatedAt || item?.timestamp || item?.created_at || item?.createdAt || null;

export const getAgeHours = (timestamp) => {
  if (!timestamp) return null;
  try {
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) return null;
    return (Date.now() - date.getTime()) / 3600000;
  } catch {
    return null;
  }
};

export const getSlaTier = (hours) => {
  if (hours == null) return "NONE";
  if (hours < 24) return "GREEN";
  if (hours < 72) return "YELLOW";
  return "RED";
};

export const STAGE_ORDER = {
  NOW: 0,
  DRAFT: 1,
  SUBMITTED: 2,
  VERIFIED: 3,
  APPROVED: 4,
  REJECTED: 5,
  LOCKED: 6,
};

export const toEssTaskItem = ({ profile, user }) => ({
  id: "ess:complete-profile",
  type: "ess",
  stage: "NOW",
  statusLabel: profile?.workflow_status || "DRAFT",
  employeeId: user?.employee_id,
  title: "Complete your profile section",
  subtitle: "Required before Data Entry can submit your record.",
  timestamp: pickTimestamp(profile),
  raw: profile,
});

export const toProfileItems = ({ profiles, stage }) =>
  safeArray(profiles).map((profile) => {
    const displayName = getReadablePersonName(profile.full_name);
    const workflowStage = profile.workflow_status || stage;

    return {
      id: `profile:${profile.employee_id}`,
      type: "profile",
      stage: workflowStage,
      statusLabel: workflowStage,
      employeeId: profile.employee_id,
      employeeCode: profile.employee_code,
      title: displayName || profile.employee_code || "Employee Profile",
      subtitle: profile.employee_code && displayName ? profile.employee_code : displayName ? "" : profile.employee_code || "",
      displayName: displayName || null,
      timestamp: pickTimestamp(profile),
      raw: profile,
    };
  });

export const toIdentityItems = ({ identities, stage }) =>
  safeArray(identities).map((identity) => {
    const displayName = getReadablePersonName(identity.full_name);

    return {
      id: `identity:${identity.employee_id}`,
      type: "identity",
      stage,
      statusLabel: identity.workflow_status || stage,
      employeeId: identity.employee_id,
      employeeCode: identity.employee_code,
      title: displayName || identity.employee_code || "Employee Identity",
      subtitle: [
        identity.employee_code && displayName ? identity.employee_code : "",
        identity.current_department_id || "",
        identity.current_designation_id || "",
      ].filter(Boolean).join(" • "),
      displayName: displayName || null,
      timestamp: pickTimestamp(identity),
      raw: identity,
    };
  });

export const toServiceBookItems = ({ entries, stage }) =>
  safeArray(entries).map((entry) => {
    const labels = buildServiceBookQueueLabels(entry);

    return {
      id: `service:${entry.id}`,
      type: "service",
      stage,
      statusLabel: entry.workflow_state || stage,
      employeeId: entry.employee_id,
      employeeCode: entry.employee_code || "",
      displayName: labels.displayName,
      title: labels.title,
      subtitle: labels.subtitle,
      timestamp: pickTimestamp(entry),
      raw: entry,
    };
  });

export const toServiceBookOpeningItems = ({ openings, stage }) =>
  safeArray(openings).map((opening) => {
    const displayName = getReadablePersonName(opening.full_name || opening.employee_name);
    const identityLabel = opening.employee_code || formatOpaqueReference("Employee", opening.employee_id);

    return {
      id: `service_opening:${opening.employee_id || opening.employee_code}`,
      type: "service_opening",
      stage: opening.workflow_status || opening.status || stage,
      statusLabel: opening.workflow_status || opening.status || stage,
      employeeId: opening.employee_id,
      employeeCode: opening.employee_code || "",
      displayName: displayName || null,
      title: displayName || identityLabel || "Service Book Opening",
      subtitle: [
        displayName && identityLabel ? identityLabel : "",
        "Opening Workflow",
      ].filter(Boolean).join(" • "),
      timestamp: pickTimestamp(opening),
      raw: opening,
    };
  });

export const toChangeRequestItems = ({ items, stage }) =>
  safeArray(items).map((cr) => ({
    id: `change_request:${cr.id || cr.request_id}`,
    type: "change_request",
    stage,
    statusLabel: cr.status || stage,
    employeeId: cr.employee_id,
    title: cr.employee_name || "Change Request",
    subtitle: cr.category || cr.request_type || "",
    timestamp: pickTimestamp(cr),
    raw: cr,
  }));

const AMBIGUOUS_QUEUE_TYPES = new Set(["identity", "profile"]);

const getQueueKindLabel = (type) => {
  if (type === "identity") return "Identity workflow";
  if (type === "profile") return "Profile workflow";
  return "";
};

export const enrichAndSortQueueItems = (items) => {
  const normalized = safeArray(items).map((item) => {
    const ageHours = getAgeHours(item.timestamp);
    return {
      ...item,
      ageHours,
      sla: getSlaTier(ageHours),
    };
  });

  const ambiguousBuckets = new Map();
  for (const item of normalized) {
    if (!AMBIGUOUS_QUEUE_TYPES.has(item.type)) continue;

    const employeeId = String(item.employeeId || "").trim();
    const stage = String(item.stage || "").trim().toUpperCase();
    if (!employeeId || !stage) continue;

    const bucketKey = `${employeeId}:${stage}`;
    const bucket = ambiguousBuckets.get(bucketKey) || [];
    bucket.push(item);
    ambiguousBuckets.set(bucketKey, bucket);
  }

  for (const bucket of ambiguousBuckets.values()) {
    if (bucket.length < 2) continue;

    for (const item of bucket) {
      const kindLabel = getQueueKindLabel(item.type);
      if (!kindLabel) continue;
      item.subtitle = [item.subtitle, kindLabel].filter(Boolean).join(" • ");
    }
  }

  normalized.sort((a, b) => {
    const stageA = STAGE_ORDER[a.stage] ?? 99;
    const stageB = STAGE_ORDER[b.stage] ?? 99;
    if (stageA !== stageB) return stageA - stageB;
    return (b.ageHours ?? 0) - (a.ageHours ?? 0);
  });

  return normalized;
};
