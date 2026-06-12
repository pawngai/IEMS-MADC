const RUNTIME_HOST = typeof window !== "undefined" ? window.location.hostname : "localhost";
const ENV_BACKEND = process.env.REACT_APP_BACKEND_URL || "";
const IS_RUNTIME_LOCALHOST = RUNTIME_HOST === "localhost" || RUNTIME_HOST === "127.0.0.1";

let envBackendHost = "";
if (ENV_BACKEND) {
  try {
    envBackendHost = new URL(ENV_BACKEND).hostname;
  } catch {
    envBackendHost = "";
  }
}

const IS_ENV_LOCALHOST = envBackendHost === "localhost" || envBackendHost === "127.0.0.1";
const BACKEND =
  ENV_BACKEND && !(IS_ENV_LOCALHOST && !IS_RUNTIME_LOCALHOST)
    ? ENV_BACKEND
    : `http://${RUNTIME_HOST}:8000`;

export function resolveUrl(pathOrUrl) {
  if (!pathOrUrl) return null;
  if (pathOrUrl.startsWith("http")) return pathOrUrl;
  return `${BACKEND}${pathOrUrl.startsWith("/") ? "" : "/"}${pathOrUrl}`;
}

export function fmt(val) {
  if (val === null || val === undefined || val === "") return "-";
  return String(val);
}

export function fmtDate(val) {
  if (!val) return "-";
  const d = new Date(val);
  if (Number.isNaN(d.getTime())) return val;
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

export function money(val) {
  if (val === null || val === undefined) return "-";
  return `Rs. ${Number(val).toLocaleString("en-IN")}`;
}

export function yesNo(val) {
  return val ? "Yes" : "No";
}

export function listToString(arr) {
  if (!Array.isArray(arr) || arr.length === 0) return "-";
  return arr
    .map((item) => {
      if (typeof item === "string") return item;
      if (item?.description) return item.description;
      const parts = [item?.degree, item?.subject, item?.year, item?.university, item?.institute]
        .filter(Boolean)
        .join(", ");
      return parts || JSON.stringify(item);
    })
    .join("; ");
}

export function addressStr(addr) {
  if (!addr) return "-";
  return [addr.line1, addr.line2, addr.city, addr.state, addr.pin, addr.country]
    .filter(Boolean)
    .join(", ") || "-";
}
