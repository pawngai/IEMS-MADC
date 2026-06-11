import React from "react";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import "@testing-library/jest-dom";

import LeaveDashboardPage from "@/contexts/leave/pages/LeaveDashboardPage";

const mockNavigate = jest.fn();
const mockSetSearchParams = jest.fn();
const mockCan = jest.fn();
const mockCanAccessModule = jest.fn();
const mockList = jest.fn();
const mockListMy = jest.fn();
const mockGetBalances = jest.fn();
const mockEmployeeIdentityList = jest.fn();
const mockEmployeeIdentityGet = jest.fn();
const mockLocation = { state: { returnTo: "/employees/EMP-200" } };
let currentSearchParams = "employee_id=EMP-200";

jest.mock("react-router-dom", () => ({
  __esModule: true,
  useNavigate: () => mockNavigate,
  useLocation: () => mockLocation,
  useSearchParams: () => [new URLSearchParams(currentSearchParams), mockSetSearchParams],
}));

jest.mock("@/app/layout/Layout", () => ({
  __esModule: true,
  default: ({ children }) => <div data-testid="layout">{children}</div>,
}));

jest.mock("@/contexts/identity_access/model/authContext", () => ({
  __esModule: true,
  useAuth: () => ({
    user: { sub: "u-1" },
    can: mockCan,
    canAccessModule: mockCanAccessModule,
  }),
}));

jest.mock("@/contexts/ess/api/essApi", () => ({
  __esModule: true,
  essAPI: {
    getMyProfile: jest.fn(),
  },
}));

jest.mock("@/contexts/leave/api/leaveApi", () => ({
  __esModule: true,
  leaveAPI: {
    list: (...args) => mockList(...args),
    listMy: (...args) => mockListMy(...args),
    getBalances: (...args) => mockGetBalances(...args),
    apply: jest.fn(),
    cancel: jest.fn(),
  },
}));

jest.mock("@/contexts/employee_identity/api/employeeIdentityApi", () => ({
  __esModule: true,
  employeeIdentityApi: {
    list: (...args) => mockEmployeeIdentityList(...args),
    get: (...args) => mockEmployeeIdentityGet(...args),
  },
}));

jest.mock("@/contexts/access_control/services/authorizationService", () => ({
  __esModule: true,
  EMPLOYEE: "EMPLOYEE",
  resolveScopeAccess: () => ({ scope: "GLOBAL", allowed: true }),
}));

jest.mock("@/contexts/leave/components/LeaveActionDialog", () => ({
  __esModule: true,
  default: () => null,
}));

jest.mock("@/shared/ui/searchable-select", () => ({
  __esModule: true,
  SearchableSelect: ({ value, onValueChange, options = [], dataTestId }) => (
    <select data-testid={dataTestId} value={value} onChange={(event) => onValueChange(event.target.value)}>
      <option value="">All leave types</option>
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  ),
}));

jest.mock("sonner", () => ({
  __esModule: true,
  toast: {
    error: jest.fn(),
    success: jest.fn(),
  },
}));

