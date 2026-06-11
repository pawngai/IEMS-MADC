import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import EmployeeIdentityEditorPage from "@/contexts/employee_master/pages/EmployeeIdentityEditorPage";

const mockNavigate = vi.fn();
const mockCreate = vi.fn();
const mockUpdate = vi.fn();
const mockGet = vi.fn();
const mockProfileUpdate = vi.fn();
const mockGetEmploymentTypes = vi.fn();
const mockToastError = vi.fn();
let mockLocationState = null;

jest.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({ pathname: "/employees/new/identity", state: mockLocationState }),
    useParams: () => ({}),
  };
});

jest.mock("@/app/layout/Layout", () => ({
  __esModule: true,
  default: ({ children }) => <div data-testid="layout-shell">{children}</div>,
}));

jest.mock("@/contexts/employee_master/api/employeeIdentityApi", () => ({
  __esModule: true,
  employeeIdentityApi: {
    create: (...args) => mockCreate(...args),
    update: (...args) => mockUpdate(...args),
    get: (...args) => mockGet(...args),
  },
}));

jest.mock("@/contexts/employee_master/api/employeeProfileApi", () => ({
  __esModule: true,
  employeeProfileApi: {
    update: (...args) => mockProfileUpdate(...args),
  },
}));

jest.mock("@/contexts/organization_master/api/mastersApi", () => ({
  __esModule: true,
  mastersAPI: {
    getEmploymentTypes: (...args) => mockGetEmploymentTypes(...args),
  },
}));

jest.mock("sonner", () => ({
  __esModule: true,
  toast: {
    error: (...args) => mockToastError(...args),
  },
}));

jest.mock("@/shared/ui/select", () => ({
  __esModule: true,
  Select: ({ value, onValueChange, children, disabled }) => (
    <select
      data-testid="mock-select"
      value={value || ""}
      onChange={(event) => onValueChange(event.target.value)}
      disabled={disabled}
    >
      {children}
    </select>
  ),
  SelectTrigger: ({ children }) => <>{children}</>,
  SelectValue: ({ placeholder }) => <option value="">{placeholder}</option>,
  SelectContent: ({ children }) => <>{children}</>,
  SelectItem: ({ value, children }) => <option value={value}>{children}</option>,
}));

describe("EmployeeIdentityEditorPage", () => {
  beforeEach(() => {
    global.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
    vi.clearAllMocks();
    mockLocationState = null;
    mockGet.mockResolvedValue({ data: {} });
    mockUpdate.mockResolvedValue({ data: {} });
    mockProfileUpdate.mockResolvedValue({ data: {} });
    mockGetEmploymentTypes.mockResolvedValue({
      data: [
        { employment_type_code: "REGULAR", name: "Regular", employment_class: "REGULAR", eligible_for_service_book: true },
        { employment_type_code: "CONTRACT", name: "Contract", employment_class: "NON_REGULAR", eligible_for_service_book: false },
        { employment_type_code: "FIXED_PAY", name: "Fixed Pay", employment_class: "NON_REGULAR", eligible_for_service_book: false },
      ],
    });
    mockCreate.mockResolvedValue({
      data: {
        employee_id: "EMP-101",
        employee_code: "MADC-2020-0001",
      },
    });
  });

  test("renders required core identity fields and submits the create contract", async () => {
    render(<EmployeeIdentityEditorPage />);

    await screen.findByText("Create Employee Identity");

    expect(screen.queryByLabelText("Father Name")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Category")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Place of Birth")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Aadhaar Number")).not.toBeInTheDocument();
    expect(screen.queryByText("Employment Type")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Date of Appointment")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Department")).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Full Name"), {
      target: { value: "Asha Employee" },
    });
    fireEvent.change(screen.getByLabelText("Date of Birth"), {
      target: { value: "1991-01-10" },
    });
    fireEvent.change(screen.getByLabelText("Mobile Number"), {
      target: { value: "9862000001" },
    });
    fireEvent.change(screen.getByLabelText("Official Email"), {
      target: { value: "Asha.Employee@MADC.GOV.IN" },
    });

    const selects = screen.getAllByTestId("mock-select");
    fireEvent.change(selects[0], { target: { value: "Female" } });

    fireEvent.click(screen.getByRole("button", { name: "Create Identity" }));

    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalledWith({
        full_name: "Asha Employee",
        gender: "Female",
        date_of_birth: "1991-01-10",
        mobile_primary: "9862000001",
        email_official: "asha.employee@madc.gov.in",
      });
    });

    expect(mockNavigate).toHaveBeenCalledWith(
      expect.stringContaining("/employees?notice=")
    );
    expect(mockNavigate).not.toHaveBeenCalledWith(
      expect.stringContaining("/employees/EMP-101/profile/edit?notice=")
    );
    expect(mockProfileUpdate).not.toHaveBeenCalled();
  });

  test("non-regular create requires picking an employment type before submit", async () => {
    mockLocationState = {
      creationMode: "non_regular",
      returnTo: "/employees",
    };

    render(<EmployeeIdentityEditorPage />);

    await screen.findByText("Create Employee Identity");

    fireEvent.change(screen.getByLabelText("Full Name"), {
      target: { value: "Asha Employee" },
    });
    fireEvent.change(screen.getByLabelText("Date of Birth"), {
      target: { value: "1991-01-10" },
    });
    fireEvent.change(screen.getAllByTestId("mock-select")[0], {
      target: { value: "Female" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Create Identity" }));

    await waitFor(() => {
      expect(
        screen.getByText("Employment type is required for non-regular employees")
      ).toBeInTheDocument();
    });
    expect(mockCreate).not.toHaveBeenCalled();
  });

  test("seeds profile extension with chosen non-regular employment type after identity create", async () => {
    mockLocationState = {
      creationMode: "non_regular",
      returnTo: "/employees",
    };

    render(<EmployeeIdentityEditorPage />);

    await screen.findByText("Create Employee Identity");
    await waitFor(() => {
      expect(screen.getByText("Non-Regular Employment Type")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText("Full Name"), {
      target: { value: "Asha Employee" },
    });
    fireEvent.change(screen.getByLabelText("Date of Birth"), {
      target: { value: "1991-01-10" },
    });
    const selects = screen.getAllByTestId("mock-select");
    fireEvent.change(selects[0], { target: { value: "Female" } });
    fireEvent.change(selects[1], { target: { value: "CONTRACT" } });

    fireEvent.click(screen.getByRole("button", { name: "Create Identity" }));

    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalled();
    });
    expect(mockProfileUpdate).toHaveBeenCalledWith("EMP-101", {
      employment_type: "CONTRACT",
    });
    expect(mockNavigate).toHaveBeenCalledWith(
      expect.stringContaining("/employees?notice=")
    );
  });
});
