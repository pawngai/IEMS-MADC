import React from "react";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

import DeptDirectoryPage from "@/modules/organization_master/pages/DeptDirectoryPage";

const mockNavigate = vi.fn();

vi.mock("react-router-dom", () => ({
  __esModule: true,
  useNavigate: () => mockNavigate,
  useLocation: () => ({
    pathname: "/department-portal/directory",
    search: "",
  }),
}));

vi.mock("@/app/layout/Layout", () => ({
  __esModule: true,
  default: ({ children }) => <div data-testid="layout">{children}</div>,
}));

vi.mock("@/modules/organization_master/hooks/useDepartmentScope", () => ({
  __esModule: true,
  useDepartmentScope: () => ({
    selectedDepartment: "FIN",
    selectedDepartmentLabel: "Finance Department",
    scopeError: "",
    canUseDepartmentPortal: true,
    canCreateProfile: true,
  }),
}));

vi.mock("@/modules/organization_master/hooks/useDepartmentEmployeeDirectory", () => ({
  __esModule: true,
  useDepartmentEmployeeDirectory: () => ({
    employees: [
      {
        employee_id: "EMP-101",
        employee_code: "E-101",
        full_name: "Finance Clerk",
        current_designation_id: "Clerk",
        current_office_id: "HQ",
        employment_type: "REGULAR",
        employee_status: "ACTIVE",
        workflow_status: "LOCKED",
        has_login_account: false,
      },
    ],
    total: 1,
    totalPages: 1,
    currentPage: 1,
    showingFrom: 1,
    showingTo: 1,
    PAGE_SIZE: 20,
    loading: false,
    refreshing: false,
    query: "",
    setQuery: vi.fn(),
    activeStatusFilter: "ALL",
    setActiveStatusFilter: vi.fn(),
    typeFilter: "ALL",
    setTypeFilter: vi.fn(),
    designationFilter: "ALL",
    setDesignationFilter: vi.fn(),
    officeFilter: "ALL",
    setOfficeFilter: vi.fn(),
    employeeStatusFilter: "ALL",
    setEmployeeStatusFilter: vi.fn(),
    recruitmentFilter: "ALL",
    setRecruitmentFilter: vi.fn(),
    payLevelFilter: "ALL",
    setPayLevelFilter: vi.fn(),
    serviceFilter: "ALL",
    setServiceFilter: vi.fn(),
    groupFilter: "ALL",
    setGroupFilter: vi.fn(),
    dateFromFilter: "",
    setDateFromFilter: vi.fn(),
    dateToFilter: "",
    setDateToFilter: vi.fn(),
    sortField: "full_name",
    sortDir: "asc",
    toggleSort: vi.fn(),
    page: 1,
    setPage: vi.fn(),
    employmentTypeOptions: [],
    designationOptions: [],
    officeOptions: [],
    employeeStatusOptions: [],
    recruitmentModeOptions: [],
    payLevelOptions: [],
    serviceOptions: [],
    serviceGroupOptions: [],
    statusCounts: { LOCKED: 1 },
    activeFilterCount: 0,
    clearAllFilters: vi.fn(),
    refresh: vi.fn(),
  }),
}));

vi.mock("sonner", () => ({
  __esModule: true,
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe("DeptDirectoryPage", () => {
  test("does not render department-only account or upload actions", async () => {
    const user = userEvent.setup();
    render(<DeptDirectoryPage />);

    // Default view is cards — find the card and open its overflow menu
    const card = await screen.findByTestId("dept-directory-card-EMP-101");
    const menuTrigger = within(card).getByRole("button", { name: "" });
    await user.click(menuTrigger);

    expect(screen.getByText("Open Profile")).toBeInTheDocument();
    expect(screen.queryByTestId("dept-directory-provision-EMP-101")).not.toBeInTheDocument();
    expect(screen.queryByTestId("dept-directory-reset-EMP-101")).not.toBeInTheDocument();
    expect(screen.queryByText("Upload Photo")).not.toBeInTheDocument();
    expect(screen.queryByText("Upload Signature")).not.toBeInTheDocument();
    expect(screen.queryByText("Reset Password")).not.toBeInTheDocument();
  });
});