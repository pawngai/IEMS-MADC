import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import EmployeeDirectoryPage from "@/contexts/employee_identity/pages/EmployeeDirectoryPage";

const mockNavigate = jest.fn();
const mockCan = jest.fn();
const mockCanAny = jest.fn();
const mockCanAccessModule = jest.fn();
const mockGetPrimaryAuthority = jest.fn();
const mockIsAny = jest.fn();
const mockRefresh = jest.fn();
const mockProvisionEmployeeAccount = jest.fn();
const mockGetEmployees = jest.fn();
const mockUseEmployeeDirectory = jest.fn();

let mockPathname = "/employees";

const mockDepartmentOptions = [{ value: "FIN", label: "Finance Department" }];
const mockDesignationOptions = [{ value: "ASO", label: "Assistant Section Officer" }];
const mockOfficeOptions = [{ value: "HQ", label: "Headquarters" }];
const mockEmploymentTypeOptions = [{ value: "REGULAR", label: "Regular" }];
const mockEmployeeStatusOptions = [{ value: "ACTIVE", label: "ACTIVE" }];

jest.mock("react-router-dom", () => ({
  __esModule: true,
  useNavigate: () => mockNavigate,
  useLocation: () => ({ pathname: mockPathname, search: "" }),
}));

jest.mock("@/app/layout/Layout", () => ({
  __esModule: true,
  default: ({ children }) => <div data-testid="layout">{children}</div>,
}));

const mockEmployees = [
  {
    employee_id: "EMP-200",
    employee_code: "E-200",
    full_name: "Sample Employee",
    current_designation_id: "ASO",
    employment_type: "REGULAR",
    employee_status: "ACTIVE",
    identity_workflow_status: "SUBMITTED",
    workflow_status: "DRAFT",
    current_department_id: "FIN",
    current_office_id: "HQ",
    email_official: "sample.employee@madc.gov.in",
    has_login_account: false,
  },
];

jest.mock("@/contexts/employee_identity/hooks/useEmployeeDirectory", () => ({
  __esModule: true,
  useEmployeeDirectory: (...args) => {
    mockUseEmployeeDirectory(...args);
    return ({
    employees: mockEmployees,
    total: mockEmployees.length,
    totalPages: 1,
    currentPage: 1,
    showingFrom: 1,
    showingTo: mockEmployees.length,
    PAGE_SIZE: 20,
    loading: false,
    refreshing: false,
    query: "",
    setQuery: jest.fn(),
    activeStatusFilter: "ALL",
    setActiveStatusFilter: jest.fn(),
    departmentFilter: "ALL",
    setDepartmentFilter: jest.fn(),
    typeFilter: "ALL",
    setTypeFilter: jest.fn(),
    designationFilter: "ALL",
    setDesignationFilter: jest.fn(),
    officeFilter: "ALL",
    setOfficeFilter: jest.fn(),
    employeeStatusFilter: "ALL",
    setEmployeeStatusFilter: jest.fn(),
    recruitmentFilter: "ALL",
    setRecruitmentFilter: jest.fn(),
    payLevelFilter: "ALL",
    setPayLevelFilter: jest.fn(),
    serviceFilter: "ALL",
    setServiceFilter: jest.fn(),
    groupFilter: "ALL",
    setGroupFilter: jest.fn(),
    dateFromFilter: "",
    setDateFromFilter: jest.fn(),
    dateToFilter: "",
    setDateToFilter: jest.fn(),
    activeFilterCount: 0,
    clearAllFilters: jest.fn(),
    statusCounts: { DRAFT: 1 },
    departmentOptions: mockDepartmentOptions,
    employmentTypeOptions: mockEmploymentTypeOptions,
    designationOptions: mockDesignationOptions,
    officeOptions: mockOfficeOptions,
    employeeStatusOptions: mockEmployeeStatusOptions,
    recruitmentModeOptions: [],
    payLevelOptions: [],
    serviceOptions: [],
    serviceGroupOptions: [],
    sortField: "full_name",
    sortDir: "asc",
    toggleSort: jest.fn(),
    page: 1,
    setPage: jest.fn(),
    refresh: mockRefresh,
    loadEmployees: jest.fn(),
    workflowFilterKind: "Profile",
    });
  },
}));

