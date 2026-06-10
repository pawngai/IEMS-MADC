export function normalizeApiError(error, fallback = "Request failed") {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) return detail;
  if (detail?.message) return detail.message;
  if (error?.message) return error.message;
  return fallback;
}
