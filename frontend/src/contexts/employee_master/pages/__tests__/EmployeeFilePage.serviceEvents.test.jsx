import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import EmployeeFilePage from "@/contexts/employee_master/pages/EmployeeFilePage";

const mockNavigate = jest.fn();
const mockCan = jest.fn();
const mockCanAny = jest.fn();
const mockCanAccessModule = jest.fn();
const mockGetPrimaryAuthority = jest.fn();
const mockGetProfile = jest.fn();
const mockGetDepartments = jest.fn();
const mockGetDesignations = jest.fn();
const mockGetOffices = jest.fn();
const mockGetPayLevels = jest.fn();
const mockGetServices = jest.fn();
const mockGetServiceGroups = jest.fn();
const mockGetServiceSummary = jest.fn();
const mockListServiceRecords = jest.fn();
const mockListServiceBookEntries = jest.fn();
const mockSubmitProfile = jest.fn();
const mockToastSuccess = jest.fn();

let mockPathname = "/employees/EMP-100";
let mockSearch = "";

jest.mock("react-router-dom", () => ({
  __esModule: true,
  useNavigate: () => mockNavigate,
  useLocation: () => ({ pathname: mockPathname, search: mockSearch, state: null }),
  useParams: () => ({ employeeId: "EMP-100" }),
}));

jest.mock("@/app/layout/Layout", () => ({
  __esModule: true,
  default: ({ children }) => <div data-testid="layout">{children}</div>,
}));

jest.mock("@/contexts/employee_master/components/EmployeeProfileSummary", () => ({
  __esModule: true,
  default: () => <div data-testid="employee-profile-summary">summary</div>,
}));

jest.mock("@/contexts/organization_master/api/mastersApi", () => ({
  __esModule: true,
  mastersAPI: {
    getDepartments: (...args) => mockGetDepartments(...args),
    getDesignations: (...args) => mockGetDesignations(...args),
    getOffices: (...args) => mockGetOffices(...args),
    getPayLevels: (...args) => mockGetPayLevels(...args),
    getServices: (...args) => mockGetServices(...args),
    getServiceGroups: (...args) => mockGetServiceGroups(...args),
  },
}));

jest.mock("@/contexts/employee_master/api/employeeProfileApi", () => ({
  __esModule: true,
  employeeProfileApi: {
    get: (...args) => mockGetProfile(...args),
    submit: (...args) => mockSubmitProfile(...args),
  },
}));

jest.mock("@/contexts/service_book/records/api/serviceRecordsApi", () => ({
  __esModule: true,
  serviceRecordsApi: {
    getServiceSummary: (...args) => mockGetServiceSummary(...args),
    listByEmployee: (...args) => mockListServiceRecords(...args),
  },
}));

jest.mock("@/contexts/service_book/api/serviceBookApi", () => ({
  __esModule: true,
  serviceBookAPI: {
    listEntries: (...args) => mockListServiceBookEntries(...args),
  },
}));

jest.mock("@/contexts/identity_access/model/authContext", () => ({
  __esModule: true,
  useAuth: () => ({
    can: mockCan,
    canAny: mockCanAny,
    canAccessModule: mockCanAccessModule,
    getPrimaryAuthority: mockGetPrimaryAuthority,
  }),
}));

jest.mock("sonner", () => ({
  __esModule: true,
  toast: {
    error: jest.fn(),
    success: (...args) => mockToastSuccess(...args),
  },
}));

