import React from "react";
import { render, screen, waitFor, within } from "@testing-library/react";
import "@testing-library/jest-dom";

import ServiceBookReadScreen from "@/contexts/service_book/containers/ServiceBookReadScreen";

jest.mock("@/app/layout/Layout", () => ({
  __esModule: true,
  default: ({ children }) => <div data-testid="layout">{children}</div>,
}));

const mockLedgerScreen = jest.fn(() => <div data-testid="service-book-ledger-screen" />);
const mockPrintScreen = jest.fn(() => <div data-testid="service-book-print-screen" />);

jest.mock("@/contexts/service_book/containers/ServiceBookLedgerScreen", () => ({
  __esModule: true,
  default: (props) => mockLedgerScreen(props),
}));

jest.mock("@/contexts/service_book/containers/ServiceBookPrintScreen", () => ({
  __esModule: true,
  default: (props) => mockPrintScreen(props),
}));

const mockUseAuth = jest.fn();

jest.mock("@/contexts/identity/model/authContext", () => ({
  __esModule: true,
  useAuth: () => mockUseAuth(),
}));

const mockGetMyProfile = jest.fn();
const mockGetPartIDefaults = jest.fn();
const mockUseParams = jest.fn(() => ({}));
const mockToastError = jest.fn();

jest.mock("@/contexts/ess/api/essApi", () => ({
  __esModule: true,
  essAPI: {
    getMyProfile: (...args) => mockGetMyProfile(...args),
  },
}));

jest.mock("@/contexts/service_book/api/serviceBookApi", () => ({
  __esModule: true,
  serviceBookAPI: {
    getPartIDefaults: (...args) => mockGetPartIDefaults(...args),
  },
}));

const mockGenerateServiceBookPrintModel = jest.fn();

jest.mock("@/contexts/service_book/services/serviceBookDomainService", () => ({
  __esModule: true,
  generateServiceBookPrintModel: (...args) => mockGenerateServiceBookPrintModel(...args),
}));

jest.mock("react-router-dom", () => ({
  useParams: () => mockUseParams(),
  Link: ({ children, to, ...rest }) => <a href={to} {...rest}>{children}</a>,
}));

jest.mock("sonner", () => ({
  toast: {
    error: (...args) => mockToastError(...args),
  },
}));

describe("ServiceBookReadScreen", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue({
      user: {
        employee_id: "EMP-1",
        name: "Regular Employee",
      },
    });
    mockUseParams.mockReturnValue({});
    mockGetMyProfile.mockRejectedValue(new Error("profile unavailable"));
    mockGetPartIDefaults.mockResolvedValue({
      employee_id: "EMP-1",
      employee_code: "EMP-1",
      name_in_block_letters: "Regular Employee",
    });
    mockGenerateServiceBookPrintModel.mockResolvedValue({
      service_book: {
        _raw_entries: [],
        parts_completed: [],
      },
    });
  });

  test("uses authenticated employee id in ESS mode when profile lookup fails", async () => {
    render(<ServiceBookReadScreen essMode />);

    await waitFor(() => {
      expect(screen.getByTestId("service-book-ledger-screen")).toBeInTheDocument();
      expect(mockLedgerScreen).toHaveBeenCalledWith(
        expect.objectContaining({
          employeeId: "EMP-1",
          employeeName: "EMP-1",
          forceReadOnly: true,
          entryStatuses: ["APPROVED", "LOCKED"],
        })
      );
    });

    expect(mockGenerateServiceBookPrintModel).toHaveBeenCalledWith(
      expect.objectContaining({
        employeeId: "EMP-1",
        statuses: ["APPROVED", "LOCKED"],
      })
    );
  });

  test("blocks the shell when the employee route cannot be resolved", async () => {
    mockUseParams.mockReturnValue({ employeeId: "MISSING-EMPLOYEE" });
    mockGetPartIDefaults.mockRejectedValue({
      response: {
        status: 404,
        data: {
          detail: "Employee not found",
        },
      },
    });

    render(<ServiceBookReadScreen />);

    await waitFor(() => {
      expect(screen.getByTestId("service-book-error")).toBeInTheDocument();
    });

    expect(within(screen.getByTestId("service-book-error")).getByRole("heading", { name: "Employee not found" })).toBeInTheDocument();
    expect(mockLedgerScreen).not.toHaveBeenCalled();
    expect(mockPrintScreen).not.toHaveBeenCalled();
    expect(mockGenerateServiceBookPrintModel).not.toHaveBeenCalled();
    expect(mockToastError).not.toHaveBeenCalled();
  });
});