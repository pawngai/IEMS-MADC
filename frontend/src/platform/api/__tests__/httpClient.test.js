/**
 * Token storage helpers + axios instance smoke tests.
 *
 * These validate token helper behavior where access tokens stay in memory,
 * user state is stored in sessionStorage, and refresh tokens live in HttpOnly cookies.
 */

// Minimal sessionStorage polyfill for Node/Jest
const store = {};
const mockStorage = {
  getItem: (k) => store[k] ?? null,
  setItem: (k, v) => {
    store[k] = String(v);
  },
  removeItem: (k) => {
    delete store[k];
  },
  clear: () => Object.keys(store).forEach((k) => delete store[k]),
};
Object.defineProperty(global, "sessionStorage", { value: mockStorage });
Object.defineProperty(global, "localStorage", { value: mockStorage });

// Now import the module under test
const {
  getToken,
  getRefresh,
  getUser,
  setTokens,
  clearTokens,
  resolveBackendBaseUrl,
  API_URL,
} = require("../httpClient");

afterEach(() => {
  clearTokens();
  mockStorage.clear();
});

describe("Token storage helpers", () => {
  test("setTokens keeps access_token in memory and stores user only", () => {
    setTokens({
      access_token: "abc",
      refresh_token: "xyz",
      user: { id: "1", name: "Test" },
    });

    expect(getToken()).toBe("abc");
    expect(getRefresh()).toBeNull();
    expect(getUser()).toEqual({ id: "1", name: "Test" });
    expect(mockStorage.getItem("iems_token")).toBeNull();
  });

  test("clearTokens removes all keys", () => {
    setTokens({ access_token: "abc", refresh_token: "xyz", user: { id: "1" } });
    mockStorage.setItem("iems_active_role", "ADMIN");
    mockStorage.setItem("iems_switch_target", "HOD");

    clearTokens();

    expect(getToken()).toBeNull();
    expect(getRefresh()).toBeNull();
    expect(getUser()).toBeNull();
    expect(mockStorage.getItem("iems_active_role")).toBeNull();
    expect(mockStorage.getItem("iems_switch_target")).toBeNull();
  });

  test("getUser returns null for missing or invalid JSON", () => {
    expect(getUser()).toBeNull();
    mockStorage.setItem("iems_user", "{bad json");
    expect(getUser()).toBeNull();
  });

  test("setTokens is additive - only overwrites provided keys", () => {
    setTokens({ access_token: "first" });
    setTokens({ refresh_token: "second" });

    expect(getToken()).toBe("first");
    expect(getRefresh()).toBeNull();
  });
});

describe("resolveBackendBaseUrl", () => {
  test("keeps runtime localhost aligned when env backend uses 127.0.0.1", () => {
    expect(resolveBackendBaseUrl("localhost", "http://127.0.0.1:8000")).toBe("http://localhost:8000");
  });

  test("keeps runtime 127 aligned when env backend uses localhost", () => {
    expect(resolveBackendBaseUrl("127.0.0.1", "http://localhost:8000")).toBe("http://127.0.0.1:8000");
  });

  test("preserves non-local configured backend urls", () => {
    expect(resolveBackendBaseUrl("localhost", "https://iems.example.gov/api-root")).toBe("https://iems.example.gov/api-root");
  });

  test("falls back to runtime host when env backend is blank", () => {
    expect(resolveBackendBaseUrl("127.0.0.1", "")).toBe("http://127.0.0.1:8000");
  });

  test("preserves same-origin relative api roots", () => {
    expect(resolveBackendBaseUrl("34.67.90.71.sslip.io", "/api")).toBe("/api");
  });
});

describe("API_URL", () => {
  test("does not duplicate /api when configured backend already ends with /api", () => {
    expect(API_URL).toBe("http://localhost:8000/api");
    expect(/\/api\/api$/i.test(API_URL)).toBe(false);
  });
});