describe("LeaveDashboardPage employee filter", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    currentSearchParams = "employee_id=EMP-200";
    mockCanAccessModule.mockReturnValue(true);
    mockCan.mockImplementation((permission) => permission === "LEAVE_READ_ALL");
    mockList.mockResolvedValue({
      data: [
        {
          id: "L-1",
          employee_id: "EMP-200",
          leave_type_code: "CL",
          from_date: "2026-04-21",
          to_date: "2026-04-22",
          days_applied: 2,
          status: "SANCTIONED",
          applied_at: "2026-04-12T10:00:00+00:00",
        },
        {
          id: "L-2",
          employee_id: "EMP-200",
          leave_type_code: "EL",
          from_date: "2026-05-02",
          to_date: "2026-05-04",
          days_applied: 3,
          status: "RECOMMENDED",
          applied_at: "2026-04-15T10:00:00+00:00",
        },
      ],
    });
    mockListMy.mockResolvedValue({ data: [] });
    mockGetBalances.mockResolvedValue({
      data: {
        balances: {
          EL: { available_days: 12 },
          HPL: { available_days: 24 },
          CL: { available_days: 6 },
        },
      },
    });
    mockEmployeeIdentityList.mockResolvedValue({
      data: { identities: [], total: 0, page: 1, page_size: 8, total_pages: 0 },
    });
    mockEmployeeIdentityGet.mockResolvedValue({ data: null });
  });

  test("loads employee-specific leave history from query string", async () => {
    render(<LeaveDashboardPage />);

    await waitFor(() => expect(mockList).toHaveBeenCalledWith({ employee_id: "EMP-200" }));
    expect(
      await screen.findByRole("heading", { level: 2, name: "Leave History" }),
    ).toBeInTheDocument();
    const summaryCard = screen.getByTestId("employee-leave-summary-card");
    const summaryBalances = within(summaryCard).getByTestId("employee-leave-summary-balances");
    expect(screen.getByText("Applications and approval history for the selected employee")).toBeInTheDocument();
    expect(screen.getByText("EMP-200")).toBeInTheDocument();
    expect(screen.queryByText("Viewing leave applications for EMP-200")).not.toBeInTheDocument();
    expect(within(summaryBalances).getByText("Leave Balance")).toBeInTheDocument();
    expect(within(summaryBalances).getByText("Earned Leave")).toBeInTheDocument();
    expect(within(summaryBalances).getByText("Half Pay Leave")).toBeInTheDocument();
    expect(within(summaryBalances).getByText("Casual Leave")).toBeInTheDocument();
    expect(within(summaryBalances).getByText("12")).toBeInTheDocument();
    expect(within(summaryBalances).getByText("24")).toBeInTheDocument();
    expect(within(summaryBalances).getByText("6")).toBeInTheDocument();
    expect(screen.getByText("Employee Leave Summary")).toBeInTheDocument();
    expect(within(screen.getByTestId("employee-leave-summary-total-applications")).getByText("2")).toBeInTheDocument();
    expect(within(screen.getByTestId("employee-leave-summary-total-days")).getByText("5")).toBeInTheDocument();
    expect(within(screen.getByTestId("employee-leave-summary-pending")).getByText("1")).toBeInTheDocument();
    expect(within(screen.getByTestId("employee-leave-summary-sanctioned")).getByText("1")).toBeInTheDocument();
    expect(screen.getByText("Casual Leave: 1")).toBeInTheDocument();
    expect(screen.getByText("Earned Leave: 1")).toBeInTheDocument();
    expect(screen.getByText("CL")).toBeInTheDocument();
    expect(screen.getByText("EL")).toBeInTheDocument();
    expect(screen.queryByText("Apply for Leave")).not.toBeInTheDocument();
    expect(screen.queryByText("Pending Recommendations")).not.toBeInTheDocument();
    expect(screen.queryByText("Pending Sanctions")).not.toBeInTheDocument();

    fireEvent.change(screen.getByTestId("employee-history-type-filter"), {
      target: { value: "EL" },
    });

    await waitFor(() => {
      expect(screen.queryByText("CL")).not.toBeInTheDocument();
    });
    expect(screen.getByText("EL")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Back"));
    expect(mockNavigate).toHaveBeenCalledWith("/employees/EMP-200");
  });

  test("searches employees and opens employee leave history directly", async () => {
    currentSearchParams = "";
    mockCan.mockImplementation((permission) => permission === "LEAVE_RECOMMEND");
    mockEmployeeIdentityList.mockResolvedValue({
      data: {
        identities: [
          {
            employee_id: "EMP-555",
            employee_code: "MADC-2024-R0555",
            full_name: "Smoke Employee",
            current_department_id: "FIN",
          },
        ],
        total: 1,
        page: 1,
        page_size: 8,
        total_pages: 1,
      },
    });

    render(<LeaveDashboardPage />);

    expect(await screen.findByText("View Employee Leave History")).toBeInTheDocument();

    fireEvent.change(screen.getByTestId("employee-history-search-input"), {
      target: { value: "smoke" },
    });

    await waitFor(() => {
      expect(mockEmployeeIdentityList).toHaveBeenCalledWith({ search: "smoke", page: 1, page_size: 8 });
    });

    fireEvent.click(await screen.findByRole("button", { name: /Smoke Employee/i }));

    await waitFor(() => {
      expect(mockSetSearchParams).toHaveBeenCalled();
    });

    const nextSearchParams = mockSetSearchParams.mock.calls.at(-1)[0];
    expect(nextSearchParams.get("employee_id")).toBe("EMP-555");
  });
});
