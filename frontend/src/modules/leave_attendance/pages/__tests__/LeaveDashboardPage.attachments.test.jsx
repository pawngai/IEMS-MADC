import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import LeaveDashboardPage from "@/modules/leave_attendance/pages/LeaveDashboardPage";

const mockCan = jest.fn();
const mockCanAccessModule = jest.fn();
const mockList = jest.fn();
const mockListMy = jest.fn();
const mockGetBalances = jest.fn();
const mockApply = jest.fn();
const mockCancel = jest.fn();

jest.mock("react-router-dom", () => ({
  __esModule: true,
  useNavigate: () => jest.fn(),
  useLocation: () => ({ state: null }),
  useSearchParams: () => [new URLSearchParams(""), jest.fn()],
}));

jest.mock("@/app/layout/Layout", () => ({
  __esModule: true,
  default: ({ children }) => <div data-testid="layout">{children}</div>,
}));

jest.mock("@/modules/documents/api/documentsApi", () => ({
  __esModule: true,
  documentsAPI: {
    getFileUrl: (filename) => `/api/documents/files/${filename}`,
    openDocument: jest.fn(),
    downloadDocument: jest.fn(),
  },
}));

jest.mock("@/modules/identity_access/model/authContext", () => ({
  __esModule: true,
  useAuth: () => ({
    user: {
      sub: "u-ess-1",
      employee_id: "EMP-1",
      authorities: ["EMPLOYEE"],
    },
    can: mockCan,
    canAccessModule: mockCanAccessModule,
  }),
}));

jest.mock("@/modules/ess/api/essApi", () => ({
  __esModule: true,
  essAPI: {
    getMyProfile: jest.fn().mockResolvedValue({
      data: {
        employee_id: "EMP-1",
        full_name: "Test Employee",
      },
    }),
  },
}));

jest.mock("@/modules/leave_attendance/api/leaveApi", () => ({
  __esModule: true,
  leaveAPI: {
    list: (...args) => mockList(...args),
    listMy: (...args) => mockListMy(...args),
    getBalances: (...args) => mockGetBalances(...args),
    apply: (...args) => mockApply(...args),
    cancel: (...args) => mockCancel(...args),
  },
}));

jest.mock("@/platform/permissions", async (importOriginal) => ({
  ...(await importOriginal()),
  resolveScopeAccess: () => ({ scope: "EMPLOYEE", allowed: true }),
}));

jest.mock("@/modules/leave_attendance/components/LeaveActionDialog", () => ({
  __esModule: true,
  default: () => null,
}));

jest.mock("@/modules/leave_attendance/components/LeaveSupportingDocumentsField", () => ({
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

describe("LeaveDashboardPage attachments", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCanAccessModule.mockReturnValue(true);
    mockCan.mockImplementation((permission) => ["LEAVE_APPLY_OWN", "LEAVE_READ_OWN"].includes(permission));
    mockGetBalances.mockResolvedValue({
      data: {
        balances: {
          EL: {
            leave_code: "EL",
            description: "Earned Leave",
            available_days: 12,
          },
        },
      },
    });
    mockList.mockResolvedValue({ data: [] });
    mockListMy.mockResolvedValue({
      data: [
        {
          id: "L-ATT-1",
          employee_id: "EMP-1",
          leave_type_code: "EL",
          from_date: "2026-04-21",
          to_date: "2026-04-22",
          days_applied: 2,
          status: "SANCTIONED",
          attachments: [
            {
              filename: "medical-note.pdf",
              original_name: "medical-note.pdf",
            },
            {
              url: "/api/documents/files/birth-record.pdf",
              filename: "birth-record.pdf",
              original_name: "birth-record.pdf",
            },
          ],
        },
      ],
    });
  });

  test("shows attachment buttons that stream files through the authenticated client", async () => {
    render(<LeaveDashboardPage />);

    expect(await screen.findByText("My Leave Applications")).toBeInTheDocument();
    await waitFor(() => expect(mockListMy).toHaveBeenCalled());

    // Attachments are now buttons (not plain anchors) so the apiClient can
    // attach the Bearer access token and stream the file as a blob.
    const medicalBtn = screen.getByRole("button", { name: "medical-note.pdf" });
    const birthBtn = screen.getByRole("button", { name: "birth-record.pdf" });

    expect(medicalBtn).not.toHaveAttribute("href");
    expect(birthBtn).not.toHaveAttribute("href");
  });
});