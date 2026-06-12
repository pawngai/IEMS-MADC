import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

const mockNavigate = vi.fn();
const mockGetDashboard = vi.fn();
const mockGetPendingWork = vi.fn();
const mockGetBulkCompletion = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("@/app/layout/Layout", () => ({
  __esModule: true,
  default: ({ children }) => <div data-testid="layout-shell">{children}</div>,
}));

vi.mock("@/modules/organization_master/api/departmentApi", () => ({
  __esModule: true,
  departmentPortalAPI: {
    getDashboard: (...args) => mockGetDashboard(...args),
    getPendingWork: (...args) => mockGetPendingWork(...args),
  },
}));

vi.mock("@/modules/organization_master/hooks/useDepartmentScope", () => ({
  __esModule: true,
  useDepartmentScope: () => ({
    loading: false,
    setLoading: vi.fn(),
    selectedDepartment: "MADC-HR",
    selectedDepartmentLabel: "MADC HR",
    scopeError: "",
    canUseDepartmentPortal: true,
    canLeaveWorkflow: true,
    canCreateProfile: true,
  }),
}));

vi.mock("@/modules/organization_master/model/departmentProfileGateway", () => ({
  __esModule: true,
  getDepartmentBulkProfileCompletion: (...args) => mockGetBulkCompletion(...args),
}));

vi.mock("sonner", () => ({
  __esModule: true,
  toast: {
    error: vi.fn(),
  },
}));

import DeptDashboard from "@/modules/organization_master/pages/DeptDashboardPage";

describe("DeptDashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetDashboard.mockResolvedValue({
      data: {
        total_employees: 3,
        locked_profiles: 2,
        regular_employees: 2,
        pending_leave_actions: 1,
        sanctioned_strength_configured: true,
        sanctioned_strength_total: 8,
        filled_strength_total: 6,
        vacancy_count: 2,
        over_strength_count: 0,
      },
    });
    mockGetPendingWork.mockResolvedValue({ data: { items: [{ employee_id: "EMP-1" }], total: 1 } });
    mockGetBulkCompletion.mockResolvedValue(null);
  });

  test("renders summary from dashboard aggregates instead of employee list rows", async () => {
    render(<DeptDashboard />);

    await waitFor(() => {
      expect(mockGetDashboard).toHaveBeenCalledTimes(1);
    });

    expect(screen.getByText("67% completion")).toBeInTheDocument();
    expect(screen.getByText("1 profile(s) not yet locked.")).toBeInTheDocument();
    expect(screen.getByText("2 regular")).toBeInTheDocument();
    expect(screen.getByText("2 vacant")).toBeInTheDocument();
    expect(screen.getByText("Sanctioned Posts")).toBeInTheDocument();
    expect(screen.getByText("Filled Posts")).toBeInTheDocument();
    expect(screen.getByText("Vacancies")).toBeInTheDocument();
    expect(screen.getByText("Occupancy")).toBeInTheDocument();
    expect(screen.queryByText("Change Requests")).not.toBeInTheDocument();
  });

  test("strength metrics drill down to sanctioned strength", async () => {
    render(<DeptDashboard />);

    await waitFor(() => {
      expect(mockGetDashboard).toHaveBeenCalledTimes(1);
    });

    fireEvent.click(screen.getByText("Vacancies"));

    expect(mockNavigate).toHaveBeenCalledWith("/department-portal/sanctioned-strength");
  });
});