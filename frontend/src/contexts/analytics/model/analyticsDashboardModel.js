export const CHART_COLORS = [
  "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
  "#06b6d4", "#ec4899", "#14b8a6", "#f97316", "#6366f1",
  "#84cc16", "#a855f7", "#22d3ee", "#e11d48", "#0ea5e9",
];

export const STATUS_COLORS = {
  DRAFT:       "#94a3b8",
  SUBMITTED:   "#3b82f6",
  VERIFIED:    "#f59e0b",
  APPROVED:    "#8b5cf6",
  LOCKED:      "#10b981",
  REJECTED:    "#ef4444",
  SUPERSEDED:  "#6b7280",
};

export const LEAVE_STATUS_COLORS = {
  SUBMITTED:    "#3b82f6",
  RECOMMENDED:  "#6366f1",
  SANCTIONED:   "#10b981",
  REJECTED:     "#ef4444",
  CANCELLED:    "#94a3b8",
};

export const LEAVE_STATUS_LABELS = {
  SUBMITTED: "Submitted",
  RECOMMENDED: "Recommended",
  SANCTIONED: "Sanctioned",
  REJECTED: "Rejected",
  CANCELLED: "Cancelled",
};

export const WORKFLOW_STAGE_LABELS = {
  DRAFT: "Draft",
  SUBMITTED: "Submitted",
  VERIFIED: "Verified",
  APPROVED: "Approved",
  LOCKED: "Locked",
  REJECTED: "Rejected",
  SUPERSEDED: "Superseded",
};

export const WORKFLOW_STAGE_ORDER = ["DRAFT", "SUBMITTED", "VERIFIED", "APPROVED", "LOCKED", "REJECTED", "SUPERSEDED"];

export const COUNT_AXIS_TICK = { fontSize: 12 };
export const COUNT_AXIS_PROPS = {
  allowDecimals: false,
  tick: COUNT_AXIS_TICK,
};
export const CHART_AXIS_LABEL_LIMIT = 18;
export const DRILLDOWN_ROW_LIMIT = 50;
export const DRILLDOWN_EXPORT_LIMIT = 5000;

export const normalizeMasterCode = (value) => String(value ?? "").trim().toUpperCase();

export const toTitleCase = (value) => (
  String(value)
    .toLowerCase()
    .split(/[\s_-]+/)
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ")
);

export const formatAnalyticsDate = (value, { includeTime = false } = {}) => {
  if (!value) return "-";

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);

  return includeTime
    ? parsed.toLocaleString([], { dateStyle: "medium", timeStyle: "short" })
    : parsed.toLocaleDateString();
};

export const getAnalyticsItemRawValues = (item) => {
  if (Array.isArray(item?.rawValues) && item.rawValues.length > 0) {
    return item.rawValues.filter((value) => String(value ?? "").trim());
  }
  const fallback = String(item?.rawName ?? item?.name ?? "").trim();
  return fallback ? [fallback] : [];
};

export const buildAnalyticsDrilldownKey = ({ section, dimension, value = null, values = null }) => {
  const normalizedValues = Array.isArray(values) && values.length > 0
    ? values
    : value != null && String(value).trim()
      ? [value]
      : [];
  return [section, dimension, normalizedValues.join("|")].join("::");
};

export const mergeAnalyticsSeries = (items) => {
  const merged = new Map();

  (Array.isArray(items) ? items : []).forEach((item) => {
    const label = String(item.tooltipLabel || item.name || "").trim();
    const key = normalizeMasterCode(label || item.name);
    if (!key) return;

    if (!merged.has(key)) {
      merged.set(key, {
        ...item,
        rawValues: [...getAnalyticsItemRawValues(item)],
      });
      return;
    }

    const existing = merged.get(key);
    const nextRawValues = new Set([...existing.rawValues, ...getAnalyticsItemRawValues(item)]);
    merged.set(key, {
      ...existing,
      value: Number(existing.value || 0) + Number(item.value || 0),
      rawValues: [...nextRawValues],
    });
  });

  return [...merged.values()].sort((left, right) => {
    const valueDiff = Number(right.value || 0) - Number(left.value || 0);
    if (valueDiff !== 0) return valueDiff;
    return String(left.name || "").localeCompare(String(right.name || ""));
  });
};

export const buildMasterNameMap = (records) => new Map(
  (Array.isArray(records) ? records : [])
    .map((record) => {
      const code = normalizeMasterCode(record?.code);
      const name = String(record?.name ?? "").trim();
      return code && name ? [code, name] : null;
    })
    .filter(Boolean)
);

