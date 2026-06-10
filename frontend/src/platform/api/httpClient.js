import axios from "axios";

const LOCAL_DEV_HOSTS = new Set(["localhost", "127.0.0.1"]);

function getRuntimeHost() {
  return typeof window !== "undefined" ? window.location.hostname : "localhost";
}

function redirectToLogin() {
  if (typeof window === "undefined") return;
  if (process.env.NODE_ENV === "test") {
    window.history.replaceState(null, "", "/login");
    return;
  }
  window.location.href = "/login";
}

export function resolveBackendBaseUrl(runtimeHost = getRuntimeHost(), envBackendUrl = process.env.REACT_APP_BACKEND_URL || "") {
  const fallbackBackendUrl = `http://${runtimeHost}:8000`;
  if (!envBackendUrl) return fallbackBackendUrl;

  if (envBackendUrl.startsWith("/")) {
    return envBackendUrl.replace(/\/$/, "");
  }

  try {
    const configuredUrl = new URL(envBackendUrl);
    const isRuntimeLocal = LOCAL_DEV_HOSTS.has(runtimeHost);
    const isConfiguredLocal = LOCAL_DEV_HOSTS.has(configuredUrl.hostname);

    if (isRuntimeLocal && isConfiguredLocal && configuredUrl.hostname !== runtimeHost) {
      configuredUrl.hostname = runtimeHost;
      return configuredUrl.toString().replace(/\/$/, "");
    }

    return envBackendUrl.replace(/\/$/, "");
  } catch {
    return fallbackBackendUrl;
  }
}

const NORMALIZED_BACKEND_URL = resolveBackendBaseUrl();
export const API_URL = /\/api$/i.test(NORMALIZED_BACKEND_URL)
  ? NORMALIZED_BACKEND_URL
  : `${NORMALIZED_BACKEND_URL}/api`;

const _store = typeof sessionStorage !== "undefined" ? sessionStorage : localStorage;
let accessToken = _store.getItem("iems_token") || null;
_store.removeItem("iems_token");

export function getToken() { return accessToken; }
export function getRefresh() { return null; }
export function getUser() {
  try { return JSON.parse(_store.getItem("iems_user")); } catch { return null; }
}
export function setTokens({ access_token, refresh_token, user }) {
  if (access_token) {
    accessToken = access_token;
    _store.removeItem("iems_token");
  }
  if (refresh_token) {
    // Refresh token is transported via HttpOnly cookie and must not be persisted in Web Storage.
    _store.removeItem("iems_refresh_token");
  }
  if (user) _store.setItem("iems_user", JSON.stringify(user));
}
export function clearTokens() {
  accessToken = null;
  _store.removeItem("iems_token");
  _store.removeItem("iems_refresh_token");
  _store.removeItem("iems_user");
  _store.removeItem("iems_active_role");
  _store.removeItem("iems_switch_target");
}

export const apiClient = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  const activeRole = _store.getItem("iems_active_role");
  if (activeRole) {
    config.headers["X-IEMS-Active-Role"] = activeRole;
  }
  return config;
});

let isRefreshing = false;
let refreshSubscribers = [];

function onRefreshed(newToken) {
  refreshSubscribers.forEach(({ resolve }) => resolve(newToken));
  refreshSubscribers = [];
}

function onRefreshFailed(error) {
  refreshSubscribers.forEach(({ reject }) => reject(error));
  refreshSubscribers = [];
}

function addRefreshSubscriber(resolve, reject) {
  refreshSubscribers.push({ resolve, reject });
}

const MAX_RETRIES = 2;
const RETRYABLE_METHODS = new Set(["get", "head", "options"]);

function parseValidationDetailItem(item) {
  if (!item) return "";
  if (typeof item === "string") return item;
  if (typeof item.msg === "string" && item.msg.trim()) return item.msg;
  try {
    return JSON.stringify(item);
  } catch {
    return String(item);
  }
}

function normalizeErrorDetail(error) {
  const responseData = error?.response?.data;
  if (!responseData || !Object.prototype.hasOwnProperty.call(responseData, "detail")) return;

  const detail = responseData.detail;
  if (typeof detail === "string") return;

  if (Array.isArray(detail)) {
    const messages = detail
      .map(parseValidationDetailItem)
      .filter((msg) => typeof msg === "string" && msg.trim().length > 0);
    responseData.detail = messages.length > 0 ? messages.join("; ") : "Request validation failed";
    return;
  }

  if (detail && typeof detail === "object") {
    const shouldPreserveStructuredDetail =
      Object.prototype.hasOwnProperty.call(detail, "error_code") ||
      Object.prototype.hasOwnProperty.call(detail, "errors") ||
      Object.prototype.hasOwnProperty.call(detail, "missing_fields_by_part");
    if (shouldPreserveStructuredDetail) {
      return;
    }

    if (typeof detail.message === "string" && detail.message.trim()) {
      responseData.detail = detail.message;
      return;
    }
    responseData.detail = parseValidationDetailItem(detail) || "Request failed";
    return;
  }

  responseData.detail = String(detail || "Request failed");
}

function shouldRetry(error) {
  if (!error.config) return false;
  if (error.config.iemsNoRetry) return false;
  const method = (error.config.method || "").toLowerCase();
  if (!RETRYABLE_METHODS.has(method)) return false;
  if (!error.response) return true;
  return error.response.status >= 500;
}

async function retryRequest(error) {
  const config = error.config;
  config.__retryCount = (config.__retryCount || 0) + 1;
  if (config.__retryCount > MAX_RETRIES) return Promise.reject(error);
  const delay = config.__retryCount * 500 + Math.random() * 500;
  await new Promise((r) => setTimeout(r, delay));
  return apiClient(config);
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    normalizeErrorDetail(error);
    const originalRequest = error.config;

    if (shouldRetry(error) && (originalRequest.__retryCount || 0) < MAX_RETRIES) {
      return retryRequest(error);
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (originalRequest.url?.includes("/auth/login")) {
        return Promise.reject(error);
      }
      if (originalRequest.url?.includes("/auth/refresh")) {
        clearTokens();
        redirectToLogin();
        return Promise.reject(error);
      }

      originalRequest._retry = true;

      if (!isRefreshing) {
        isRefreshing = true;

        try {
          const res = await axios.post(`${API_URL}/auth/refresh`, {}, { withCredentials: true });
          const { access_token, refresh_token: newRefresh, user } = res.data;
          setTokens({ access_token, refresh_token: newRefresh, user });
          isRefreshing = false;
          onRefreshed(access_token);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return apiClient(originalRequest);
        } catch {
          isRefreshing = false;
          onRefreshFailed(error);
          clearTokens();
          redirectToLogin();
          return Promise.reject(error);
        }
      }

      return new Promise((resolve, reject) => {
        addRefreshSubscriber(
          (newToken) => {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            resolve(apiClient(originalRequest));
          },
          reject
        );
      });
    }

    return Promise.reject(error);
  }
);

export default apiClient;
