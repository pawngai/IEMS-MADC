import { API_URL } from "@/platform/api/httpClient";

export const resolveEmployeeProfileMediaUrl = (path) => {
  if (!path) return "";
  if (String(path).startsWith("http")) return path;
  const backendBase = API_URL.replace(/\/api$/, "");
  return `${backendBase}${String(path).startsWith("/") ? "" : "/"}${path}`;
};