jest.mock("@/contexts/employee_identity/api/employeeIdentityApi", () => ({
  __esModule: true,
  employeeIdentityApi: {
    list: jest.fn(),
  },
}));

jest.mock("@/contexts/identity/api/userManagementApi", () => ({
  __esModule: true,
  userManagementAPI: {
    getEmployees: (...args) => mockGetEmployees(...args),
    provisionEmployeeAccount: (...args) => mockProvisionEmployeeAccount(...args),
  },
}));

jest.mock("@/contexts/identity/model/authContext", () => ({
  __esModule: true,
  useAuth: () => ({
    can: mockCan,
    canAny: mockCanAny,
    canAccessModule: mockCanAccessModule,
    getPrimaryAuthority: mockGetPrimaryAuthority,
    isAny: mockIsAny,
  }),
}));

jest.mock("sonner", () => ({
  __esModule: true,
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

describe("EmployeeDirectoryPage directory navigation", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPathname = "/employees";
    mockEmployees[0].full_name = "Sample Employee";
    mockEmployees[0].current_designation_id = "ASO";
    mockEmployees[0].identity_workflow_status = "SUBMITTED";
    mockEmployees[0].employee_status = "ACTIVE";
    mockEmployees[0].workflow_status = "DRAFT";
    mockEmployees[0].profile_workflow_status = "DRAFT";
    mockEmployees[0].email_official = "sample.employee@madc.gov.in";
    mockEmployees[0].has_login_account = false;
    delete mockEmployees[0].account_email;

    mockCanAny.mockReturnValue(true);
    mockCan.mockImplementation((permission) => permission === "SERVICE_BOOK_READ_ALL");
    mockCanAccessModule.mockImplementation((moduleId) => ["data_entry", "service_book"].includes(moduleId));
    mockGetPrimaryAuthority.mockReturnValue("DEPT_DATA_ENTRY");
    mockIsAny.mockReturnValue(false);
    mockGetEmployees.mockResolvedValue({ data: { employees: [] } });
    mockProvisionEmployeeAccount.mockResolvedValue({
      data: {
        already_exists: false,
        temp_password: "Tmp@ABCD1234",
      },
    });
  });

  test("clicking an employee row navigates to employee profile", async () => {
    render(<EmployeeDirectoryPage />);

    const row = await screen.findByTestId("employees-row-EMP-200");
    fireEvent.click(row);

    expect(mockNavigate).toHaveBeenCalledWith("/employees/EMP-200");
  });

  test("clicking an employee row in portal navigates to portal profile", async () => {
    mockPathname = "/portal/employees";

    render(<EmployeeDirectoryPage />);

    const row = await screen.findByTestId("employees-row-EMP-200");
    fireEvent.click(row);

    expect(mockNavigate).toHaveBeenCalledWith("/portal/employees/EMP-200");
  });

  test("renders readable labels instead of raw directory codes", async () => {
    render(<EmployeeDirectoryPage />);

    expect(await screen.findByText("Assistant Section Officer")).toBeInTheDocument();
    expect(screen.getByText("Finance Department")).toBeInTheDocument();
    expect(screen.getByText("Headquarters")).toBeInTheDocument();
    expect(screen.getByText("Regular")).toBeInTheDocument();
    expect(screen.getByText("Pending")).toBeInTheDocument();
    expect(screen.getByText("Submitted")).toBeInTheDocument();
    expect(screen.getByText("Draft")).toBeInTheDocument();
  });

  test("shows identity status as pending until identity workflow is active", async () => {
    mockEmployees[0].employee_status = "ACTIVE";
    mockEmployees[0].identity_workflow_status = "VERIFIED";

    render(<EmployeeDirectoryPage />);

    expect(await screen.findByText("Pending")).toBeInTheDocument();
    expect(screen.queryByText("Active")).not.toBeInTheDocument();
  });

  test("shows identity status as active after approval activates the identity", async () => {
    mockEmployees[0].employee_status = "ACTIVE";
    mockEmployees[0].identity_workflow_status = "ACTIVE";

    render(<EmployeeDirectoryPage />);

    expect(await screen.findAllByText("Active")).toHaveLength(2);
    expect(screen.queryByText("Pending")).not.toBeInTheDocument();
  });

  test("renders readable workflow labels in the directory status filter pills", async () => {
    render(<EmployeeDirectoryPage />);

    expect(await screen.findByRole("button", { name: "All (1)" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Draft (1)" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "DRAFT (1)" })).not.toBeInTheDocument();
  });

  test("preserves full cell values via title attributes for truncated directory columns", async () => {
    render(<EmployeeDirectoryPage />);

    expect(await screen.findByTitle("Sample Employee")).toBeInTheDocument();
    expect(screen.getByTitle("Assistant Section Officer")).toBeInTheDocument();
    expect(screen.getByTitle("Finance Department")).toBeInTheDocument();
    expect(screen.getByTitle("Headquarters")).toBeInTheDocument();
  });

  test("renders accessible search and status filter controls", async () => {
    render(<EmployeeDirectoryPage />);

    expect(
      await screen.findByRole("textbox", { name: "Search employees by name, code, department, or designation" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Profile workflow status filters" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "All (1)" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "Draft (1)" })).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByRole("button", { name: "Choose visible columns (9 of 17 shown)" })).toBeInTheDocument();
  });

  test("uses identity directory source for global data entry so all identities remain visible", async () => {
    mockGetPrimaryAuthority.mockReturnValue("GLOBAL_DATA_ENTRY");
    mockIsAny.mockImplementation((authorities) => authorities.includes("GLOBAL_DATA_ENTRY"));

    render(<EmployeeDirectoryPage />);

    await screen.findByTestId("employees-row-EMP-200");
    expect(mockUseEmployeeDirectory).toHaveBeenCalledWith(expect.objectContaining({
      useIdentityDirectory: true,
      useUserDirectory: false,
    }));
  });

  test("keeps directory available for global data entry even when module access payload is missing", async () => {
    mockCanAccessModule.mockReturnValue(false);
    mockGetPrimaryAuthority.mockReturnValue("GLOBAL_DATA_ENTRY");
    mockIsAny.mockImplementation((authorities) => authorities.includes("GLOBAL_DATA_ENTRY"));

    render(<EmployeeDirectoryPage />);

    expect(await screen.findByTestId("employees-page")).toBeInTheDocument();
    expect(screen.queryByTestId("employees-denied")).not.toBeInTheDocument();
  });

  test("shows global create actions when module access payload is missing but profile create is allowed", async () => {
    mockCan.mockImplementation((permission) => permission === "PROFILE_CREATE");
    mockCanAccessModule.mockReturnValue(false);
    mockGetPrimaryAuthority.mockReturnValue("GLOBAL_DATA_ENTRY");
    mockIsAny.mockImplementation((authorities) => authorities.includes("GLOBAL_DATA_ENTRY"));

    render(<EmployeeDirectoryPage />);

    expect(await screen.findByTestId("employees-new")).toBeInTheDocument();
    expect(screen.getByTestId("employees-new-non-regular")).toBeInTheDocument();
  });

  test("uses identity directory source for verifier review", async () => {
    mockGetPrimaryAuthority.mockReturnValue("VERIFIER");
    mockIsAny.mockImplementation((authorities) => authorities.includes("VERIFIER"));

    render(<EmployeeDirectoryPage />);

    await screen.findByTestId("employees-row-EMP-200");
    expect(mockUseEmployeeDirectory).toHaveBeenCalledWith(expect.objectContaining({
      useIdentityDirectory: true,
      useUserDirectory: false,
    }));
  });

  test("uses identity directory source for approving authority so verified identities remain visible", async () => {
    mockGetPrimaryAuthority.mockReturnValue("APPROVING_AUTHORITY");
    mockIsAny.mockImplementation((authorities) => authorities.includes("APPROVING_AUTHORITY"));

    render(<EmployeeDirectoryPage />);

    await screen.findByTestId("employees-row-EMP-200");
    expect(mockUseEmployeeDirectory).toHaveBeenCalledWith(expect.objectContaining({
      useIdentityDirectory: true,
      useUserDirectory: false,
    }));
  });

  test("uses user-management directory source for system admin", async () => {
    mockGetPrimaryAuthority.mockReturnValue("SYSTEM_ADMIN");
    mockIsAny.mockImplementation((authorities) => authorities.includes("SYSTEM_ADMIN"));

    render(<EmployeeDirectoryPage />);

    await screen.findByTestId("employees-row-EMP-200");
    expect(mockUseEmployeeDirectory).toHaveBeenCalledWith(expect.objectContaining({
      useIdentityDirectory: false,
      useUserDirectory: true,
    }));
  });

  test("normalizes synthetic seeded employee names in the directory table", async () => {
    mockEmployees[0].full_name = "TEST_66cff484 User";

    render(<EmployeeDirectoryPage />);

    expect(await screen.findByText("Test User")).toBeInTheDocument();
    expect(screen.queryByText("TEST_66cff484 User")).not.toBeInTheDocument();
  });

  test("formats unmapped level-code designations and workflow help text", async () => {
    mockEmployees[0].current_designation_id = "L6";
    mockGetPrimaryAuthority.mockReturnValue("GLOBAL_DATA_ENTRY");
    mockIsAny.mockImplementation((authorities) => authorities.includes("GLOBAL_DATA_ENTRY"));

    render(<EmployeeDirectoryPage />);

    expect(await screen.findByText("Level 6")).toBeInTheDocument();
    expect(screen.getByText("Awaiting approval")).toBeInTheDocument();
    expect(screen.getByText("Login available after identity activation")).toBeInTheDocument();
  });

  test("does not render provisioning action for department data entry", async () => {
    render(<EmployeeDirectoryPage />);

    expect(screen.queryByTestId("employees-provision-EMP-200")).not.toBeInTheDocument();
  });

  test("renders provisioning action for global data entry and does not trigger row navigation", async () => {
    mockEmployees[0].identity_workflow_status = "ACTIVE";
    mockEmployees[0].workflow_status = "ACTIVE";
    mockEmployees[0].profile_workflow_status = "DRAFT";
    mockGetPrimaryAuthority.mockReturnValue("GLOBAL_DATA_ENTRY");
    mockIsAny.mockImplementation((authorities) => authorities.includes("GLOBAL_DATA_ENTRY"));

    render(<EmployeeDirectoryPage />);

    const button = await screen.findByTestId("employees-provision-EMP-200");
    fireEvent.click(button);

    await waitFor(() => {
      expect(mockProvisionEmployeeAccount).toHaveBeenCalledWith({
        employee_id: "EMP-200",
        email: "sample.employee@madc.gov.in",
      });
    });
    await waitFor(() => {
      expect(mockRefresh).toHaveBeenCalled();
    });
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  test("renders provisioning action for system admin", async () => {
    mockEmployees[0].identity_workflow_status = "ACTIVE";
    mockEmployees[0].workflow_status = "ACTIVE";
    mockEmployees[0].profile_workflow_status = "DRAFT";
    mockGetPrimaryAuthority.mockReturnValue("SYSTEM_ADMIN");
    mockIsAny.mockImplementation((authorities) => authorities.includes("SYSTEM_ADMIN"));

    render(<EmployeeDirectoryPage />);

    expect(await screen.findByTestId("employees-provision-EMP-200")).toBeInTheDocument();
  });

  test("shows existing login account state instead of provisioning action", async () => {
    mockEmployees[0].identity_workflow_status = "ACTIVE";
    mockEmployees[0].workflow_status = "ACTIVE";
    mockEmployees[0].profile_workflow_status = "DRAFT";
    mockEmployees[0].has_login_account = true;
    mockEmployees[0].account_email = "sample.employee@madc.gov.in";
    mockGetPrimaryAuthority.mockReturnValue("GLOBAL_DATA_ENTRY");
    mockIsAny.mockImplementation((authorities) => authorities.includes("GLOBAL_DATA_ENTRY"));

    render(<EmployeeDirectoryPage />);

    expect(screen.queryByTestId("employees-provision-EMP-200")).not.toBeInTheDocument();
    expect(await screen.findByText("Login ready")).toBeInTheDocument();
    expect(screen.getByText("sample.employee@madc.gov.in")).toBeInTheDocument();
  });
});
