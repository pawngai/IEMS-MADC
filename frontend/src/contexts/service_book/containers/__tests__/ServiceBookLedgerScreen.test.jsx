import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import ServiceBookLedgerScreen from "@/contexts/service_book/containers/ServiceBookLedgerScreen";

const mockUseAuth = jest.fn();
const mockUseServiceBookProjection = jest.fn();
const mockLedgerShell = jest.fn(() => <div data-testid="service-book-ledger-shell" />);

jest.mock("@/contexts/identity_access", () => ({
  __esModule: true,
  useAuth: () => mockUseAuth(),
  usePermissions: () => {
    const auth = mockUseAuth();
    return { can: auth.can, Permissions: auth.Permissions };
  },
}));

jest.mock("@/contexts/organization_master", () => ({
  __esModule: true,
  mastersAPI: {
    getServiceEventTypes: jest.fn(() => Promise.resolve({ data: [] })),
    getLeaveTypes: jest.fn(() => Promise.resolve({ data: [] })),
    getCasteCategories: jest.fn(() => Promise.resolve({ data: [] })),
    getPayLevels: jest.fn(() => Promise.resolve({ data: [] })),
  },
}));

jest.mock("@/contexts/service_book/hooks/useServiceBookProjection", () => ({
  __esModule: true,
  useServiceBookProjection: (...args) => mockUseServiceBookProjection(...args),
}));

jest.mock("@/contexts/service_book/components/ServiceBookLedgerShell", () => ({
  __esModule: true,
  default: (props) => mockLedgerShell(props),
}));

describe("ServiceBookLedgerScreen", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    const Permissions = {
      SERVICE_BOOK_READ_ALL: "SERVICE_BOOK_READ_ALL",
      AUDIT_READ_ALL: "AUDIT_READ_ALL",
      SERVICE_BOOK_READ_OWN: "SERVICE_BOOK_READ_OWN",
      SERVICE_BOOK_ENTRY_CREATE: "SERVICE_BOOK_ENTRY_CREATE",
      SERVICE_BOOK_SUPERSEDE: "SERVICE_BOOK_SUPERSEDE",
      SERVICE_BOOK_ENTRY_APPROVE: "SERVICE_BOOK_ENTRY_APPROVE",
      SERVICE_BOOK_ENTRY_VERIFY: "SERVICE_BOOK_ENTRY_VERIFY",
    };

    mockUseAuth.mockReturnValue({
      user: { employee_id: "EMP-1" },
      loading: false,
      Permissions,
      can: (permission) => permission === Permissions.SERVICE_BOOK_READ_ALL,
    });

    mockUseServiceBookProjection.mockReturnValue({
      serviceBook: {
        employee_code: "OLD-CODE",
        completion_percentage: 22,
        part_i: {
          name_in_block_letters: "CONTEXT TEST EMPLOYEE",
          employee_code: "OLD-CODE",
          parent_name: "Context Test Father",
        },
      },
      partsInfo: {},
      isLoading: false,
      notApplicable: null,
      reloadServiceBook: jest.fn(),
    });
  });

  test("overlays canonical Part I identity fields before rendering the ledger", async () => {
    render(
      <ServiceBookLedgerScreen
        employeeId="EMP-1"
        employeeName="K. VANLALIANA"
        partIDefaults={{
          employee_code: "MADC-1992-R0001",
          name_in_block_letters: "K. VANLALIANA",
        }}
      />,
    );

    await waitFor(() => {
      expect(screen.getByTestId("service-book-ledger-shell")).toBeInTheDocument();
    });

    expect(mockLedgerShell).toHaveBeenCalled();
    expect(mockLedgerShell.mock.calls.at(-1)?.[0]).toEqual(
      expect.objectContaining({
        serviceBook: expect.objectContaining({
          employee_code: "MADC-1992-R0001",
          part_i: expect.objectContaining({
            employee_code: "MADC-1992-R0001",
            name_in_block_letters: "K. VANLALIANA",
            parent_name: "Context Test Father",
          }),
        }),
      }),
    );
  });
});