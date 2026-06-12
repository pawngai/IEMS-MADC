import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import DeptSanctionedStrengthPage from "@/modules/organization_master/pages/DeptSanctionedStrengthPage";

const mockGetSanctionedStrength = vi.fn();
const mockUpdateSanctionedStrength = vi.fn();
const mockGetDesignations = vi.fn();
const mockGetPayLevels = vi.fn();
const mockGetServiceGroups = vi.fn();

vi.mock("@/app/layout/Layout", () => ({
  __esModule: true,
  default: ({ children }) => <div data-testid="layout">{children}</div>,
}));

vi.mock("@/modules/organization_master/hooks/useDepartmentScope", () => ({
  __esModule: true,
  useDepartmentScope: () => ({
    canUseDepartmentPortal: true,
    canManageSanctionedStrength: true,
    loading: false,
    selectedDepartment: "FIN",
    selectedDepartmentLabel: "Finance Department",
    scopeError: "",
  }),
}));

vi.mock("@/modules/organization_master/api/departmentApi", () => ({
  __esModule: true,
  departmentPortalAPI: {
    getSanctionedStrength: (...args) => mockGetSanctionedStrength(...args),
    updateSanctionedStrength: (...args) => mockUpdateSanctionedStrength(...args),
  },
}));

vi.mock("@/modules/organization_master/api/mastersApi", () => ({
  __esModule: true,
  mastersAPI: {
    getDesignations: (...args) => mockGetDesignations(...args),
    getPayLevels: (...args) => mockGetPayLevels(...args),
    getServiceGroups: (...args) => mockGetServiceGroups(...args),
  },
}));

vi.mock("sonner", () => ({
  __esModule: true,
  toast: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

describe("DeptSanctionedStrengthPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetSanctionedStrength.mockResolvedValue({
      data: {
        items: [
          {
            designation_code: "SO",
            employment_type: null,
            sanctioned_count: 5,
            filled_count: 3,
            vacancy_count: 2,
            over_strength_count: 0,
            order_number: "12/2026",
            order_date: "2026-04-04",
            remarks: "Revised",
          },
        ],
        totals: {
          sanctioned_strength_total: 5,
          filled_strength_total: 3,
          vacancy_count: 2,
          over_strength_count: 0,
        },
      },
    });
    mockGetDesignations.mockResolvedValue({
      data: [
        {
          code: "SO",
          name: "Section Officer",
          metadata: {
            service_group_code: "GROUP_B",
            pay_level_code: "LEVEL_7",
          },
        },
      ],
    });
    mockGetPayLevels.mockResolvedValue({
      data: [{ code: "LEVEL_7", name: "Level 7" }],
    });
    mockGetServiceGroups.mockResolvedValue({
      data: [{ code: "GROUP_B", name: "Group B" }],
    });
  });

  test("loads department-safe master references and renders derived row values", async () => {
    render(<DeptSanctionedStrengthPage />);

    await waitFor(() => {
      expect(mockGetSanctionedStrength).toHaveBeenCalledTimes(1);
      expect(mockGetDesignations).toHaveBeenCalledTimes(1);
      expect(mockGetPayLevels).toHaveBeenCalledTimes(1);
      expect(mockGetServiceGroups).toHaveBeenCalledTimes(1);
    });

    expect(screen.getByText("Sanctioned Strength")).toBeInTheDocument();
    expect(screen.getByText("SO - Section Officer")).toBeInTheDocument();
    expect(screen.getByText("GROUP_B")).toBeInTheDocument();
    expect(screen.getByText("LEVEL_7")).toBeInTheDocument();
    expect(screen.getByDisplayValue("5")).toBeInTheDocument();
  });
});