export const formatAnalyticsCategoryLabel = (value, { emptyLabel = "Unknown", nameMap = null } = {}) => {
  const rawValue = String(value ?? "").trim();

  if (!rawValue) return emptyLabel;
  if (/^unassigned$/i.test(rawValue)) return "Unassigned";

  const mappedName = nameMap?.get(normalizeMasterCode(rawValue));
  if (mappedName) return mappedName;

  if (/^L\d+$/i.test(rawValue)) return `Level ${rawValue.slice(1)}`;
  if (rawValue.includes("_")) return toTitleCase(rawValue);
  if (rawValue === rawValue.toUpperCase() && rawValue.length > 4) return toTitleCase(rawValue);

  return rawValue;
};

export const getCompactDepartmentLabel = (label) => {
  const normalized = normalizeMasterCode(label);

  if (normalized === "FINANCE DEPARTMENT") return "Finance";
  if (normalized === "GENERAL ADMINISTRATION") return "Administration";
  if (normalized === "HUMAN RESOURCES") return "HR";
  if (normalized === "INFORMATION TECHNOLOGY") return "IT";
  if (normalized === "LEGAL AFFAIRS") return "Legal";
  if (normalized.endsWith(" DEPARTMENT")) return label.replace(/\s+Department$/i, "");

  return label;
};

export const getCompactDesignationLabel = (label) => {
  const normalized = normalizeMasterCode(label);

  if (normalized === "ASSISTANT SECTION OFFICER") return "Asst. Sec. Officer";
  if (normalized === "SENIOR ANALYST") return "Sr. Analyst";

  return label;
};

export const buildServiceEventTypeNameMap = (records) => new Map(
  (Array.isArray(records) ? records : [])
    .map((record) => {
      const eventCode = normalizeMasterCode(record?.event_code || record?.code);
      const label = String(record?.name || record?.description || record?.event_code || record?.code || "").trim();
      return eventCode && label ? [eventCode, label] : null;
    })
    .filter(Boolean)
);

export const buildLeaveTypeNameMap = (records) => new Map(
  (Array.isArray(records) ? records : [])
    .map((record) => {
      const leaveCode = normalizeMasterCode(record?.leave_code || record?.code);
      const label = String(record?.description || record?.name || record?.leave_code || record?.code || "").trim();
      return leaveCode && label ? [leaveCode, label] : null;
    })
    .filter(Boolean)
);

export const formatServiceEventTypeLabel = (value, eventTypeNameMap) => {
  const rawValue = String(value ?? "").trim();
  if (!rawValue) return "Unknown";

  const mappedName = eventTypeNameMap?.get(normalizeMasterCode(rawValue));
  if (mappedName) return mappedName;

  return toTitleCase(rawValue);
};

export const formatLeaveTypeLabel = (value, leaveTypeNameMap) => {
  const rawValue = String(value ?? "").trim();
  if (!rawValue) return "Unknown";

  const mappedName = leaveTypeNameMap?.get(normalizeMasterCode(rawValue));
  if (mappedName) return mappedName;

  return toTitleCase(rawValue);
};

export const formatLeaveStatusLabel = (value) => {
  const rawValue = String(value ?? "").trim();
  if (!rawValue) return "Unknown";

  return LEAVE_STATUS_LABELS[normalizeMasterCode(rawValue)] || toTitleCase(rawValue);
};

export const formatGenderAnalyticsLabel = (value) => {
  const rawValue = String(value ?? "").trim();
  if (!rawValue) return "Not specified";

  const normalized = normalizeMasterCode(rawValue);
  if (normalized === "MALE") return "Male";
  if (normalized === "FEMALE") return "Female";
  if (normalized === "OTHER") return "Other";

  return formatAnalyticsCategoryLabel(rawValue, { emptyLabel: "Not specified" });
};

export const formatWorkflowStageLabel = (value) => {
  const rawValue = String(value ?? "").trim();
  if (!rawValue) return "Unknown";
  return WORKFLOW_STAGE_LABELS[normalizeMasterCode(rawValue)] || toTitleCase(rawValue);
};

export const formatWorkflowStageSeries = (items) => (
  (Array.isArray(items) ? items : []).map((entry) => {
    const fullLabel = formatWorkflowStageLabel(entry.name);
    return {
      ...entry,
      rawName: entry.name,
      rawValues: [entry.name],
      name: fullLabel,
      tooltipLabel: fullLabel,
    };
  })
);

export const sortWorkflowStageSeries = (items) => {
  const getStageIndex = (value) => {
    const index = WORKFLOW_STAGE_ORDER.indexOf(normalizeMasterCode(value));
    return index === -1 ? WORKFLOW_STAGE_ORDER.length : index;
  };

  return [...(Array.isArray(items) ? items : [])].sort((left, right) => {
    const indexDiff = getStageIndex(left.rawName || left.name) - getStageIndex(right.rawName || right.name);
    if (indexDiff !== 0) return indexDiff;
    return String(left.name).localeCompare(String(right.name));
  });
};