describe("EmployeeFilePage Service Book records action", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPathname = "/employees/EMP-100";
    mockSearch = "";

    mockCan.mockImplementation((permission) => permission === "SERVICE_BOOK_READ_ALL");
    mockCanAny.mockReturnValue(false);
    mockCanAccessModule.mockImplementation((moduleId) => moduleId === "service_book");
    mockGetPrimaryAuthority.mockReturnValue("GLOBAL_DATA_ENTRY");
    mockGetDepartments.mockResolvedValue({ data: [] });
    mockGetDesignations.mockResolvedValue({ data: [] });
    mockGetOffices.mockResolvedValue({ data: [] });
    mockGetPayLevels.mockResolvedValue({ data: [] });
    mockGetServices.mockResolvedValue({ data: [] });
    mockGetServiceGroups.mockResolvedValue({ data: [] });
    mockGetServiceSummary.mockResolvedValue({ data: null });
    mockListServiceRecords.mockResolvedValue({ data: { employee_id: "EMP-100", events: [] } });
    mockListServiceBookEntries.mockResolvedValue({ entries: [] });
    mockSubmitProfile.mockResolvedValue({ data: { success: true } });

    mockGetProfile.mockResolvedValue({
      data: {
        employee_id: "EMP-100",
        employee_code: "E-100",
        full_name: "Demo Employee",
        employment_type: "REGULAR",
        workflow_status: "DRAFT",
      },
    });
  });

  test("navigates to non-portal Service Book records route", async () => {
    render(<EmployeeFilePage />);

    const btn = await screen.findByTestId("employee-profile-service-book-records");
    fireEvent.click(btn);

    expect(mockNavigate).toHaveBeenCalledWith("/service-book/records/E-100");
  });

  test("navigates to non-portal Service Book Opening route when not opened", async () => {
    render(<EmployeeFilePage />);

    const btn = await screen.findByTestId("employee-profile-servicebook");
    fireEvent.click(btn);

    expect(mockNavigate).toHaveBeenCalledWith("/service-book/opening/E-100");
  });

  test("navigates to non-portal Service Book projection route from view button", async () => {
    render(<EmployeeFilePage />);

    const btn = await screen.findByTestId("employee-profile-view-servicebook");
    fireEvent.click(btn);

    expect(mockNavigate).toHaveBeenCalledWith("/service-book/E-100");
  });

  test("navigates to leave history for the selected employee", async () => {
    mockCan.mockImplementation(
      (permission) => permission === "SERVICE_BOOK_READ_ALL" || permission === "LEAVE_READ_ALL"
    );
    mockCanAccessModule.mockImplementation(
      (moduleId) => moduleId === "service_book" || moduleId === "leave"
    );

    render(<EmployeeFilePage />);

    const btn = await screen.findByTestId("employee-profile-leave-history");
    fireEvent.click(btn);

    expect(mockNavigate).toHaveBeenCalledWith("/leave?employee_id=EMP-100", {
      state: { returnTo: "/employees/EMP-100" },
    });
  });

  test("navigates to portal Service Book records route", async () => {
    mockPathname = "/portal/employees/EMP-100";

    render(<EmployeeFilePage />);

    const btn = await screen.findByTestId("employee-profile-service-book-records");
    fireEvent.click(btn);

    expect(mockNavigate).toHaveBeenCalledWith("/portal/service-book/records/E-100");
  });

  test("navigates to portal Service Book Opening route when not opened", async () => {
    mockPathname = "/portal/employees/EMP-100";

    render(<EmployeeFilePage />);

    const btn = await screen.findByTestId("employee-profile-servicebook");
    fireEvent.click(btn);

    expect(mockNavigate).toHaveBeenCalledWith("/portal/service-book/opening/E-100");
  });

  test("navigates to portal Service Book projection route from view button", async () => {
    mockPathname = "/portal/employees/EMP-100";

    render(<EmployeeFilePage />);

    const btn = await screen.findByTestId("employee-profile-view-servicebook");
    fireEvent.click(btn);

    expect(mockNavigate).toHaveBeenCalledWith("/portal/service-book/E-100");
  });

  test("hides button when service_book module is not accessible", async () => {
    mockCanAccessModule.mockReturnValue(false);

    render(<EmployeeFilePage />);

    await waitFor(() => expect(mockGetProfile).toHaveBeenCalled());
    expect(screen.queryByTestId("employee-profile-service-book-records")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-profile-servicebook")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-profile-view-servicebook")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-profile-leave-history")).not.toBeInTheDocument();
  });

  test("hides servicebook and Service Book records buttons for non-regular employees", async () => {
    mockGetProfile.mockResolvedValue({
      data: {
        employee_id: "EMP-100",
        employee_code: "E-100",
        full_name: "Demo Employee",
        employment_type: "CONTRACTUAL",
        workflow_status: "DRAFT",
      },
    });

    render(<EmployeeFilePage />);

    await waitFor(() => expect(mockGetProfile).toHaveBeenCalled());
    expect(screen.queryByTestId("employee-profile-servicebook")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-profile-view-servicebook")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-profile-service-book-records")).not.toBeInTheDocument();
  });

  test("routes edit actions to separate identity and profile pages", async () => {
    mockCanAny.mockReturnValue(true);

    render(<EmployeeFilePage />);

    fireEvent.click(await screen.findByTestId("employee-profile-edit-identity"));
    expect(mockNavigate).toHaveBeenCalledWith("/employees/EMP-100/identity/edit", {
      state: { returnTo: "/employees/EMP-100" },
    });

    fireEvent.click(screen.getByTestId("employee-profile-edit-profile"));
    expect(mockNavigate).toHaveBeenCalledWith("/employees/EMP-100/profile/edit", {
      state: { returnTo: "/employees/EMP-100", nonRegular: false },
    });
  });

  test("threads nonRegular intent to the profile editor for non-regular employees", async () => {
    mockCanAny.mockReturnValue(true);
    mockGetProfile.mockResolvedValue({
      data: {
        employee_id: "EMP-100",
        employee_code: "E-100",
        full_name: "Demo Employee",
        employment_type: "CONTRACT",
        identity_workflow_status: "ACTIVE",
        workflow_status: "DRAFT",
      },
    });

    render(<EmployeeFilePage />);

    fireEvent.click(await screen.findByTestId("employee-profile-edit-profile"));
    expect(mockNavigate).toHaveBeenCalledWith("/employees/EMP-100/profile/edit", {
      state: { returnTo: "/employees/EMP-100", nonRegular: true },
    });
  });

  test("submits draft profile from the employee file when both sections are complete", async () => {
    mockCanAny.mockReturnValue(true);
    mockGetProfile.mockResolvedValue({
      data: {
        employee_id: "EMP-100",
        employee_code: "E-100",
        full_name: "Demo Employee",
        employment_type: "CONTRACTUAL",
        identity_workflow_status: "ACTIVE",
        workflow_status: "DRAFT",
        employee_section_completed: true,
        data_entry_section_completed: true,
      },
    });

    render(<EmployeeFilePage />);

    fireEvent.click(await screen.findByTestId("employee-profile-submit-profile"));

    await waitFor(() => {
      expect(mockSubmitProfile).toHaveBeenCalledWith("EMP-100");
    });
    expect(mockToastSuccess).toHaveBeenCalledWith("Profile submitted for verification");
  });

  test("shows regularisation action for non-regular employees with service-book entry permission", async () => {
    mockCan.mockImplementation(
      (permission) => permission === "SERVICE_BOOK_READ_ALL" || permission === "SERVICE_BOOK_ENTRY_CREATE"
    );
    mockGetProfile.mockResolvedValue({
      data: {
        employee_id: "EMP-100",
        employee_code: "E-100",
        full_name: "Demo Employee",
        employment_type: "CONTRACTUAL",
        identity_workflow_status: "ACTIVE",
        workflow_status: "DRAFT",
      },
    });

    render(<EmployeeFilePage />);

    fireEvent.click(await screen.findByTestId("employee-profile-regularisation"));
    expect(mockNavigate).toHaveBeenCalledWith("/employees/EMP-100/regularisation");
  });

  test("hides regularisation action for regular employees", async () => {
    mockCan.mockImplementation(
      (permission) => permission === "SERVICE_BOOK_READ_ALL" || permission === "SERVICE_BOOK_ENTRY_CREATE"
    );
    mockGetProfile.mockResolvedValue({
      data: {
        employee_id: "EMP-100",
        employee_code: "E-100",
        full_name: "Demo Employee",
        employment_type: "REGULAR",
        identity_workflow_status: "ACTIVE",
        workflow_status: "DRAFT",
      },
    });

    render(<EmployeeFilePage />);

    await screen.findByTestId("employee-profile-summary");
    expect(screen.queryByTestId("employee-profile-regularisation")).not.toBeInTheDocument();
  });

  test("hides edit-oriented actions for approving authority", async () => {
    mockGetPrimaryAuthority.mockReturnValue("APPROVING_AUTHORITY");
    mockCanAny.mockReturnValue(true);

    render(<EmployeeFilePage />);

    await screen.findByTestId("employee-profile-summary");
    expect(screen.queryByTestId("employee-profile-service-book-records")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-profile-upload-photo")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-profile-upload-signature")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-profile-edit-identity")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-profile-edit-profile")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-profile-servicebook")).not.toBeInTheDocument();
  });

  test("hides edit-oriented actions for verifier", async () => {
    mockGetPrimaryAuthority.mockReturnValue("VERIFIER");
    mockCanAny.mockReturnValue(true);

    render(<EmployeeFilePage />);

    await screen.findByTestId("employee-profile-summary");
    expect(screen.queryByTestId("employee-profile-service-book-records")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-profile-upload-photo")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-profile-upload-signature")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-profile-edit-identity")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-profile-edit-profile")).not.toBeInTheDocument();
    expect(screen.queryByTestId("employee-profile-servicebook")).not.toBeInTheDocument();
  });

  test("renders readable workflow and employment labels in the detail header", async () => {
    mockGetProfile.mockResolvedValue({
      data: {
        employee_id: "EMP-100",
        employee_code: "E-100",
        full_name: "Demo Employee",
        employment_type: "REGULAR",
        workflow_status: "APPROVED",
      },
    });

    render(<EmployeeFilePage />);

    expect(await screen.findByText("Approved")).toBeInTheDocument();
    expect(screen.getByText("Regular")).toBeInTheDocument();
    expect(screen.queryByText("APPROVED")).not.toBeInTheDocument();
    expect(screen.queryByText("REGULAR")).not.toBeInTheDocument();
  });
});
