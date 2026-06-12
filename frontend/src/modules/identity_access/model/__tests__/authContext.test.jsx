import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

const mockGetMe = vi.fn();
const mockGetModuleAccess = vi.fn();
const mockLogin = vi.fn();
const mockLogout = vi.fn();
const mockRefresh = vi.fn();
const mockClearTokens = vi.fn();

vi.mock("@/modules/identity_access/api/authApi", () => ({
  __esModule: true,
  authAPI: {
    getMe: (...args) => mockGetMe(...args),
    getModuleAccess: (...args) => mockGetModuleAccess(...args),
    login: (...args) => mockLogin(...args),
    logout: (...args) => mockLogout(...args),
    refresh: (...args) => mockRefresh(...args),
  },
}));

vi.mock("@/platform/api/httpClient", () => ({
  __esModule: true,
  getToken: () => sessionStorage.getItem("iems_token"),
  getUser: () => {
    try {
      return JSON.parse(sessionStorage.getItem("iems_user") || "null");
    } catch {
      return null;
    }
  },
  setTokens: ({ access_token, user }) => {
    if (access_token) sessionStorage.setItem("iems_token", access_token);
    if (user) sessionStorage.setItem("iems_user", JSON.stringify(user));
  },
  clearTokens: () => {
    mockClearTokens();
    sessionStorage.removeItem("iems_token");
    sessionStorage.removeItem("iems_user");
    sessionStorage.removeItem("iems_active_role");
  },
}));

import { AuthProvider, useAuth } from "@/modules/identity_access/model/authContext";

const AuthStateProbe = () => {
  const { user, loading } = useAuth();
  return <div data-testid="auth-state">{loading ? "loading" : user?.name || "guest"}</div>;
};

describe("AuthProvider", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    window.history.replaceState(null, "", "/");
    mockRefresh.mockRejectedValue(new Error("no refresh session"));
    mockGetModuleAccess.mockResolvedValue({ data: { mode: "allow_all", allowed_modules: null } });
  });

  test("skips bootstrap refresh on the login route", async () => {
    window.history.replaceState(null, "", "/login");

    render(
      <AuthProvider>
        <AuthStateProbe />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("auth-state")).toHaveTextContent("guest");
    });

    expect(mockRefresh).not.toHaveBeenCalled();
    expect(mockClearTokens).toHaveBeenCalledTimes(1);
  });

  test("reuses a single bootstrap refresh request under StrictMode", async () => {
    window.history.replaceState(null, "", "/employees");
    let resolveRefresh;
    const refreshPromise = new Promise((resolve) => {
      resolveRefresh = resolve;
    });
    mockRefresh.mockReturnValue(refreshPromise);
    mockGetMe.mockResolvedValue({
      data: { name: "Priya Nair", authorities: ["GLOBAL_DATA_ENTRY"] },
    });

    render(
      <React.StrictMode>
        <AuthProvider>
          <AuthStateProbe />
        </AuthProvider>
      </React.StrictMode>
    );

    await waitFor(() => {
      expect(mockRefresh).toHaveBeenCalledTimes(1);
    });

    resolveRefresh({
      data: {
        access_token: "fresh-token",
        refresh_token: null,
        user: { name: "Priya Nair", authorities: ["GLOBAL_DATA_ENTRY"] },
      },
    });

    await waitFor(() => {
      expect(screen.getByTestId("auth-state")).toHaveTextContent("Priya Nair");
    });
  });

  test("forces re-login when authorities drift from stored session state", async () => {
    sessionStorage.setItem("iems_token", "stale-token");
    sessionStorage.setItem(
      "iems_user",
      JSON.stringify({ name: "Priya Nair", authorities: ["GLOBAL_DATA_ENTRY"] })
    );

    mockGetMe.mockResolvedValue({
      data: { name: "Priya Nair", authorities: ["GLOBAL_DATA_ENTRY", "VERIFIER"] },
    });

    render(
      <AuthProvider>
        <AuthStateProbe />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(mockClearTokens).toHaveBeenCalledTimes(1);
    });

    expect(screen.getByTestId("auth-state")).toHaveTextContent("guest");
    expect(sessionStorage.getItem("iems_auth_notice")).toBe("Your access changed. Sign in again to continue.");
  });
});
