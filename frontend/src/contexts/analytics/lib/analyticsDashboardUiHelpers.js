export const sanitizeAnalyticsFilenameSegment = (value, fallback = "all") => {
  const normalized = String(value ?? "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return normalized || fallback;
};

export const triggerAnalyticsCsvDownload = (blob, filename) => {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
};

export const getAnalyticsDownloadFilename = (headers, fallback = "analytics-drilldown.csv") => {
  const contentDisposition = headers?.["content-disposition"] || headers?.get?.("content-disposition");
  if (!contentDisposition) return fallback;

  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(utf8Match[1]);
    } catch {
      return utf8Match[1];
    }
  }

  const filenameMatch = contentDisposition.match(/filename="?([^";]+)"?/i);
  return filenameMatch?.[1] || fallback;
};

export const buildAnalyticsDrilldownFallbackFilename = (config) => {
  const sectionSegment = sanitizeAnalyticsFilenameSegment(config?.section, "analytics");
  const dimensionSegment = sanitizeAnalyticsFilenameSegment(config?.dimension, "all");
  const valueSegment = sanitizeAnalyticsFilenameSegment(
    config?.label || config?.value || (Array.isArray(config?.values) ? config.values.join("-") : ""),
    "selection",
  );
  return `analytics-${sectionSegment}-${dimensionSegment}-${valueSegment}.csv`;
};

export const buildAnalyticsLocalWorkforceFilename = (config, { hasFilter, hasCustomFields }) => {
  const baseFilename = buildAnalyticsDrilldownFallbackFilename(config).replace(/\.csv$/i, "");
  const suffix = [
    hasFilter ? "filtered" : null,
    hasCustomFields ? "visible-columns" : null,
  ].filter(Boolean).join("-");

  return `${baseFilename}-${suffix || "loaded-rows"}.csv`;
};

export const formatAnalyticsEmployeeReference = (eventRow) => {
  if (eventRow.employee_code) return eventRow.employee_code;
  if (!eventRow.employee_id) return "-";
  return eventRow.employee_id.length > 18
    ? `${eventRow.employee_id.slice(0, 8)}...${eventRow.employee_id.slice(-4)}`
    : eventRow.employee_id;
};

export const getAnalyticsEmployeeDisplay = (eventRow) => {
  const employeeName = String(eventRow.employee_name || "").trim();
  const employeeCode = String(eventRow.employee_code || "").trim();
  const employeeId = String(eventRow.employee_id || "").trim();
  const shortenedId = employeeId
    ? employeeId.length > 18
      ? `${employeeId.slice(0, 8)}...${employeeId.slice(-4)}`
      : employeeId
    : null;

  if (employeeName) {
    return {
      primary: employeeName,
      secondary: employeeCode || shortenedId,
      reference: employeeCode || shortenedId || "-",
    };
  }

  if (employeeCode) {
    return {
      primary: employeeCode,
      secondary: shortenedId && shortenedId !== employeeCode ? shortenedId : null,
      reference: employeeCode,
    };
  }

  if (shortenedId) {
    return {
      primary: "Identity unavailable",
      secondary: shortenedId,
      reference: shortenedId,
    };
  }

  return { primary: "-", secondary: null, reference: "-" };
};