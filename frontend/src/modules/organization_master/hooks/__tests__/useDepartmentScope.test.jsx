import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import { useDepartmentScope } from "@/modules/organization_master/hooks/useDepartmentScope";

const mockUseAuth = vi.fn();
const mockGetDepartments = vi.fn();
const mockGetMe = vi.fn();
const mockSetTokens = vi.fn();

vi.mock("@/modules/identity_access/model/authContext", () => ({
  __esModule: true,
  useAuth: () => mockUseAuth(),
}));

vi.mock("@/modules/organization_master/api/mastersApi", () => ({
  __esModule: true,
  mastersAPI: {
    getDepartments: (...args) => mockGetDepartments(...args),
  },
}));

vi.mock("@/modules/identity_access/api/authApi", () => ({
  __esModule: true,
  authAPI: {
    getMe: (...args) => mockGetMe(...args),
  },
}));

vi.mock("@/platform/api/httpClient", () => ({
  __esModule: true,
  setTokens: (...args) => mockSetTokens(...args),
}));

vi.mock("sonner", () => ({
  __esModule: true,
  toast: {
    error: vi.fn(),
  },
}));

const ScopeProbe = () => {
  const scope = useDepartmentScope();

  return (
    <div>
      <div data-testid="can-use">{String(scope.canUseDepartmentPortal)}</div>
      <div data-testid="is-data-entry">{String(scope.isDataEntry)}</div>
      <div data-testid="can-manage-strength">{String(scope.canManageSanctionedStrength)}</div>
      <div data-testid="selected-department">{scope.selectedDepartment || ""}</div>
      <div data-testid="scope-error">{scope.scopeError || ""}</div>
      <div data-testid="loading">{String(scope.loading)}</div>
    </div>
  );
};

describe("useDepartmentScope", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetDepartments.mockResolvedValue({
      data: [
        { code: "FIN", name: "Finance" },
        { code: "HR", name: "Human Resources" },
      ],
    });
    mockGetMe.mockResolvedValue({ data: {} });
    mockUseAuth.mockReturnValue({
      user: { authorities: ["DEPT_DATA_ENTRY"], department_code: "FIN" },
      can: (permission) => permission === "PROFILE_READ_ALL" || permission === "PROFILE_CREATE",
      canAccessModule: () => true,
    });
  });

  test("allows department-scoped data entry users and resolves their department", async () => {
    render(<ScopeProbe />);

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });

    expect(screen.getByTestId("can-use")).toHaveTextContent("true");
    expect(screen.getByTestId("is-data-entry")).toHaveTextContent("true");
    expect(screen.getByTestId("can-manage-strength")).toHaveTextContent("false");
    expect(screen.getByTestId("selected-department")).toHaveTextContent("FIN");
    expect(screen.getByTestId("scope-error")).toHaveTextContent("");
    expect(mockGetDepartments).toHaveBeenCalledTimes(1);
  });

  test("fails closed for global data entry users", async () => {
    mockUseAuth.mockReturnValue({
      user: { authorities: ["GLOBAL_DATA_ENTRY"], department_code: "FIN" },
      can: (permission) => permission === "PROFILE_READ_ALL",
      canAccessModule: () => true,
    });

    render(<ScopeProbe />);

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });

    expect(screen.getByTestId("can-use")).toHaveTextContent("false");
    expect(screen.getByTestId("is-data-entry")).toHaveTextContent("false");
    expect(screen.getByTestId("can-manage-strength")).toHaveTextContent("false");
    expect(screen.getByTestId("selected-department")).toHaveTextContent("");
    expect(mockGetDepartments).not.toHaveBeenCalled();
    expect(mockGetMe).not.toHaveBeenCalled();
  });
});