export const formatWorkforceAnalytics = (data, departmentNameMap, designationNameMap) => {
  if (!data) return null;

  const mapSeries = (items, options = {}) => (
    (Array.isArray(items) ? items : []).map((entry) => {
      const rawValue = String(entry.name ?? "").trim();
      const fullLabel = options.formatLabel
        ? options.formatLabel(rawValue)
        : formatAnalyticsCategoryLabel(rawValue, options);
      return {
        ...entry,
        rawName: rawValue,
        rawValues: rawValue ? [rawValue] : [],
        name: options.compactLabel ? options.compactLabel(fullLabel) : fullLabel,
        tooltipLabel: fullLabel,
      };
    })
  );

  return {
    ...data,
    by_department: mapSeries(data.by_department, {
      emptyLabel: "Unassigned",
      compactLabel: getCompactDepartmentLabel,
      nameMap: departmentNameMap,
    }),
    by_designation: mapSeries(data.by_designation, {
      emptyLabel: "Unassigned",
      compactLabel: getCompactDesignationLabel,
      nameMap: designationNameMap,
    }),
    by_employment_type: mergeAnalyticsSeries(mapSeries(data.by_employment_type)),
    by_status: mergeAnalyticsSeries(mapSeries(data.by_status)),
    by_gender: mergeAnalyticsSeries(mapSeries(data.by_gender, {
      emptyLabel: "Not specified",
      formatLabel: formatGenderAnalyticsLabel,
    })),
  };
};

export const formatServiceEventsAnalytics = (data, eventTypeNameMap) => {
  if (!data) return null;

  return {
    ...data,
    by_type: (Array.isArray(data.by_type) ? data.by_type : []).map((entry) => {
      const fullLabel = formatServiceEventTypeLabel(entry.name, eventTypeNameMap);
      return {
        ...entry,
        rawName: entry.name,
        rawValues: entry.name ? [entry.name] : [],
        name: fullLabel,
        tooltipLabel: fullLabel,
      };
    }),
    monthly_trend: (Array.isArray(data.monthly_trend) ? data.monthly_trend : []).map((entry) => ({
      ...entry,
      monthKey: entry.month_key || null,
      tooltipLabel: entry.month,
    })),
    recent_events: (Array.isArray(data.recent_events) ? data.recent_events : []).map((entry) => ({
      ...entry,
      raw_event_type: entry.event_type,
      event_type_label: formatServiceEventTypeLabel(entry.event_type, eventTypeNameMap),
    })),
  };
};

export const formatLeaveAnalytics = (data, leaveTypeNameMap) => {
  if (!data) return null;

  return {
    ...data,
    by_type: (Array.isArray(data.by_type) ? data.by_type : []).map((entry) => {
      const fullLabel = formatLeaveTypeLabel(entry.name, leaveTypeNameMap);
      return {
        ...entry,
        rawName: entry.name,
        rawValues: entry.name ? [entry.name] : [],
        name: fullLabel,
        tooltipLabel: fullLabel,
      };
    }),
    by_status: (Array.isArray(data.by_status) ? data.by_status : []).map((entry) => {
      const fullLabel = formatLeaveStatusLabel(entry.name);
      return {
        ...entry,
        rawName: entry.name,
        rawValues: entry.name ? [entry.name] : [],
        name: fullLabel,
        tooltipLabel: fullLabel,
      };
    }),
    monthly_trend: (Array.isArray(data.monthly_trend) ? data.monthly_trend : []).map((entry) => ({
      ...entry,
      monthKey: entry.month_key || null,
      tooltipLabel: entry.month,
    })),
    avg_duration_by_type: (Array.isArray(data.avg_duration_by_type) ? data.avg_duration_by_type : []).map((entry) => ({
      ...entry,
      rawType: entry.type,
      type: formatLeaveTypeLabel(entry.type, leaveTypeNameMap),
    })),
  };
};

export const wrapChartTick = (value, maxLength = CHART_AXIS_LABEL_LIMIT, maxLines = 2) => {
  const label = String(value ?? "").trim();
  if (!label) return [""];

  const words = label.split(/\s+/).filter(Boolean);
  const lines = [];
  let currentLine = "";

  words.forEach((word) => {
    const nextLine = currentLine ? `${currentLine} ${word}` : word;
    if (nextLine.length <= maxLength || !currentLine) {
      currentLine = nextLine;
      return;
    }

    lines.push(currentLine);
    currentLine = word;
  });

  if (currentLine) lines.push(currentLine);

  if (lines.length <= maxLines) return lines;

  const visibleLines = lines.slice(0, maxLines);
  const overflow = visibleLines[maxLines - 1];
  visibleLines[maxLines - 1] = `${overflow.slice(0, Math.max(maxLength - 3, 1)).trimEnd()}...`;
  return visibleLines;
};

